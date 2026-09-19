from __future__ import annotations

from dataclasses import dataclass

from .artifact_commit import (
    ArtifactCommitCoordinator,
    ArtifactCommitJournal,
    ArtifactCommitReconciler,
)
from .event_bus import InProcessEventBus
from .job_lifecycle import JobLifecycleController
from .job_store import JobStore
from .path_manager import PathManager
from .recovery import StartupReconciler, StartupRecoveryCoordinator
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
    artifact_journal: ArtifactCommitJournal
    artifact_commits: ArtifactCommitCoordinator
    artifact_recovery: ArtifactCommitReconciler
    startup_recovery: StartupRecoveryCoordinator

    @classmethod
    def compose(
        cls,
        *,
        paths: PathManager,
        jobs: JobStore,
        events: InProcessEventBus | None = None,
        leases: TaskLeaseRegistry | None = None,
    ) -> MainBoard:
        resources = ResourceBroker(paths)
        artifact_journal = ArtifactCommitJournal(jobs)
        artifact_journal.initialize()
        recovery = StartupReconciler(jobs)
        artifact_recovery = ArtifactCommitReconciler(artifact_journal, resources, jobs)
        return cls(
            paths=paths,
            resources=resources,
            jobs=jobs,
            events=events or InProcessEventBus(),
            leases=leases or TaskLeaseRegistry(),
            lifecycle=JobLifecycleController(jobs),
            recovery=recovery,
            artifact_journal=artifact_journal,
            artifact_commits=ArtifactCommitCoordinator(artifact_journal, resources),
            artifact_recovery=artifact_recovery,
            startup_recovery=StartupRecoveryCoordinator(artifact_recovery, recovery),
        )
