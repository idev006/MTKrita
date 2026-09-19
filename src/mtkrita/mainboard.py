from __future__ import annotations

from dataclasses import dataclass

from .event_bus import InProcessEventBus
from .job_lifecycle import JobLifecycleController
from .job_store import JobStore
from .path_manager import PathManager
from .recovery import StartupReconciler
from .resource_broker import ResourceBroker
from .task_leases import TaskLeaseRegistry


@dataclass(frozen=True)
class MainBoard:
    """Control-plane composition root; contains no sticker business algorithms."""

    paths: PathManager
    resources: ResourceBroker
    jobs: JobStore
    events: InProcessEventBus
    leases: TaskLeaseRegistry
    lifecycle: JobLifecycleController
    recovery: StartupReconciler

    @classmethod
    def compose(
        cls,
        *,
        paths: PathManager,
        jobs: JobStore,
        events: InProcessEventBus | None = None,
        leases: TaskLeaseRegistry | None = None,
    ) -> MainBoard:
        return cls(
            paths=paths,
            resources=ResourceBroker(paths),
            jobs=jobs,
            events=events or InProcessEventBus(),
            leases=leases or TaskLeaseRegistry(),
            lifecycle=JobLifecycleController(jobs),
            recovery=StartupReconciler(jobs),
        )
