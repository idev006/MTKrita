from __future__ import annotations

from dataclasses import dataclass

from .event_bus import InProcessEventBus
from .job_store import JobStore
from .path_manager import PathManager
from .resource_broker import ResourceBroker


@dataclass(frozen=True)
class MainBoard:
    """Control-plane composition root; contains no sticker business algorithms."""

    paths: PathManager
    resources: ResourceBroker
    jobs: JobStore
    events: InProcessEventBus

    @classmethod
    def compose(
        cls,
        *,
        paths: PathManager,
        jobs: JobStore,
        events: InProcessEventBus | None = None,
    ) -> MainBoard:
        return cls(
            paths=paths,
            resources=ResourceBroker(paths),
            jobs=jobs,
            events=events or InProcessEventBus(),
        )
