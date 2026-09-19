from __future__ import annotations

import multiprocessing
from dataclasses import dataclass
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess

from .ipc import JsonMessageCodec, JsonMessageReceiver, JsonMessageSender, WireMessageError
from .messages import MessageEnvelope, MessageKind

WORKER_CONTROL_JOB_ID = "__worker_control__"


class WorkerProcessError(RuntimeError):
    """Raised when the concrete worker-process adapter cannot satisfy its contract."""


class ProcessWorkerHandle:
    """WorkerHandle-compatible wrapper around a spawned process and command channel."""

    def __init__(
        self,
        *,
        worker_id: str,
        process: BaseProcess,
        command_sender: JsonMessageSender,
    ) -> None:
        self._worker_id = worker_id
        self._process = process
        self._command_sender = command_sender
        self._stop_requested = False

    @property
    def pid(self) -> int:
        pid = self._process.pid
        if pid is None:
            raise WorkerProcessError("worker process has not started")
        return pid

    def is_alive(self) -> bool:
        return self._process.is_alive()

    def request_stop(self) -> None:
        if self._stop_requested or not self.is_alive():
            return
        self._command_sender.send(
            MessageEnvelope.create(
                kind=MessageKind.COMMAND,
                message_type="StopWorker",
                job_id=WORKER_CONTROL_JOB_ID,
                worker_id=self._worker_id,
            )
        )
        self._stop_requested = True

    def join(self, timeout_seconds: float | None = None) -> None:
        self._process.join(timeout_seconds)

    def terminate(self) -> None:
        if self.is_alive():
            self._process.terminate()


@dataclass
class ProcessWorkerSession:
    """Parent-side worker process session with directional JSON message channels."""

    worker_id: str
    handle: ProcessWorkerHandle
    command_sender: JsonMessageSender
    event_receiver: JsonMessageReceiver
    command_connection: Connection
    event_connection: Connection

    def send_command(self, message: MessageEnvelope) -> None:
        if message.kind != MessageKind.COMMAND:
            raise WorkerProcessError("worker command channel accepts COMMAND messages only")
        if message.worker_id != self.worker_id:
            raise WorkerProcessError("worker command identity mismatch")
        self.command_sender.send(message)

    def receive_event(self, *, timeout_seconds: float = 5.0) -> MessageEnvelope:
        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        if not self.event_connection.poll(timeout_seconds):
            raise TimeoutError("timed out waiting for worker event")
        message = self.event_receiver.receive(expected_worker_id=self.worker_id)
        if message.kind != MessageKind.EVENT:
            raise WorkerProcessError("worker event channel produced a non-EVENT message")
        return message

    def wait_for_exit(self, timeout_seconds: float | None = None) -> bool:
        self.handle.join(timeout_seconds)
        return not self.handle.is_alive()

    def close(self) -> None:
        self.command_connection.close()
        self.event_connection.close()


class WindowsSpawnWorkerFactory:
    """Create isolated workers through explicit multiprocessing spawn semantics."""

    def __init__(self, *, max_message_bytes: int = 1024 * 1024) -> None:
        self._codec = JsonMessageCodec(max_message_bytes=max_message_bytes)
        self._context = multiprocessing.get_context("spawn")

    def spawn(self, worker_id: str) -> ProcessWorkerSession:
        if not worker_id:
            raise ValueError("worker_id is required")

        command_receiver, command_sender_connection = self._context.Pipe(duplex=False)
        event_receiver_connection, event_sender = self._context.Pipe(duplex=False)
        process = self._context.Process(
            target=worker_process_entrypoint,
            args=(
                worker_id,
                command_receiver,
                event_sender,
                self._codec.max_message_bytes,
            ),
            name=f"mtkrita-worker-{worker_id}",
        )
        process.start()

        command_receiver.close()
        event_sender.close()

        command_sender = JsonMessageSender(command_sender_connection, self._codec)
        session = ProcessWorkerSession(
            worker_id=worker_id,
            handle=ProcessWorkerHandle(
                worker_id=worker_id,
                process=process,
                command_sender=command_sender,
            ),
            command_sender=command_sender,
            event_receiver=JsonMessageReceiver(event_receiver_connection, self._codec),
            command_connection=command_sender_connection,
            event_connection=event_receiver_connection,
        )
        session.send_command(
            MessageEnvelope.create(
                kind=MessageKind.COMMAND,
                message_type="WorkerInitialize",
                job_id=WORKER_CONTROL_JOB_ID,
                worker_id=worker_id,
            )
        )
        return session


