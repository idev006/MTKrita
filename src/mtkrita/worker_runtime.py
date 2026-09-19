from __future__ import annotations

from time import monotonic
from typing import Protocol

from .messages import MessageEnvelope, MessageKind
from .worker_events import RoutedWorkerEvent, WorkerEventRouter
from .worker_manager import WorkerHandle, WorkerManager, WorkerRecord, WorkerState
from .worker_process import WORKER_CONTROL_JOB_ID


class WorkerRuntimeSession(Protocol):
    worker_id: str
    handle: WorkerHandle

    def send_command(self, message: MessageEnvelope) -> None: ...

    def receive_event(self, *, timeout_seconds: float = 5.0) -> MessageEnvelope: ...

    def wait_for_exit(self, timeout_seconds: float | None = None) -> bool: ...

    def close(self) -> None: ...


class WorkerProcessFactory(Protocol):
    def spawn(self, worker_id: str) -> WorkerRuntimeSession: ...


class WorkerRuntimeController:
    """Application service coordinating process sessions with authoritative worker state."""

    def __init__(
        self,
        *,
        factory: WorkerProcessFactory,
        workers: WorkerManager,
        events: WorkerEventRouter,
    ) -> None:
        self._factory = factory
        self._workers = workers
        self._events = events
        self._sessions: dict[str, WorkerRuntimeSession] = {}

    def start(self, worker_id: str, *, ready_timeout_seconds: float = 10.0) -> WorkerRecord:
        if ready_timeout_seconds <= 0:
            raise ValueError("ready_timeout_seconds must be positive")
        if worker_id in self._sessions:
            raise ValueError("worker runtime session already exists")

        session = self._factory.spawn(worker_id)
        try:
            self._workers.register(worker_id, session.handle)
            self._sessions[worker_id] = session
            routed = self.pump_once(worker_id, timeout_seconds=ready_timeout_seconds)
            if routed.message.message_type != "WorkerReady":
                raise RuntimeError("worker did not produce WorkerReady as first routed event")
            return routed.worker
        except Exception:
            self._sessions.pop(worker_id, None)
            try:
                session.handle.request_stop()
            except (BrokenPipeError, OSError):
                pass
            session.close()
            raise

    def pump_once(self, worker_id: str, *, timeout_seconds: float = 5.0) -> RoutedWorkerEvent:
        session = self._session(worker_id)
        message = session.receive_event(timeout_seconds=timeout_seconds)
        return self._events.route(message)

    def ping(self, worker_id: str) -> MessageEnvelope:
        current = self._workers.get(worker_id)
        if current.state not in {WorkerState.READY, WorkerState.BUSY}:
            raise RuntimeError("only READY or BUSY worker may be pinged")
        command = MessageEnvelope.create(
            kind=MessageKind.COMMAND,
            message_type="PingWorker",
            job_id=WORKER_CONTROL_JOB_ID,
            worker_id=worker_id,
            task_id=current.active_task_id,
            attempt=current.active_attempt,
        )
        self._session(worker_id).send_command(command)
        return command

    def request_stop(self, worker_id: str) -> WorkerRecord:
        return self._workers.request_stop(worker_id)

    def stop(self, worker_id: str, *, timeout_seconds: float = 5.0) -> WorkerRecord:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        current = self._workers.get(worker_id)
        if current.state == WorkerState.STOPPED:
            return current
        if current.state == WorkerState.LOST:
            return current

        self.request_stop(worker_id)
        deadline = monotonic() + timeout_seconds
        while self._workers.get(worker_id).state == WorkerState.STOPPING:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError("timed out waiting for worker to stop")
            self.pump_once(worker_id, timeout_seconds=remaining)

        remaining = max(0.0, deadline - monotonic())
        if not self._session(worker_id).wait_for_exit(remaining):
            raise TimeoutError("worker emitted stop event but process did not exit")
        return self._workers.get(worker_id)

    def close(self, worker_id: str) -> None:
        current = self._workers.get(worker_id)
        if current.state not in {WorkerState.STOPPED, WorkerState.LOST}:
            raise RuntimeError("worker session may close only after STOPPED or LOST")
        session = self._sessions.pop(worker_id, None)
        if session is not None:
            session.close()

    def _session(self, worker_id: str) -> WorkerRuntimeSession:
        try:
            return self._sessions[worker_id]
        except KeyError as exc:
            raise KeyError(f"worker runtime session not found: {worker_id}") from exc
