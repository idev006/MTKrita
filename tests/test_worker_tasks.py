from pathlib import Path

import pytest

from mtkrita.job_store import JobStore
from mtkrita.path_manager import PathManager
from mtkrita.worker_tasks import (
    ExecuteTaskCommandBuilder,
    ProvisionalArtifact,
    TaskCandidateResult,
    TaskCandidateStatus,
    WorkerTaskContractError,
    candidate_event,
    parse_candidate_event,
    parse_execute_task,
)


def _assigned_task(tmp_path: Path):
    paths = PathManager(tmp_path / "workspace")
    paths.prepare_job("job-1")
    jobs = JobStore(paths.evidence("job-1", "jobs.sqlite3").path)
    jobs.initialize()
    jobs.create_job("job-1")
    jobs.create_task(
        "task-1",
        job_id="job-1",
        priority=10,
        descriptor={"frame_id": 1, "stage_plan": ["inspect", "export"]},
        descriptor_version=1,
    )
    jobs.assign_task(
        "task-1",
        expected_generation=0,
        worker_id="worker-1",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )
    return paths, jobs


def test_execute_task_builder_uses_durable_assignment_and_path_manager(tmp_path: Path) -> None:
    paths, jobs = _assigned_task(tmp_path)

    command = ExecuteTaskCommandBuilder(jobs=jobs, paths=paths).build("task-1")
    request = parse_execute_task(command)

    assert request.job_id == "job-1"
    assert request.task_id == "task-1"
    assert request.worker_id == "worker-1"
    assert request.attempt == 1
    assert request.descriptor_version == 1
    assert request.descriptor["frame_id"] == 1
    assert Path(request.scratch_path) == paths.worker_scratch("job-1", "worker-1").path
    assert Path(request.scratch_path).is_dir()
    assert "target_path" not in command.payload
    assert "output_path" not in command.payload


def test_execute_task_builder_rejects_non_running_task(tmp_path: Path) -> None:
    paths = PathManager(tmp_path / "workspace")
    paths.prepare_job("job-1")
    jobs = JobStore(paths.evidence("job-1", "jobs.sqlite3").path)
    jobs.initialize()
    jobs.create_job("job-1")
    jobs.create_task("task-1", job_id="job-1", descriptor={"frame_id": 1})

    with pytest.raises(RuntimeError, match="RUNNING"):
        ExecuteTaskCommandBuilder(jobs=jobs, paths=paths).build("task-1")


def test_candidate_result_round_trip_preserves_only_provisional_artifact_evidence(
    tmp_path: Path,
) -> None:
    paths, jobs = _assigned_task(tmp_path)
    command = ExecuteTaskCommandBuilder(jobs=jobs, paths=paths).build("task-1")
    result = TaskCandidateResult(
        status=TaskCandidateStatus.SUCCEEDED,
        artifacts=(
            ProvisionalArtifact(
                filename="candidate.png",
                sha256="a" * 64,
                byte_size=123,
            ),
        ),
        findings=({"code": "QA.OK"},),
    )

    event = candidate_event(result=result, causation=command)
    parsed = parse_candidate_event(event)

    assert event.message_type == "TaskSucceededCandidate"
    assert event.worker_id == "worker-1"
    assert event.attempt == 1
    assert parsed == result
    assert set(event.payload["artifacts"][0]) == {"filename", "sha256", "byte_size"}


def test_provisional_artifact_rejects_path_traversal_and_bad_hash() -> None:
    with pytest.raises(WorkerTaskContractError, match="path component"):
        ProvisionalArtifact(filename="../escape.png", sha256="a" * 64, byte_size=1)

    with pytest.raises(WorkerTaskContractError, match="sha256"):
        ProvisionalArtifact(filename="candidate.png", sha256="NOT-A-HASH", byte_size=1)


def test_failed_candidate_requires_error_code() -> None:
    with pytest.raises(WorkerTaskContractError, match="error_code"):
        TaskCandidateResult(status=TaskCandidateStatus.FAILED)
