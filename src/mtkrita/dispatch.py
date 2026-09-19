from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .job_store import JobStore, TaskRecord
from .scheduler import BoundedFairScheduler, ScheduledTask
from .task_leases import TaskLeaseRegistry
from .worker_manager import WorkerManager, WorkerState

Clock = Callable[[], datetime]


@dataclass(frozen=True)
class DispatchAssignment:
    task: ScheduledTask
    worker_id: str
    attempt: int
    task_generation: int
    lease_expires_at: datetime


class DispatchCoordinator:
    """Bridge in-memory dispatch policy to durable task authority and runtime worker guards."""

    def __init__(
        self,
        *,
        scheduler: BoundedFairScheduler,
        jobs: JobStore,
        leases: TaskLeaseRegistry,
        workers: WorkerManager,
        clock: Clock | None = None,
    ) -> None:
        self._scheduler = scheduler
        self._jobs = jobs
        self._leases = leases
        self._workers = workers
        self._clock = clock or (lambda: datetime.now(UTC))

    def dispatch_next(self, *, worker_id: str, lease_seconds: int) -> DispatchAssignment | None:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        worker = self._workers.get(worker_id)
        if worker.state != WorkerState.READY:
            raise RuntimeError("worker must be READY before dispatch")

        scheduled = self._scheduler.dispatch_next()
        if scheduled is None:
            return None

        durable = self._jobs.get_task(scheduled.task_id)
        if durable.job_id != scheduled.job_id or durable.state not in {"PENDING", "INTERRUPTED"}:
            self._scheduler.complete(scheduled.task_id)
            raise RuntimeError("scheduled task does not match durable dispatchable state")

        attempt = durable.attempt + 1
        lease_expires_at = self._clock() + timedelta(seconds=lease_seconds)
        assigned: TaskRecord | None = None
        runtime_lease_assigned = False
        try:
            assigned = self._jobs.assign_task(
                scheduled.task_id,
                expected_generation=durable.generation,
                worker_id=worker_id,
                attempt=attempt,
                lease_expires_at=lease_expires_at.isoformat(),
            )
            self._leases.assign(
                task_id=scheduled.task_id,
                job_id=scheduled.job_id,
                worker_id=worker_id,
                attempt=attempt,
                lease_seconds=lease_seconds,
            )
            runtime_lease_assigned = True
            self._workers.assign(worker_id, task_id=scheduled.task_id, attempt=attempt)
        except Exception:
            if runtime_lease_assigned:
                try:
                    self._leases.release(
                        scheduled.task_id,
                        worker_id=worker_id,
                        attempt=attempt,
                    )
                except (ValueError, KeyError):
                    pass
            if assigned is not None:
                current = self._jobs.get_task(scheduled.task_id)
                if (
                    current.state == "RUNNING"
                    and current.worker_id == worker_id
                    and current.attempt == attempt
                ):
                    self._jobs.finish_task(
                        scheduled.task_id,
                        expected_generation=current.generation,
                        worker_id=worker_id,
                        attempt=attempt,
                        new_state="INTERRUPTED",
                        event_code="TASK.INTERRUPTED_BY_DISPATCH_FAILURE",
                    )
            self._scheduler.complete(scheduled.task_id)
            raise

        return DispatchAssignment(
            task=scheduled,
            worker_id=worker_id,
            attempt=attempt,
            task_generation=assigned.generation,
            lease_expires_at=lease_expires_at,
        )
