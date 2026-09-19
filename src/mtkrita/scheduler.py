from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum


class TaskPriority(IntEnum):
    CRITICAL = 0
    HIGH = 10
    NORMAL = 20
    LOW = 30


@dataclass(frozen=True)
class ScheduledTask:
    task_id: str
    job_id: str
    priority: TaskPriority = TaskPriority.NORMAL


JobDispatchable = Callable[[str], bool]


class BoundedFairScheduler:
    """In-memory admission/dispatch policy; durable task authority remains in JobStore."""

    def __init__(
        self,
        *,
        max_inflight_tasks: int,
        max_queued_tasks: int,
        job_dispatchable: JobDispatchable | None = None,
        priority_burst_limit: int = 4,
    ) -> None:
        if max_inflight_tasks <= 0:
            raise ValueError("max_inflight_tasks must be positive")
        if max_queued_tasks <= 0:
            raise ValueError("max_queued_tasks must be positive")
        if priority_burst_limit <= 0:
            raise ValueError("priority_burst_limit must be positive")
        self._max_inflight = max_inflight_tasks
        self._max_queued = max_queued_tasks
        self._job_dispatchable = job_dispatchable or (lambda _job_id: True)
        self._priority_burst_limit = priority_burst_limit
        self._queues: dict[TaskPriority, dict[str, deque[ScheduledTask]]] = defaultdict(dict)
        self._job_rotations: dict[TaskPriority, deque[str]] = defaultdict(deque)
        self._queued_ids: set[str] = set()
        self._inflight: dict[str, ScheduledTask] = {}
        self._last_priority: TaskPriority | None = None
        self._priority_burst = 0

    @property
    def queued_count(self) -> int:
        return len(self._queued_ids)

    @property
    def inflight_count(self) -> int:
        return len(self._inflight)

    @property
    def has_capacity(self) -> bool:
        return self.inflight_count < self._max_inflight

    def submit(self, task: ScheduledTask) -> bool:
        if task.task_id in self._queued_ids or task.task_id in self._inflight:
            raise ValueError("duplicate task_id")
        if self.queued_count >= self._max_queued:
            return False
        jobs = self._queues[task.priority]
        queue = jobs.get(task.job_id)
        if queue is None:
            queue = deque()
            jobs[task.job_id] = queue
            self._job_rotations[task.priority].append(task.job_id)
        queue.append(task)
        self._queued_ids.add(task.task_id)
        return True

    def dispatch_next(self) -> ScheduledTask | None:
        if not self.has_capacity or not self._queued_ids:
            return None
        priority = self._choose_priority()
        if priority is None:
            return None
        task = self._pop_fair(priority)
        if task is None:
            return None
        self._queued_ids.remove(task.task_id)
        self._inflight[task.task_id] = task
        if self._last_priority == priority:
            self._priority_burst += 1
        else:
            self._last_priority = priority
            self._priority_burst = 1
        return task

    def complete(self, task_id: str) -> ScheduledTask:
        try:
            return self._inflight.pop(task_id)
        except KeyError as exc:
            raise KeyError(f"task is not inflight: {task_id}") from exc

    def _choose_priority(self) -> TaskPriority | None:
        available = [priority for priority in sorted(self._queues) if self._has_dispatchable(priority)]
        if not available:
            return None
        preferred = available[0]
        if (
            self._last_priority == preferred
            and self._priority_burst >= self._priority_burst_limit
            and len(available) > 1
        ):
            return available[1]
        return preferred

    def _has_dispatchable(self, priority: TaskPriority) -> bool:
        return any(
            queue and self._job_dispatchable(job_id)
            for job_id, queue in self._queues[priority].items()
        )

    def _pop_fair(self, priority: TaskPriority) -> ScheduledTask | None:
        rotation = self._job_rotations[priority]
        jobs = self._queues[priority]
        attempts = len(rotation)
        for _ in range(attempts):
            job_id = rotation.popleft()
            queue = jobs.get(job_id)
            if not queue:
                jobs.pop(job_id, None)
                continue
            rotation.append(job_id)
            if not self._job_dispatchable(job_id):
                continue
            task = queue.popleft()
            if not queue:
                jobs.pop(job_id, None)
                rotation.remove(job_id)
            return task
        return None