def worker_process_entrypoint(
    worker_id: str,
    command_connection: Connection,
    event_connection: Connection,
    max_message_bytes: int,
) -> None:
    """Top-level spawn-safe child entrypoint; contains no authoritative shared state."""

    codec = JsonMessageCodec(max_message_bytes=max_message_bytes)
    receiver = JsonMessageReceiver(command_connection, codec)
    sender = JsonMessageSender(event_connection, codec)
    try:
        initialize = receiver.receive(expected_worker_id=worker_id)
        if initialize.kind != MessageKind.COMMAND or initialize.message_type != "WorkerInitialize":
            _send_internal_error(
                sender,
                worker_id=worker_id,
                causation=initialize,
                detail="first worker command must be WorkerInitialize",
            )
            return
        sender.send(
            _worker_event(
                "WorkerReady",
                worker_id=worker_id,
                causation=initialize,
                payload={"pid": multiprocessing.current_process().pid},
            )
        )

        while True:
            command = receiver.receive(expected_worker_id=worker_id)
            if command.kind != MessageKind.COMMAND:
                _send_internal_error(
                    sender,
                    worker_id=worker_id,
                    causation=command,
                    detail="worker command channel accepts COMMAND messages only",
                )
                continue

            if command.message_type == "PingWorker":
                sender.send(
                    _worker_event(
                        "WorkerHeartbeat",
                        worker_id=worker_id,
                        causation=command,
                    )
                )
                continue

            if command.message_type == "StopWorker":
                sender.send(
                    _worker_event(
                        "WorkerStopping",
                        worker_id=worker_id,
                        causation=command,
                    )
                )
                sender.send(
                    _worker_event(
                        "WorkerStopped",
                        worker_id=worker_id,
                        causation=command,
                    )
                )
                return

            if command.message_type == "ExecuteTask":
                _send_internal_error(
                    sender,
                    worker_id=worker_id,
                    causation=command,
                    detail="ExecuteTask executor is not connected in the process-adapter baseline",
                )
                continue

            _send_internal_error(
                sender,
                worker_id=worker_id,
                causation=command,
                detail=f"unsupported worker command: {command.message_type}",
            )
    except (EOFError, BrokenPipeError, OSError, WireMessageError) as exc:
        try:
            _send_internal_error(
                sender,
                worker_id=worker_id,
                causation=None,
                detail=f"worker transport failure: {type(exc).__name__}",
            )
        except (BrokenPipeError, OSError, WireMessageError):
            pass
    finally:
        command_connection.close()
        event_connection.close()


def _worker_event(
    message_type: str,
    *,
    worker_id: str,
    causation: MessageEnvelope,
    payload: dict[str, object] | None = None,
) -> MessageEnvelope:
    return MessageEnvelope.create(
        kind=MessageKind.EVENT,
        message_type=message_type,
        job_id=causation.job_id,
        correlation_id=causation.correlation_id,
        causation_id=causation.message_id,
        task_id=causation.task_id,
        frame_id=causation.frame_id,
        stage_id=causation.stage_id,
        worker_id=worker_id,
        attempt=causation.attempt,
        payload=payload,
    )


def _send_internal_error(
    sender: JsonMessageSender,
    *,
    worker_id: str,
    causation: MessageEnvelope | None,
    detail: str,
) -> None:
    sender.send(
        MessageEnvelope.create(
            kind=MessageKind.EVENT,
            message_type="WorkerInternalError",
            job_id=causation.job_id if causation is not None else WORKER_CONTROL_JOB_ID,
            correlation_id=causation.correlation_id if causation is not None else None,
            causation_id=causation.message_id if causation is not None else None,
            task_id=causation.task_id if causation is not None else None,
            frame_id=causation.frame_id if causation is not None else None,
            stage_id=causation.stage_id if causation is not None else None,
            worker_id=worker_id,
            attempt=causation.attempt if causation is not None else None,
            payload={"detail": detail},
        )
    )
