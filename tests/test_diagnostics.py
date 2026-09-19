import json
import zipfile
from pathlib import Path

from mtkrita.diagnostics import DiagnosticBundleBuilder
from mtkrita.job_store import JobStore
from mtkrita.log_sink import JsonlLogSink, LogSeverity
from mtkrita.path_manager import PathManager


def _prepared_job(tmp_path: Path):
    paths = PathManager(tmp_path / "workspace")
    paths.prepare_job("job-1")
    jobs = JobStore(paths.evidence("job-1", "jobs.sqlite3").path)
    jobs.initialize()
    jobs.create_job("job-1", source_hash="src-hash", config_hash="cfg-hash")
    jobs.create_task("task-1", job_id="job-1")
    return paths, jobs


def test_diagnostic_bundle_contains_safe_operational_evidence(tmp_path: Path) -> None:
    paths, jobs = _prepared_job(tmp_path)
    sink = JsonlLogSink(paths, fsync=False)
    sink.write(
        sink.create_record(
            severity=LogSeverity.ERROR,
            component="worker_manager",
            code="WORKER.LOST",
            message="worker heartbeat expired",
            job_id="job-1",
            correlation_id="corr-1",
        )
    )

    result = DiagnosticBundleBuilder(paths, jobs).build(
        "job-1",
        effective_config={
            "provider": "opencv",
            "api_token": "should-not-leak",
            "nested": {"password": "also-secret", "workers": 4},
        },
    )

    assert result.target.path.is_file()
    with zipfile.ZipFile(result.target.path) as archive:
        names = set(archive.namelist())
        assert names == {
            "effective_config_redacted.json",
            "environment.json",
            "events.json",
            "events.jsonl",
            "job.json",
            "tasks.json",
        }
        config = json.loads(archive.read("effective_config_redacted.json"))
        assert config["provider"] == "opencv"
        assert config["api_token"] == "<redacted>"
        assert config["nested"]["password"] == "<redacted>"
        assert config["nested"]["workers"] == 4
        assert b"should-not-leak" not in archive.read("effective_config_redacted.json")
        assert json.loads(archive.read("job.json"))["source_hash"] == "src-hash"
        assert json.loads(archive.read("tasks.json"))[0]["task_id"] == "task-1"
        assert b"WORKER.LOST" in archive.read("events.jsonl")


def test_diagnostic_bundle_refuses_overwrite_and_never_includes_workspace_source_files(
    tmp_path: Path,
) -> None:
    paths, jobs = _prepared_job(tmp_path)
    private_source = paths.job_root("job-1").path / "private-source.png"
    private_source.write_bytes(b"private-image")
    builder = DiagnosticBundleBuilder(paths, jobs)

    first = builder.build("job-1")

    with zipfile.ZipFile(first.target.path) as archive:
        assert "private-source.png" not in archive.namelist()
        combined = b"".join(archive.read(name) for name in archive.namelist())
        assert b"private-image" not in combined

    try:
        builder.build("job-1")
    except FileExistsError:
        pass
    else:
        raise AssertionError("expected diagnostic bundle overwrite refusal")
