from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mtkrita.worker_manager import WorkerManager, WorkerState


@dataclass
class FakeHandle:
    pid: int
    alive: bool = True
    stop_requested: bool = False

    def is_alive(self) -> bool:
        return self.alive

    def request_stop(self) -> None:
        self.stop_requested = True


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 19, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


def test_worker_lifecycle_ready_busy_ready_and_orderly_stop() -> None:
    clock = FakeClock()
    manager = WorkerManager(clock=clock)
    handle = FakeHandle(pid=101)

    registered = manager.register("worker-1", handle)
    assert registered.state == WorkerState.STARTING
    ready = manager.mark_ready("worker-1")
    assert ready.state == WorkerState.READY
    busy = manager.assign("worker-1", task_id="task-1", attempt=2)
    assert busy.state == WorkerState.BUSY
    assert busy.active_task_id == "task-1"
    assert busy.active_attempt == 2

    released = manager.release_task("worker-1", task_id="task-1", attempt=2)
    assert released.state == WorkerState.READY
    stopping = manager.request_stop("worker-1")
    assert stopping.state == WorkerState.STOPPING
    assert handle.stop_requested is True
    handle.alive = False
    assert manager.refresh_process_state("worker-1").state == WorkerState.STOPPED


def test_worker_heartbeat_timeout_marks_worker_lost() -> None:
    clock = FakeClock()
    manager = WorkerManager(clock=clock)
    manager.register("worker-1", FakeHandle(pid=201))
    manager.mark_ready("worker-1")
    clock.advance(31)

    lost = manager.detect_lost(heartbeat_timeout_seconds=30)

    assert len(lost) == 1
    assert lost[0].worker_id == "worker-1"
    assert lost[0].state == WorkerState.LOST


def test_heartbeat_refresh_prevents_false_worker_loss() -> None:
    clock = FakeClock()
    manager = WorkerManager(clock=clock)
    manager.register("worker-1", FakeHandle(pid=301))
    manager.mark_ready("worker-1")
    clock.advance(20)
    manager.heartbeat("worker-1")
    clock.advance(20)

    assert manager.detect_lost(heartbeat_timeout_seconds=30) == ()


def test_dead_process_is_lost_even_before_heartbeat_timeout() -> None:
    clock = FakeClock()
    handle = FakeHandle(pid=401)
    manager = WorkerManager(clock=clock)
    manager.register("worker-1", handle)
    manager.mark_ready("worker-1")
    handle.alive = False

    lost = manager.detect_lost(heartbeat_timeout_seconds=60)

    assert len(lost) == 1
    assert lost[0].state == WorkerState.LOST


def test_stale_task_release_is_rejected() -> None:
    manager = WorkerManager()
    manager.register("worker-1", FakeHandle(pid=501))
    manager.mark_ready("worker-1")
    manager.assign("worker-1", task_id="task-1", attempt=3)

    try:
        manager.release_task("worker-1", task_id="task-1", attempt=2)
    except RuntimeError as exc:
        assert "ownership mismatch" in str(exc)
    else:
        raise AssertionError("expected stale task release rejection")
