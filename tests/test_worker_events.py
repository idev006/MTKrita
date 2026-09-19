from dataclasses import dataclass

import pytest

from mtkrita.event_bus import InProcessEventBus
from mtkrita.messages import MessageEnvelope, MessageKind
from mtkrita.worker_events import WorkerEventError, WorkerEventRouter
from mtkrita.worker_manager import WorkerManager, WorkerState


@dataclass
class FakeHandle:
    pid: int = 1234
    alive: bool = True

    def is_alive(self) -> bool:
        return self.alive

    def request_stop(self) -> None:
        pass


def _event(
    message_type: str,
    *,
    worker_id: str = "worker-1",
    task_id: str | None = None,
    attempt: int | None = None,
) -> MessageEnvelope:
    return MessageEnvelope.create(
        kind=MessageKind.EVENT,
        message_type=message_type,
        job_id="job-1",
        worker_id=worker_id,
        task_id=task_id,
        attempt=attempt,
    )


def test_worker_ready_and_heartbeat_update_manager_before_publish() -> None:
    workers = WorkerManager()
    workers.register("worker-1", FakeHandle())
    bus = InProcessEventBus()
    observed: list[WorkerState] = []
    router = WorkerEventRouter(workers=workers, events=bus)
    bus.subscribe_all(lambda message: observed.append(workers.get(message.worker_id or "").state))

    ready = router.route(_event("WorkerReady"))
    heartbeat = router.route(_event("WorkerHeartbeat"))

    assert ready.worker.state == WorkerState.READY
    assert heartbeat.worker.state == WorkerState.READY
    assert observed == [WorkerState.READY, WorkerState.READY]


def test_task_candidate_requires_authoritative_busy_identity_and_does_not_release_worker() -> None:
    workers = WorkerManager()
    workers.register("worker-1", FakeHandle())
    workers.mark_ready("worker-1")
    workers.assign("worker-1", task_id="task-1", attempt=2)
    bus = InProcessEventBus()
    published: list[str] = []
    bus.subscribe_all(lambda message: published.append(message.message_type))
    router = WorkerEventRouter(workers=workers, events=bus)

    routed = router.route(
        _event("TaskSucceededCandidate", task_id="task-1", attempt=2)
    )

    assert routed.worker.state == WorkerState.BUSY
    assert routed.worker.active_task_id == "task-1"
    assert published == ["TaskSucceededCandidate"]

    with pytest.raises(WorkerEventError, match="identity mismatch"):
        router.route(_event("TaskSucceededCandidate", task_id="task-1", attempt=1))
    assert published == ["TaskSucceededCandidate"]


def test_busy_heartbeat_must_carry_exact_task_attempt() -> None:
    workers = WorkerManager()
    workers.register("worker-1", FakeHandle())
    workers.mark_ready("worker-1")
    workers.assign("worker-1", task_id="task-1", attempt=3)
    router = WorkerEventRouter(workers=workers, events=InProcessEventBus())

    with pytest.raises(WorkerEventError, match="task_id and attempt"):
        router.route(_event("WorkerHeartbeat"))

    heartbeat = router.route(_event("WorkerHeartbeat", task_id="task-1", attempt=3))
    assert heartbeat.worker.state == WorkerState.BUSY


def test_worker_stopped_requires_stop_authority_and_becomes_terminal() -> None:
    workers = WorkerManager()
    workers.register("worker-1", FakeHandle())
    workers.mark_ready("worker-1")
    router = WorkerEventRouter(workers=workers, events=InProcessEventBus())

    with pytest.raises(WorkerEventError, match="STOPPING"):
        router.route(_event("WorkerStopped"))

    workers.request_stop("worker-1")
    router.route(_event("WorkerStopping"))
    stopped = router.route(_event("WorkerStopped"))
    assert stopped.worker.state == WorkerState.STOPPED


def test_router_rejects_unknown_event_without_publish() -> None:
    workers = WorkerManager()
    workers.register("worker-1", FakeHandle())
    bus = InProcessEventBus()
    published: list[str] = []
    bus.subscribe_all(lambda message: published.append(message.message_type))
    router = WorkerEventRouter(workers=workers, events=bus)

    with pytest.raises(WorkerEventError, match="unsupported"):
        router.route(_event("UnknownWorkerEvent"))
    assert published == []
