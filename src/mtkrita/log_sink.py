from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from .event_bus import InProcessEventBus
from .messages import MessageEnvelope
from .path_manager import PathManager


class LogSeverity(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class StructuredLogRecord:
    timestamp: str
    severity: LogSeverity
    component: str
    code: str
    message: str
    job_id: str
    correlation_id: str
    frame_id: int | None = None
    stage_id: str | None = None
    task_id: str | None = None
    worker_id: str | None = None
    attempt: int | None = None
    provider: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_message(
        cls,
        event: MessageEnvelope,
        *,
        severity: LogSeverity = LogSeverity.INFO,
        component: str = "event_bus",
    ) -> StructuredLogRecord:
        return cls(
            timestamp=event.occurred_at,
            severity=severity,
            component=component,
            code=event.message_type,
            message=event.message_type,
            job_id=event.job_id,
            correlation_id=event.correlation_id,
            frame_id=event.frame_id,
            stage_id=event.stage_id,
            task_id=event.task_id,
            worker_id=event.worker_id,
            attempt=event.attempt,
            fields=dict(event.payload),
        )


class JsonlLogSink:
    """Single control-plane writer for per-job structured JSONL operational logs."""

    def __init__(self, paths: PathManager, *, fsync: bool = True) -> None:
        self._paths = paths
        self._fsync = fsync

    def attach(self, bus: InProcessEventBus):
        return bus.subscribe_all(self.write_message)

    def write_message(self, event: MessageEnvelope) -> None:
        self.write(StructuredLogRecord.from_message(event))

    def write(self, record: StructuredLogRecord) -> None:
        target = self._paths.log(record.job_id).path
        self._paths.assert_owned(target)
        if not target.parent.is_dir():
            raise ValueError("job log directory is not prepared")
        payload = json.dumps(
            asdict(record),
            ensure_ascii=False,
            sort_keys=True,
            default=str,
            separators=(",", ":"),
        )
        with target.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(payload + "\n")
            handle.flush()
            if self._fsync:
                os.fsync(handle.fileno())

    @staticmethod
    def create_record(
        *,
        severity: LogSeverity,
        component: str,
        code: str,
        message: str,
        job_id: str,
        correlation_id: str,
        **fields: Any,
    ) -> StructuredLogRecord:
        return StructuredLogRecord(
            timestamp=datetime.now(UTC).isoformat(),
            severity=severity,
            component=component,
            code=code,
            message=message,
            job_id=job_id,
            correlation_id=correlation_id,
            fields=fields,
        )
