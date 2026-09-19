from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from mtkrita.artifact_commit import ArtifactCommitCoordinator, ArtifactCommitJournal
from mtkrita.dispatch import DispatchCoordinator
from mtkrita.event_bus import InProcessEventBus
from mtkrita.job_store import JobStore, TaskDescriptorRecord, TaskRecord
from mtkrita.messages import MessageEnvelope, MessageKind
from mtkrita.path_manager import PathManager, PathRef
from mtkrita.resource_broker import ResourceBroker
from mtkrita.scheduler import BoundedFairScheduler, ScheduledTask
from mtkrita.task_leases import TaskLeaseRegistry
from mtkrita.task_results import CandidateResultCoordinator
from mtkrita.worker_events import WorkerEventRouter
from mtkrita.worker_manager import WorkerManager, WorkerState
from mtkrita.worker_tasks import (
    ExecuteTaskCommandBuilder,
    ExecuteTaskRequest,
    ProvisionalArtifact,
    TaskCandidateResult,
    TaskCandidateStatus,
    candidate_event,
    parse_execute_task,
)


@dataclass
class FakeHandle:
    pid: int = 7001

    def is_alive(self) -> bool:
        return True

    def request_stop(self) -> None:
        pass


class DescriptorTargetResolver:
    def __init__(self, paths: PathManager) -> None:
        self._paths = paths

    def resolve(
        self,
        *,
        task: TaskRecord,
        descriptor: TaskDescriptorRecord,
        artifact: ProvisionalArtifact,
    ) -> PathRef:
        output_name = descriptor.descriptor["output_name"]
        assert isinstance(output_name, str)
        return self._paths.output(task.job_id, output_name)


class ScratchWritingExecutor:
    """Test-only executor proving the interface without adding a production fake-success path."""

    def execute(self, request: ExecuteTaskRequest) -> TaskCandidateResult:
        data = b"integration-candidate"
        filename = "candidate.png"
        path = Path(request.scratch_path) / filename
        path.mkdir(parents=True, exist_ok=True) if False else None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return TaskCandidateResult(
            status=TaskCandidateStatus.SUCCEEDED,
            artifacts=(
                ProvisionalArtifact(
                    filename=filename,
                    sha256=hashlib.sha256(data).hexdigest(),
                    byte_size=len(data),
                ),
            ),
            findings=({"code": "INTEGRATION.OK"},),
        )


def test_dispatched_task_candidate_reaches_durable_success_only_through_commit(
    tmp_path: Path,
) -> None:
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

    scheduler = BoundedFairScheduler(max_inflight_tasks=1, max_queued_tasks=2)
    scheduler.submit(ScheduledTask("task-1", "job-1"))
    workers = WorkerManager()
    workers.register("worker-1", FakeHandle())
    workers.mark_ready("worker-1")
    leases = TaskLeaseRegistry()
    assignment = DispatchCoordinator(
        scheduler=scheduler,
        jobs=jobs,
        leases=leases,
        workers=workers,
    ).dispatch_next(worker_id="worker-1", lease_seconds=120)
    assert assignment is not None
    assert jobs.get_task("task-1").state == "RUNNING"

    command = ExecuteTaskCommandBuilder(jobs=jobs, paths=paths).build("task-1")
    request = parse_execute_task(command)
    result = ScratchWritingExecutor().execute(request)

    bus = InProcessEventBus()
    observed: list[str] = []
    bus.subscribe_all(lambda message: observed.append(message.message_type))
    router = WorkerEventRouter(workers=workers, events=bus)
    started = MessageEnvelope.create(
        kind=MessageKind.EVENT,
        message_type="TaskStarted",
        job_id=command.job_id,
        correlation_id=command.correlation_id,
        causation_id=command.message_id,
        task_id=command.task_id,
        worker_id=command.worker_id,
        attempt=command.attempt,
    )
    router.route(started)
    candidate = candidate_event(result=result, causation=command)
    router.route(candidate)

    assert jobs.get_task("task-1").state == "RUNNING"
    assert workers.get("worker-1").state == WorkerState.BUSY
    assert observed == ["TaskStarted", "TaskSucceededCandidate"]

    resources = ResourceBroker(paths)
    journal = ArtifactCommitJournal(jobs)
    journal.initialize()
    outcome = CandidateResultCoordinator(
        jobs=jobs,
        paths=paths,
        resources=resources,
        commits=ArtifactCommitCoordinator(journal, resources),
        leases=leases,
        workers=workers,
        targets=DescriptorTargetResolver(paths),
        inflight=scheduler,
    ).accept(candidate)

    assert outcome.task.state == "SUCCEEDED"
    assert paths.output("job-1", "01.png").path.read_bytes() == b"integration-candidate"
    assert workers.get("worker-1").state == WorkerState.READY
    assert scheduler.inflight_count == 0
