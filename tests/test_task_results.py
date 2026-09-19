from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from mtkrita.artifact_commit import ArtifactCommitCoordinator, ArtifactCommitJournal
from mtkrita.dispatch import DispatchCoordinator
from mtkrita.job_store import JobStore, TaskDescriptorRecord, TaskRecord
from mtkrita.path_manager import PathManager, PathRef
from mtkrita.resource_broker import ResourceBroker
from mtkrita.scheduler import BoundedFairScheduler, ScheduledTask
from mtkrita.task_leases import TaskLeaseRegistry
from mtkrita.task_results import CandidateResultCoordinator, CandidateResultError
from mtkrita.worker_manager import WorkerManager, WorkerState
from mtkrita.worker_tasks import (
    ExecuteTaskCommandBuilder,
    ProvisionalArtifact,
    TaskCandidateResult,
    TaskCandidateStatus,
    candidate_event,
)


@dataclass
class FakeHandle:
    pid: int = 5555
    alive: bool = True

    def is_alive(self) -> bool:
        return self.alive

    def request_stop(self) -> None:
        pass


class FixedTargetResolver:
    def __init__(self, target: PathRef) -> None:
        self.target = target
        self.calls = 0

    def resolve(
        self,
        *,
        task: TaskRecord,
        descriptor: TaskDescriptorRecord,
        artifact: ProvisionalArtifact,
    ) -> PathRef:
        assert descriptor.task_id == task.task_id
        assert artifact.filename
        self.calls += 1
        return self.target


@dataclass
class Harness:
    paths: PathManager
    jobs: JobStore
    resources: ResourceBroker
    leases: TaskLeaseRegistry
    workers: WorkerManager
    scheduler: BoundedFairScheduler
    resolver: FixedTargetResolver
    coordinator: CandidateResultCoordinator
    command: object


def _harness(tmp_path: Path, *, attempt_seed: int = 0) -> Harness:
    paths = PathManager(tmp_path / "workspace")
    paths.prepare_job("job-1")
    jobs = JobStore(paths.evidence("job-1", "jobs.sqlite3").path)
    jobs.initialize()
    jobs.create_job("job-1")
    jobs.create_task(
        "task-1",
        job_id="job-1",
        descriptor={"frame_id": 1, "output_name": "01.png"},
        descriptor_version=1,
    )
    if attempt_seed:
        seeded = jobs.assign_task(
            "task-1",
            expected_generation=0,
            worker_id="seed-worker",
            attempt=attempt_seed,
            lease_expires_at="2030-01-01T00:00:00+00:00",
        )
        jobs.finish_task(
            "task-1",
            expected_generation=seeded.generation,
            worker_id="seed-worker",
            attempt=attempt_seed,
            new_state="INTERRUPTED",
            event_code="TASK.SEED_INTERRUPTED",
        )

    scheduler = BoundedFairScheduler(max_inflight_tasks=1, max_queued_tasks=4)
    scheduler.submit(ScheduledTask("task-1", "job-1"))
    workers = WorkerManager()
    workers.register("worker-1", FakeHandle())
    workers.mark_ready("worker-1")
    leases = TaskLeaseRegistry()
    dispatch = DispatchCoordinator(
        scheduler=scheduler,
        jobs=jobs,
        leases=leases,
        workers=workers,
    )
    assignment = dispatch.dispatch_next(worker_id="worker-1", lease_seconds=120)
    assert assignment is not None

    resources = ResourceBroker(paths)
    journal = ArtifactCommitJournal(jobs)
    journal.initialize()
    resolver = FixedTargetResolver(paths.output("job-1", "01.png"))
    coordinator = CandidateResultCoordinator(
        jobs=jobs,
        paths=paths,
        resources=resources,
        commits=ArtifactCommitCoordinator(journal, resources),
        leases=leases,
        workers=workers,
        targets=resolver,
        inflight=scheduler,
    )
    command = ExecuteTaskCommandBuilder(jobs=jobs, paths=paths).build("task-1")
    return Harness(
        paths=paths,
        jobs=jobs,
        resources=resources,
        leases=leases,
        workers=workers,
        scheduler=scheduler,
        resolver=resolver,
        coordinator=coordinator,
        command=command,
    )


def _artifact(harness: Harness, data: bytes = b"candidate-png") -> ProvisionalArtifact:
    path = harness.paths.worker_file("job-1", "worker-1", "candidate.png").path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return ProvisionalArtifact(
        filename="candidate.png",
        sha256=hashlib.sha256(data).hexdigest(),
        byte_size=len(data),
    )


