from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol


class WorkerState(StrEnum):
    STARTING = "STARTING"
    READY = "READY"
    BUSY = "BUSY"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    LOST = "LOST"


class WorkerHandle(Protocol):
    @property
    def pid(self) -> int: ...

    def is_alive(self) -> bool: ...

    def request_stop(self) -> None: ...


Clock = Callable[[], datetime]


@dataclass(frozen=True)
class WorkerRecord:
    worker_id: str
    pid: int
    state: WorkerState
    last_heartbeat_at: datetime
    active_task_id: str | None = None
    active_attempt: int | None = None


class WorkerManager:
    """Track worker lifecycle/heartbeats behind replaceable process handles."""

    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self._handles: dict[str, WorkerHandle] = {}
        self._records: dict[str, WorkerRecord] = {}

    def register(self, worker_id: str, handle: WorkerHandle) -> WorkerRecord:
        if not worker_id:
            raise ValueError("worker_id is required")
        if worker_id in self._records:
            raise ValueError("worker already registered")
        record = WorkerRecord(
            worker_id=worker_id,
            pid=handle.pid,
            state=WorkerState.STARTING,
            last_heartbeat_at=self._clock(),
        )
        self._handles[worker_id] = handle
        self._records[worker_id] = record
        return record

    def get(self, worker_id: str) -> WorkerRecord:
        try:
            return self._records[worker_id]
        except KeyError as exc:
            raise KeyError(f"unknown worker: {worker_id}") from exc

    def mark_ready(self, worker_id: str) -> WorkerRecord:
        current = self.get(worker_id)
        if current.state not in {WorkerState.STARTING, WorkerState.READY}:
            raise RuntimeError("worker cannot become READY from current state")
        return self._replace(
            current,
            state=WorkerState.READY,
            last_heartbeat_at=self._clock(),
            active_task_id=None,
            active_attempt=None,
        )

    def heartbeat(self, worker_id: str) -> WorkerRecord:
        current = self.get(worker_id)
        if current.state in {WorkerState.STOPPED, WorkerState.LOST}:
            raise RuntimeError("terminal worker cannot heartbeat")
        return self._replace(current, last_heartbeat_at=self._clock())

    def assign(self, worker_id: str, *, task_id: str, attempt: int) -> WorkerRecord:
        if attempt <= 0:
            raise ValueError("attempt must be positive")
        current = self.get(worker_id)
        if current.state != WorkerState.READY:
            raise RuntimeError("worker must be READY before task assignment")
        return self._replace(
            current,
            state=WorkerState.BUSY,
            active_task_id=task_id,
            active_attempt=attempt,
        )

    def release_task(self, worker_id: str, *, task_id: str, attempt: int) -> WorkerRecord:
        current = self.get(worker_id)
        if (
            current.state != WorkerState.BUSY
            or current.active_task_id != task_id
            or current.active_attempt != attempt
        ):
            raise RuntimeError("worker task ownership mismatch")
        return self._replace(
            current,
            state=WorkerState.READY,
            active_task_id=None,
            active_attempt=None,
            last_heartbeat_at=self._clock(),
        )

    def request_stop(self, worker_id: str) -> WorkerRecord:
        current = self.get(worker_id)
        if current.state in {WorkerState.STOPPED, WorkerState.LOST}:
            return current
        self._handles[worker_id].request_stop()
        return self._replace(current, state=WorkerState.STOPPING)

    def refresh_process_state(self, worker_id: str) -> WorkerRecord:
        current = self.get(worker_id)
        if current.state in {WorkerState.STOPPED, WorkerState.LOST}:
            return current
        if self._handles[worker_id].is_alive():
            return current
        terminal = WorkerState.STOPPED if current.state == WorkerState.STOPPING else WorkerState.LOST
        return self._replace(current, state=terminal)

    def detect_lost(self, *, heartbeat_timeout_seconds: float) -> tuple[WorkerRecord, ...]:
        if heartbeat_timeout_seconds <= 0:
            raise ValueError("heartbeat_timeout_seconds must be positive")
        now = self._clock()
        lost: list[WorkerRecord] = []
        for worker_id, current in tuple(self._records.items()):
            if current.state in {WorkerState.STOPPED, WorkerState.LOST, WorkerState.STOPPING}:
                continue
            age = (now - current.last_heartbeat_at).total_seconds()
            if not self._handles[worker_id].is_alive() or age > heartbeat_timeout_seconds:
                updated = self._replace(current, state=WorkerState.LOST)
                lost.append(updated)
        return tuple(lost)

    def list_workers(self) -> tuple[WorkerRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def _replace(self, current: WorkerRecord, **changes: object) -> WorkerRecord:
        updated = replace(current, **changes)
        self._records[current.worker_id] = updated
        return updated
