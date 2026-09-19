from __future__ import annotations

from dataclasses import dataclass

from .job_store import JobStore
from .scheduler import BoundedFairScheduler, ScheduledTask
from .task_leases import TaskLeaseRegistry
from .worker_manager import WorkerManager


@dataclass(frozen=True)
class WorkerLossOutcome:
    worker_id: str
    task_id: str | None
    interrupted: bool
    requeued: bool


class WorkerLossCoordinator:
    """Reconcile LOST workers with durable task state and scheduler capacity."""

    def __init__(
        self,
        *,
        workers: WorkerManager,
        jobs: JobStore,
        leases: TaskLeaseRegistry,
        scheduler: BoundedFairScheduler,
    ) -> None:
        self._workers = workers
        self._jobs = jobs
        self._leases = leases
        self._scheduler = scheduler

    def reconcile_lost(
        self,
        *,
        heartbeat_timeout_seconds: float,
        requeue: bool = True,
    ) -> tuple[WorkerLossOutcome, ...]:
        outcomes: list[WorkerLossOutcome] = []
        for worker in self._workers.detect_lost(
            heartbeat_timeout_seconds=heartbeat_timeout_seconds
        ):
            task_id = worker.active_task_id
            attempt = worker.active_attempt
            if task_id is None or attempt is None:
                outcomes.append(
                    WorkerLossOutcome(
                        worker_id=worker.worker_id,
                        task_id=None,
                        interrupted=False,
                        requeued=False,
                    )
                )
                continue

            durable = self._jobs.get_task(task_id)
            authoritative = (
                durable.state == "RUNNING"
                and durable.worker_id == worker.worker_id
                and durable.attempt == attempt
            )
            interrupted = False
            if authoritative:
                self._jobs.finish_task(
                    task_id,
                    expected_generation=durable.generation,
                    worker_id=worker.worker_id,
                    attempt=attempt,
                    new_state="INTERRUPTED",
                    event_code="TASK.INTERRUPTED_BY_WORKER_LOSS",
                )
                interrupted = True

            try:
                self._leases.discard(
                    task_id,
                    worker_id=worker.worker_id,
                    attempt=attempt,
                )
            except ValueError:
                pass

            scheduled: ScheduledTask | None = None
            try:
                scheduled = self._scheduler.complete(task_id)
            except KeyError:
                scheduled = None

            requeued = False
            if interrupted and requeue and scheduled is not None:
                requeued = self._scheduler.submit(scheduled)

            outcomes.append(
                WorkerLossOutcome(
                    worker_id=worker.worker_id,
                    task_id=task_id,
                    interrupted=interrupted,
                    requeued=requeued,
                )
            )
        return tuple(outcomes)
