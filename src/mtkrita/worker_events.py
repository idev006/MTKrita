from __future__ import annotations

from dataclasses import dataclass

from .event_bus import InProcessEventBus
from .messages import MessageEnvelope, MessageKind
from .worker_manager import WorkerManager, WorkerRecord, WorkerState


class WorkerEventError(RuntimeError):
    """Raised when a decoded worker event violates runtime identity/state contracts."""


@dataclass(frozen=True)
class RoutedWorkerEvent:
    message: MessageEnvelope
    worker: WorkerRecord


class WorkerEventRouter:
    """Validate worker-originated events before state mutation or EventBus publication."""

    _KNOWN_TYPES = {
        "WorkerReady",
        "WorkerHeartbeat",
        "TaskStarted",
        "TaskSucceededCandidate",
        "TaskReviewCandidate",
        "TaskFailed",
        "WorkerStopping",
        "WorkerStopped",
        "WorkerInternalError",
    }
    _TASK_TYPES = {
        "TaskStarted",
        "TaskSucceededCandidate",
        "TaskReviewCandidate",
        "TaskFailed",
    }

    def __init__(self, *, workers: WorkerManager, events: InProcessEventBus) -> None:
        self._workers = workers
        self._events = events

    def route(self, message: MessageEnvelope) -> RoutedWorkerEvent:
        if message.kind != MessageKind.EVENT:
            raise WorkerEventError("worker event router accepts EVENT messages only")
        if message.message_type not in self._KNOWN_TYPES:
            raise WorkerEventError("unsupported worker event type")
        if message.worker_id is None:
            raise WorkerEventError("worker event requires worker_id")

        current = self._workers.get(message.worker_id)
        if message.message_type == "WorkerReady":
            current = self._workers.mark_ready(message.worker_id)
        elif message.message_type == "WorkerHeartbeat":
            self._validate_heartbeat_identity(current, message)
            current = self._workers.heartbeat(message.worker_id)
        elif message.message_type in self._TASK_TYPES:
            self._require_active_task_identity(current, message)
        elif message.message_type == "WorkerStopping":
            if current.state != WorkerState.STOPPING:
                raise WorkerEventError("WorkerStopping requires authoritative STOPPING state")
        elif message.message_type == "WorkerStopped":
            if current.state != WorkerState.STOPPING:
                raise WorkerEventError("WorkerStopped requires authoritative STOPPING state")
            current = self._workers.mark_stopped(message.worker_id)
        elif message.message_type == "WorkerInternalError":
            if message.task_id is not None or message.attempt is not None:
                self._require_active_task_identity(current, message)

        self._events.publish(message)
        return RoutedWorkerEvent(message=message, worker=current)

    @staticmethod
    def _validate_heartbeat_identity(current: WorkerRecord, message: MessageEnvelope) -> None:
        if current.state == WorkerState.BUSY:
            WorkerEventRouter._require_active_task_identity(current, message)
            return
        if message.task_id is not None or message.attempt is not None:
            raise WorkerEventError("idle worker heartbeat must not claim task ownership")

    @staticmethod
    def _require_active_task_identity(current: WorkerRecord, message: MessageEnvelope) -> None:
        if current.state != WorkerState.BUSY:
            raise WorkerEventError("task event requires BUSY worker")
        if message.task_id is None or message.attempt is None:
            raise WorkerEventError("task event requires task_id and attempt")
        if (
            current.active_task_id != message.task_id
            or current.active_attempt != message.attempt
        ):
            raise WorkerEventError("worker task event identity mismatch")
