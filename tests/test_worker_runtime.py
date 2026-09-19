from __future__ import annotations

from dataclasses import dataclass

import pytest

from mtkrita.event_bus import InProcessEventBus
from mtkrita.messages import MessageEnvelope, MessageKind
from mtkrita.worker_events import WorkerEventRouter
from mtkrita.worker_manager import WorkerManager, WorkerState
from mtkrita.worker_process import WORKER_CONTROL_JOB_ID
from mtkrita.worker_runtime import WorkerRuntimeController


@dataclass
class FakeHandle:
    pid: int
    session: FakeSession | None = None
    alive: bool = True

    def is_alive(self) -> bool:
        return self.alive

    def request_stop(self) -> None:
        if self.session is None or not self.alive:
            return
        self.session.events.extend(
            [
                self.session.event("WorkerStopping"),
                self.session.event("WorkerStopped"),
            ]
        )
        self.alive = False


class FakeSession:
    def __init__(self, worker_id: str) -> None:
        self.worker_id = worker_id
        self.handle = FakeHandle(pid=4321)
        self.handle.session = self
        self.events = [self.event("WorkerReady")]
        self.commands: list[MessageEnvelope] = []
        self.closed = False

    def event(
        self,
        message_type: str,
        *,
        task_id: str | None = None,
        attempt: int | None = None,
    ) -> MessageEnvelope:
        return MessageEnvelope.create(
            kind=MessageKind.EVENT,
            message_type=message_type,
            job_id=WORKER_CONTROL_JOB_ID,
            worker_id=self.worker_id,
            task_id=task_id,
            attempt=attempt,
        )

    def send_command(self, message: MessageEnvelope) -> None:
        self.commands.append(message)
        if message.message_type == "PingWorker":
            self.events.append(
                self.event(
                    "WorkerHeartbeat",
                    task_id=message.task_id,
                    attempt=message.attempt,
                )
            )

    def receive_event(self, *, timeout_seconds: float = 5.0) -> MessageEnvelope:
        if timeout_seconds < 0:
            raise ValueError
        if not self.events:
            raise TimeoutError("no fake worker event")
        return self.events.pop(0)

    def wait_for_exit(self, timeout_seconds: float | None = None) -> bool:
        return not self.handle.alive

    def close(self) -> None:
        self.closed = True


class FakeFactory:
    def __init__(self) -> None:
        self.sessions: dict[str, FakeSession] = {}

    def spawn(self, worker_id: str) -> FakeSession:
        session = FakeSession(worker_id)
        self.sessions[worker_id] = session
        return session


def _runtime() -> tuple[WorkerRuntimeController, WorkerManager, FakeFactory, list[str]]:
    workers = WorkerManager()
    bus = InProcessEventBus()
    published: list[str] = []
    bus.subscribe_all(lambda message: published.append(message.message_type))
    factory = FakeFactory()
    controller = WorkerRuntimeController(
        factory=factory,
        workers=workers,
        events=WorkerEventRouter(workers=workers, events=bus),
    )
    return controller, workers, factory, published


def test_runtime_start_ping_stop_and_close() -> None:
    runtime, workers, factory, published = _runtime()

    ready = runtime.start("worker-1")
    assert ready.state == WorkerState.READY
    assert published == ["WorkerReady"]

    ping = runtime.ping("worker-1")
    assert ping.message_type == "PingWorker"
    heartbeat = runtime.pump_once("worker-1")
    assert heartbeat.message.message_type == "WorkerHeartbeat"

    stopped = runtime.stop("worker-1")
    assert stopped.state == WorkerState.STOPPED
    assert published[-2:] == ["WorkerStopping", "WorkerStopped"]

    runtime.close("worker-1")
    assert factory.sessions["worker-1"].closed is True
    assert workers.get("worker-1").state == WorkerState.STOPPED


def test_busy_ping_carries_authoritative_task_attempt() -> None:
    runtime, workers, factory, _published = _runtime()
    runtime.start("worker-1")
    workers.assign("worker-1", task_id="task-7", attempt=3)

    command = runtime.ping("worker-1")
    routed = runtime.pump_once("worker-1")

    assert command.task_id == "task-7"
    assert command.attempt == 3
    assert factory.sessions["worker-1"].commands[-1] == command
    assert routed.worker.state == WorkerState.BUSY
    assert routed.worker.active_task_id == "task-7"


def test_runtime_refuses_close_while_worker_is_active() -> None:
    runtime, _workers, _factory, _published = _runtime()
    runtime.start("worker-1")

    with pytest.raises(RuntimeError, match="STOPPED or LOST"):
        runtime.close("worker-1")


def test_runtime_rejects_duplicate_session_identity() -> None:
    runtime, _workers, _factory, _published = _runtime()
    runtime.start("worker-1")

    with pytest.raises(ValueError, match="already exists"):
        runtime.start("worker-1")
