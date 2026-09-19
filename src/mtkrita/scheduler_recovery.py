from __future__ import annotations

from dataclasses import dataclass

from .job_store import JobStore
from .scheduler import BoundedFairScheduler, ScheduledTask, TaskPriority

SUPPORTED_DESCRIPTOR_VERSION = 1


@dataclass(frozen=True)
class SchedulerRebuildResult:
    enqueued_task_ids: tuple[str, ...]
    deferred_task_ids: tuple[str, ...]


class SchedulerReconstructor:
    """Rebuild disposable scheduler state from durable JobStore task descriptors."""

    def __init__(self, jobs: JobStore) -> None:
        self._jobs = jobs

    def rebuild_jobs(
        self,
        scheduler: BoundedFairScheduler,
        job_ids: tuple[str, ...],
    ) -> SchedulerRebuildResult:
        candidates = []
        for job_id in sorted(set(job_ids)):
            candidates.extend(self._jobs.list_reconstructable_tasks(job_id))

        prepared: list[ScheduledTask] = []
        for task, descriptor in candidates:
            if descriptor.descriptor_version != SUPPORTED_DESCRIPTOR_VERSION:
                raise RuntimeError(
                    f"unsupported task descriptor version for {task.task_id}: "
                    f"{descriptor.descriptor_version}"
                )
            try:
                priority = TaskPriority(descriptor.priority)
            except ValueError as exc:
                raise RuntimeError(
                    f"unsupported scheduler priority for {task.task_id}: {descriptor.priority}"
                ) from exc
            prepared.append(
                ScheduledTask(
                    task_id=task.task_id,
                    job_id=task.job_id,
                    priority=priority,
                )
            )

        enqueued: list[str] = []
        deferred: list[str] = []
        for task in prepared:
            if scheduler.submit(task):
                enqueued.append(task.task_id)
            else:
                deferred.append(task.task_id)

        return SchedulerRebuildResult(
            enqueued_task_ids=tuple(enqueued),
            deferred_task_ids=tuple(deferred),
        )