def test_success_candidate_commits_one_artifact_then_releases_runtime(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    artifact = _artifact(harness)
    event = candidate_event(
        result=TaskCandidateResult(
            status=TaskCandidateStatus.SUCCEEDED,
            artifacts=(artifact,),
        ),
        causation=harness.command,
    )

    outcome = harness.coordinator.accept(event)

    assert outcome.task.state == "SUCCEEDED"
    assert outcome.committed_artifact is not None
    assert harness.paths.output("job-1", "01.png").path.read_bytes() == b"candidate-png"
    assert not harness.paths.worker_file("job-1", "worker-1", "candidate.png").path.exists()
    assert harness.workers.get("worker-1").state == WorkerState.READY
    assert harness.scheduler.inflight_count == 0
    with pytest.raises(ValueError, match="no active lease"):
        harness.leases.require_active("task-1", worker_id="worker-1", attempt=1)


def test_success_candidate_hash_mismatch_leaves_task_running(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    artifact = _artifact(harness)
    bad = replace(artifact, sha256="b" * 64)
    event = candidate_event(
        result=TaskCandidateResult(
            status=TaskCandidateStatus.SUCCEEDED,
            artifacts=(bad,),
        ),
        causation=harness.command,
    )

    with pytest.raises(ValueError, match="hash mismatch"):
        harness.coordinator.accept(event)

    assert harness.jobs.get_task("task-1").state == "RUNNING"
    assert harness.workers.get("worker-1").state == WorkerState.BUSY
    assert harness.scheduler.inflight_count == 1
    assert not harness.paths.output("job-1", "01.png").path.exists()


def test_success_candidate_byte_size_mismatch_leaves_task_running(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    artifact = _artifact(harness)
    bad = replace(artifact, byte_size=artifact.byte_size + 1)
    event = candidate_event(
        result=TaskCandidateResult(
            status=TaskCandidateStatus.SUCCEEDED,
            artifacts=(bad,),
        ),
        causation=harness.command,
    )

    with pytest.raises(CandidateResultError, match="byte-size"):
        harness.coordinator.accept(event)

    assert harness.jobs.get_task("task-1").state == "RUNNING"
    assert not harness.paths.output("job-1", "01.png").path.exists()


def test_success_candidate_requires_exactly_one_artifact(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    artifact = _artifact(harness)
    for artifacts in ((), (artifact, artifact)):
        event = candidate_event(
            result=TaskCandidateResult(
                status=TaskCandidateStatus.SUCCEEDED,
                artifacts=artifacts,
            ),
            causation=harness.command,
        )
        with pytest.raises(CandidateResultError, match="exactly one"):
            harness.coordinator.accept(event)
    assert harness.jobs.get_task("task-1").state == "RUNNING"


def test_stale_attempt_candidate_is_rejected_before_commit(tmp_path: Path) -> None:
    harness = _harness(tmp_path, attempt_seed=1)
    artifact = _artifact(harness)
    event = candidate_event(
        result=TaskCandidateResult(
            status=TaskCandidateStatus.SUCCEEDED,
            artifacts=(artifact,),
        ),
        causation=harness.command,
    )
    stale = replace(event, attempt=1)

    with pytest.raises(CandidateResultError, match="authoritative RUNNING"):
        harness.coordinator.accept(stale)

    assert harness.jobs.get_task("task-1").state == "RUNNING"
    assert harness.resolver.calls == 0


def test_cross_job_target_is_rejected_without_promotion(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    harness.paths.prepare_job("job-2")
    harness.resolver.target = harness.paths.output("job-2", "01.png")
    artifact = _artifact(harness)
    event = candidate_event(
        result=TaskCandidateResult(
            status=TaskCandidateStatus.SUCCEEDED,
            artifacts=(artifact,),
        ),
        causation=harness.command,
    )

    with pytest.raises(CandidateResultError, match="cross-job"):
        harness.coordinator.accept(event)

    assert harness.jobs.get_task("task-1").state == "RUNNING"
    assert not harness.paths.output("job-2", "01.png").path.exists()


def test_review_candidate_transitions_before_runtime_release(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    event = candidate_event(
        result=TaskCandidateResult(status=TaskCandidateStatus.REVIEW),
        causation=harness.command,
    )

    outcome = harness.coordinator.accept(event)

    assert outcome.task.state == "REVIEW"
    assert harness.workers.get("worker-1").state == WorkerState.READY
    assert harness.scheduler.inflight_count == 0


def test_failed_candidate_transitions_before_runtime_release(tmp_path: Path) -> None:
    harness = _harness(tmp_path)
    event = candidate_event(
        result=TaskCandidateResult(
            status=TaskCandidateStatus.FAILED,
            error_code="PROVIDER.FAILURE",
            error_message="provider failed",
        ),
        causation=harness.command,
    )

    outcome = harness.coordinator.accept(event)

    assert outcome.task.state == "FAILED"
    assert harness.workers.get("worker-1").state == WorkerState.READY
    assert harness.scheduler.inflight_count == 0
