from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from mtkrita.dispatch import DispatchCoordinator
from mtkrita.job_store import JobStore
from mtkrita.scheduler import BoundedFairScheduler, ScheduledTask
from mtkrita.task_leases import TaskLeaseRegistry
from mtkrita.worker_manager import WorkerManager, WorkerState


@dataclass
class FakeHandle:
    pid: int

    def is_alive(self) -> bool:
        return True

    def request_stop(self) -> None:
        pass


class FailingWorkerManager(WorkerManager):
    def assign(self, worker_id: str, *, task_id: str, attempt: int):
        raise RuntimeError("simulated runtime assignment failure")


def _clock() -> datetime:
    return datetime(2026, 9, 19, 6, 30, tzinfo=UTC)


def _store(tmp_path: Path) -> JobStore:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    store.create_job("job-1")
    store.create_task("task-1", job_id="job-1")
    return store


def test_dispatch_assigns_durable_attempt_lease_and_worker_atomically_enough(tmp_path: Path) -> None:
    store = _store(tmp_path)
    scheduler = BoundedFairScheduler(max_inflight_tasks=2, max_queued_tasks=4)
    scheduler.submit(ScheduledTask("task-1", "job-1"))
    workers = WorkerManager(clock=_clock)
    workers.register("worker-1", FakeHandle(pid=1001))
    workers.mark_ready("worker-1")
    leases = TaskLeaseRegistry(clock=_clock)
    coordinator = DispatchCoordinator(
        scheduler=scheduler,
        jobs=store,
        leases=leases,
        workers=workers,
        clock=_clock,
    )

    assignment = coordinator.dispatch_next(worker_id="worker-1", lease_seconds=120)

    assert assignment is not None
    assert assignment.task.task_id == "task-1"
    assert assignment.attempt == 1
    durable = store.get_task("task-1")
    assert durable.state == "RUNNING"
    assert durable.worker_id == "worker-1"
    assert durable.attempt == 1
    assert leases.require_active("task-1", worker_id="worker-1", attempt=1).job_id == "job-1"
    assert workers.get("worker-1").state == WorkerState.BUSY
    assert scheduler.inflight_count == 1


def test_dispatch_failure_compensates_durable_running_state_and_releases_slot(tmp_path: Path) -> None:
    store = _store(tmp_path)
    scheduler = BoundedFairScheduler(max_inflight_tasks=1, max_queued_tasks=2)
    scheduler.submit(ScheduledTask("task-1", "job-1"))
    workers = FailingWorkerManager(clock=_clock)
    workers.register("worker-1", FakeHandle(pid=1002))
    workers.mark_ready("worker-1")
    leases = TaskLeaseRegistry(clock=_clock)
    coordinator = DispatchCoordinator(
        scheduler=scheduler,
        jobs=store,
        leases=leases,
        workers=workers,
        clock=_clock,
    )

    try:
        coordinator.dispatch_next(worker_id="worker-1", lease_seconds=60)
    except RuntimeError as exc:
        assert "simulated" in str(exc)
    else:
        raise AssertionError("expected simulated dispatch failure")

    durable = store.get_task("task-1")
    assert durable.state == "INTERRUPTED"
    assert durable.attempt == 1
    assert scheduler.inflight_count == 0
    try:
        leases.require_active("task-1", worker_id="worker-1", attempt=1)
    except ValueError:
        pass
    else:
        raise AssertionError("runtime lease should be released after compensation")
    event_codes = [event.event_code for event in store.list_events("job-1")]
    assert "TASK.INTERRUPTED_BY_DISPATCH_FAILURE" in event_codes


def test_dispatch_rejects_stale_scheduler_entry_without_mutating_durable_state(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.assign_task(
        "task-1",
        expected_generation=0,
        worker_id="worker-old",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )
    scheduler = BoundedFairScheduler(max_inflight_tasks=1, max_queued_tasks=2)
    scheduler.submit(ScheduledTask("task-1", "job-1"))
    workers = WorkerManager(clock=_clock)
    workers.register("worker-1", FakeHandle(pid=1003))
    workers.mark_ready("worker-1")
    coordinator = DispatchCoordinator(
        scheduler=scheduler,
        jobs=store,
        leases=TaskLeaseRegistry(clock=_clock),
        workers=workers,
        clock=_clock,
    )

    try:
        coordinator.dispatch_next(worker_id="worker-1", lease_seconds=60)
    except RuntimeError as exc:
        assert "durable dispatchable state" in str(exc)
    else:
        raise AssertionError("expected stale scheduler entry rejection")

    durable = store.get_task("task-1")
    assert durable.worker_id == "worker-old"
    assert durable.attempt == 1
    assert durable.state == "RUNNING"
    assert scheduler.inflight_count == 0
