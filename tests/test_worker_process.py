import sys
from contextlib import suppress

import pytest

from mtkrita.messages import MessageEnvelope, MessageKind
from mtkrita.worker_process import (
    WORKER_CONTROL_JOB_ID,
    WindowsSpawnWorkerFactory,
    WorkerProcessError,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows spawn runtime smoke test")


def _command(message_type: str, *, worker_id: str) -> MessageEnvelope:
    return MessageEnvelope.create(
        kind=MessageKind.COMMAND,
        message_type=message_type,
        job_id=WORKER_CONTROL_JOB_ID,
        worker_id=worker_id,
    )


def test_windows_spawn_worker_ready_ping_and_graceful_stop() -> None:
    session = WindowsSpawnWorkerFactory().spawn("worker-smoke")
    try:
        ready = session.receive_event(timeout_seconds=10)
        assert ready.message_type == "WorkerReady"
        assert ready.worker_id == "worker-smoke"
        assert ready.payload["pid"] == session.handle.pid
        assert session.handle.is_alive() is True

        session.send_command(_command("PingWorker", worker_id="worker-smoke"))
        heartbeat = session.receive_event(timeout_seconds=5)
        assert heartbeat.message_type == "WorkerHeartbeat"
        assert heartbeat.worker_id == "worker-smoke"

        session.handle.request_stop()
        stopping = session.receive_event(timeout_seconds=5)
        stopped = session.receive_event(timeout_seconds=5)
        assert stopping.message_type == "WorkerStopping"
        assert stopped.message_type == "WorkerStopped"

        session.handle.join(5)
        assert session.handle.is_alive() is False
    finally:
        if session.handle.is_alive():
            session.handle.terminate()
            session.handle.join(5)
        session.close()


def test_windows_worker_command_channel_rejects_event_direction() -> None:
    session = WindowsSpawnWorkerFactory().spawn("worker-direction")
    try:
        ready = session.receive_event(timeout_seconds=10)
        assert ready.message_type == "WorkerReady"

        event = MessageEnvelope.create(
            kind=MessageKind.EVENT,
            message_type="NotACommand",
            job_id=WORKER_CONTROL_JOB_ID,
            worker_id="worker-direction",
        )
        with pytest.raises(WorkerProcessError, match="COMMAND"):
            session.send_command(event)
    finally:
        with suppress(BrokenPipeError, OSError):
            session.handle.request_stop()
        if session.handle.is_alive():
            with suppress(TimeoutError, EOFError, OSError):
                session.receive_event(timeout_seconds=2)
                session.receive_event(timeout_seconds=2)
            session.handle.join(5)
        if session.handle.is_alive():
            session.handle.terminate()
            session.handle.join(5)
        session.close()
