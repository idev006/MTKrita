from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

Clock = Callable[[], datetime]


@dataclass(frozen=True)
class TaskLease:
    task_id: str
    job_id: str
    worker_id: str
    attempt: int
    lease_expires_at: datetime


class TaskLeaseRegistry:
    """MainBoard-owned active-attempt guard; durable persistence is a later phase."""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self._leases: dict[str, TaskLease] = {}

    def assign(
        self,
        *,
        task_id: str,
        job_id: str,
        worker_id: str,
        attempt: int,
        lease_seconds: int,
    ) -> TaskLease:
        if attempt <= 0:
            raise ValueError("attempt must be positive")
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        current = self._leases.get(task_id)
        if current is not None and attempt <= current.attempt:
            raise ValueError("new lease attempt must supersede current attempt")

        lease = TaskLease(
            task_id=task_id,
            job_id=job_id,
            worker_id=worker_id,
            attempt=attempt,
            lease_expires_at=self._clock() + timedelta(seconds=lease_seconds),
        )
        self._leases[task_id] = lease
        return lease

    def renew(
        self,
        *,
        task_id: str,
        worker_id: str,
        attempt: int,
        lease_seconds: int,
    ) -> TaskLease:
        current = self.require_active(task_id, worker_id=worker_id, attempt=attempt)
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        renewed = TaskLease(
            task_id=current.task_id,
            job_id=current.job_id,
            worker_id=current.worker_id,
            attempt=current.attempt,
            lease_expires_at=self._clock() + timedelta(seconds=lease_seconds),
        )
        self._leases[task_id] = renewed
        return renewed

    def require_active(self, task_id: str, *, worker_id: str, attempt: int) -> TaskLease:
        current = self._leases.get(task_id)
        if current is None:
            raise ValueError("task has no active lease")
        if current.worker_id != worker_id or current.attempt != attempt:
            raise ValueError("stale or non-authoritative task attempt")
        if current.lease_expires_at <= self._clock():
            raise ValueError("task lease expired")
        return current

    def release(self, task_id: str, *, worker_id: str, attempt: int) -> TaskLease:
        current = self.require_active(task_id, worker_id=worker_id, attempt=attempt)
        del self._leases[task_id]
        return current

    def discard(self, task_id: str, *, worker_id: str, attempt: int) -> TaskLease | None:
        """Remove the matching runtime lease even when expired during recovery/watchdog cleanup."""
        current = self._leases.get(task_id)
        if current is None:
            return None
        if current.worker_id != worker_id or current.attempt != attempt:
            raise ValueError("stale or non-authoritative task attempt")
        del self._leases[task_id]
        return current

    def expired(self) -> tuple[TaskLease, ...]:
        now = self._clock()
        return tuple(lease for lease in self._leases.values() if lease.lease_expires_at <= now)
