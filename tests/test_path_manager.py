from pathlib import Path

from mtkrita.path_manager import PathKind, PathManager


def test_path_manager_builds_isolated_job_and_worker_paths(tmp_path: Path) -> None:
    manager = PathManager(tmp_path / "พื้นที่งาน")
    job = manager.prepare_job("job-001")
    worker = manager.prepare_worker_scratch("job-001", "worker-02")

    assert job.kind == PathKind.JOB_ROOT
    assert job.path.is_dir()
    assert (job.path / "inputs").is_dir()
    assert worker.kind == PathKind.WORKER_SCRATCH
    assert worker.path.is_dir()
    assert worker.path.parent == job.path / "scratch"


def test_input_path_is_typed_non_worker_owned_and_inside_job(tmp_path: Path) -> None:
    manager = PathManager(tmp_path)
    job = manager.prepare_job("job-123")

    source = manager.input("job-123", "frame-001.png")

    assert source.kind == PathKind.INPUT
    assert source.worker_id is None
    assert source.job_id == "job-123"
    assert source.path == job.path / "inputs" / "frame-001.png"
    assert manager.assert_owned(source.path) == source.path.resolve()


def test_worker_file_preserves_typed_worker_ownership(tmp_path: Path) -> None:
    manager = PathManager(tmp_path)
    manager.prepare_job("job-123")
    manager.prepare_worker_scratch("job-123", "worker-02")

    candidate = manager.worker_file("job-123", "worker-02", "candidate.png")

    assert candidate.kind == PathKind.WORKER_SCRATCH
    assert candidate.worker_id == "worker-02"
    assert candidate.job_id == "job-123"
    assert candidate.path == (
        tmp_path.resolve() / "jobs" / "job-123" / "scratch" / "worker-02" / "candidate.png"
    )


def test_output_evidence_and_log_resolve_inside_job(tmp_path: Path) -> None:
    manager = PathManager(tmp_path)
    manager.prepare_job("job-123")

    output = manager.output("job-123", "01.png")
    evidence = manager.evidence("job-123", "manifest.json")
    log = manager.log("job-123")

    assert output.path == tmp_path.resolve() / "jobs" / "job-123" / "outputs" / "01.png"
    assert evidence.path.parent.name == "evidence"
    assert log.path.name == "events.jsonl"
    assert manager.assert_owned(output.path) == output.path.resolve()


def test_path_manager_rejects_traversal_and_external_paths(tmp_path: Path) -> None:
    manager = PathManager(tmp_path / "workspace")

    for bad_job in ("../escape", "..", "job/name"):
        try:
            manager.job_root(bad_job)
        except ValueError:
            pass
        else:
            raise AssertionError("expected unsafe job id rejection")

    for resolver in (manager.input, manager.output):
        try:
            resolver("job-1", "../outside.png")
        except ValueError:
            pass
        else:
            raise AssertionError("expected unsafe filename rejection")

    try:
        manager.assert_owned(tmp_path / "outside.txt")
    except ValueError:
        pass
    else:
        raise AssertionError("expected external path rejection")
