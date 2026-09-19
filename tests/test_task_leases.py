from datetime import UTC, datetime, timedelta

from mtkrita.task_leases import TaskLeaseRegistry


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 19, 5, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


def test_newer_attempt_invalidates_old_worker_result() -> None:
    clock = FakeClock()
    registry = TaskLeaseRegistry(clock)
    registry.assign(task_id="task-1", job_id="job-1", worker_id="worker-1", attempt=1, lease_seconds=30)
    registry.assign(task_id="task-1", job_id="job-1", worker_id="worker-2", attempt=2, lease_seconds=30)

    try:
        registry.require_active("task-1", worker_id="worker-1", attempt=1)
    except ValueError as exc:
        assert "stale" in str(exc)
    else:
        raise AssertionError("expected stale attempt rejection")

    active = registry.require_active("task-1", worker_id="worker-2", attempt=2)
    assert active.attempt == 2


def test_expired_lease_rejects_result_and_is_reported() -> None:
    clock = FakeClock()
    registry = TaskLeaseRegistry(clock)
    lease = registry.assign(
        task_id="task-1",
        job_id="job-1",
        worker_id="worker-1",
        attempt=1,
        lease_seconds=10,
    )
    clock.advance(11)

    assert registry.expired() == (lease,)
    try:
        registry.require_active("task-1", worker_id="worker-1", attempt=1)
    except ValueError as exc:
        assert "expired" in str(exc)
    else:
        raise AssertionError("expected expired lease rejection")


def test_renew_and_release_require_authoritative_attempt() -> None:
    clock = FakeClock()
    registry = TaskLeaseRegistry(clock)
    first = registry.assign(
        task_id="task-1",
        job_id="job-1",
        worker_id="worker-1",
        attempt=1,
        lease_seconds=10,
    )
    clock.advance(5)
    renewed = registry.renew(
        task_id="task-1",
        worker_id="worker-1",
        attempt=1,
        lease_seconds=20,
    )
    assert renewed.lease_expires_at > first.lease_expires_at

    released = registry.release("task-1", worker_id="worker-1", attempt=1)
    assert released.attempt == 1
    try:
        registry.require_active("task-1", worker_id="worker-1", attempt=1)
    except ValueError as exc:
        assert "no active lease" in str(exc)
    else:
        raise AssertionError("expected released lease to be inactive")
