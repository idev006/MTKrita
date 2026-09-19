from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from mtkrita.dispatch import DispatchCoordinator
from mtkrita.job_store import JobStore
from mtkrita.scheduler import BoundedFairScheduler, ScheduledTask
from mtkrita.task_leases import TaskLeaseRegistry
from mtkrita.watchdog import WorkerLossCoordinator
from mtkrita.worker_manager import WorkerManager


@dataclass
class FakeHandle:
    pid: int
    alive: bool = True

    def is_alive(self) -> bool:
        return self.alive

    def request_stop(self) -> None:
        pass


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 19, 7, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


def _setup(tmp_path: Path):
    clock = FakeClock()
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    store.create_job("job-1")
    store.create_task("task-1", job_id="job-1")
    scheduler = BoundedFairScheduler(max_inflight_tasks=1, max_queued_tasks=4)
    scheduler.submit(ScheduledTask("task-1", "job-1"))
    workers = WorkerManager(clock=clock)
    handle = FakeHandle(pid=9001)
    workers.register("worker-1", handle)
    workers.mark_ready("worker-1")
    leases = TaskLeaseRegistry(clock=clock)
    dispatch = DispatchCoordinator(
        scheduler=scheduler,
        jobs=store,
        leases=leases,
        workers=workers,
        clock=clock,
    )
    assignment = dispatch.dispatch_next(worker_id="worker-1", lease_seconds=120)
    assert assignment is not None
    watchdog = WorkerLossCoordinator(
        workers=workers,
        jobs=store,
        leases=leases,
        scheduler=scheduler,
    )
    return clock, store, scheduler, workers, handle, leases, watchdog


def test_lost_worker_interrupts_authoritative_task_and_requeues(tmp_path: Path) -> None:
    clock, store, scheduler, _workers, handle, leases, watchdog = _setup(tmp_path)
    handle.alive = False

    outcomes = watchdog.reconcile_lost(heartbeat_timeout_seconds=60, requeue=True)

    assert len(outcomes) == 1
    assert outcomes[0].interrupted is True
    assert outcomes[0].requeued is True
    durable = store.get_task("task-1")
    assert durable.state == "INTERRUPTED"
    assert scheduler.inflight_count == 0
    assert scheduler.queued_count == 1
    assert leases.discard("task-1", worker_id="worker-1", attempt=1) is None
    event_codes = [event.event_code for event in store.list_events("job-1")]
    assert "TASK.INTERRUPTED_BY_WORKER_LOSS" in event_codes


def test_heartbeat_timeout_interrupts_busy_worker_task(tmp_path: Path) -> None:
    clock, store, scheduler, _workers, _handle, _leases, watchdog = _setup(tmp_path)
    clock.advance(121)

    outcomes = watchdog.reconcile_lost(heartbeat_timeout_seconds=120, requeue=False)

    assert len(outcomes) == 1
    assert outcomes[0].interrupted is True
    assert outcomes[0].requeued is False
    assert store.get_task("task-1").state == "INTERRUPTED"
    assert scheduler.inflight_count == 0
    assert scheduler.queued_count == 0


def test_lost_idle_worker_does_not_mutate_task_state(tmp_path: Path) -> None:
    clock = FakeClock()
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    store.create_job("job-1")
    scheduler = BoundedFairScheduler(max_inflight_tasks=1, max_queued_tasks=2)
    workers = WorkerManager(clock=clock)
    handle = FakeHandle(pid=9002)
    workers.register("worker-1", handle)
    workers.mark_ready("worker-1")
    handle.alive = False
    watchdog = WorkerLossCoordinator(
        workers=workers,
        jobs=store,
        leases=TaskLeaseRegistry(clock=clock),
        scheduler=scheduler,
    )

    outcomes = watchdog.reconcile_lost(heartbeat_timeout_seconds=60)

    assert len(outcomes) == 1
    assert outcomes[0].task_id is None
    assert outcomes[0].interrupted is False
    assert outcomes[0].requeued is False
