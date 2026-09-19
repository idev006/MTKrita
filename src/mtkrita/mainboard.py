from __future__ import annotations

from dataclasses import dataclass

from .artifact_commit import (
    ArtifactCommitCoordinator,
    ArtifactCommitJournal,
    ArtifactCommitReconciler,
)
from .diagnostics import DiagnosticBundleBuilder
from .event_bus import InProcessEventBus
from .job_lifecycle import JobLifecycleController
from .job_store import JobStore
from .log_sink import JsonlLogSink
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
    logs: JsonlLogSink
    diagnostics: DiagnosticBundleBuilder
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
        logs: JsonlLogSink | None = None,
    ) -> MainBoard:
        resources = ResourceBroker(paths)
        artifact_journal = ArtifactCommitJournal(jobs)
        artifact_journal.initialize()
        recovery = StartupReconciler(jobs)
        artifact_recovery = ArtifactCommitReconciler(artifact_journal, resources, jobs)
        event_bus = events or InProcessEventBus()
        log_sink = logs or JsonlLogSink(paths)
        log_sink.attach(event_bus)
        return cls(
            paths=paths,
            resources=resources,
            jobs=jobs,
            events=event_bus,
            logs=log_sink,
            diagnostics=DiagnosticBundleBuilder(paths, jobs),
            leases=leases or TaskLeaseRegistry(),
            lifecycle=JobLifecycleController(jobs),
            recovery=recovery,
            artifact_journal=artifact_journal,
            artifact_commits=ArtifactCommitCoordinator(artifact_journal, resources),
            artifact_recovery=artifact_recovery,
            startup_recovery=StartupRecoveryCoordinator(artifact_recovery, recovery),
        )
