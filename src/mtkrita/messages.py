from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


MESSAGE_SCHEMA_VERSION = 1


class MessageKind(StrEnum):
    COMMAND = "command"
    EVENT = "event"


@dataclass(frozen=True)
class MessageEnvelope:
    message_id: str
    schema_version: int
    kind: MessageKind
    message_type: str
    occurred_at: str
    job_id: str
    correlation_id: str
    causation_id: str | None = None
    frame_id: int | None = None
    stage_id: str | None = None
    task_id: str | None = None
    worker_id: str | None = None
    attempt: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        kind: MessageKind,
        message_type: str,
        job_id: str,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        frame_id: int | None = None,
        stage_id: str | None = None,
        task_id: str | None = None,
        worker_id: str | None = None,
        attempt: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> MessageEnvelope:
        message_id = uuid4().hex
        return cls(
            message_id=message_id,
            schema_version=MESSAGE_SCHEMA_VERSION,
            kind=kind,
            message_type=message_type,
            occurred_at=datetime.now(UTC).isoformat(),
            job_id=job_id,
            correlation_id=correlation_id or message_id,
            causation_id=causation_id,
            frame_id=frame_id,
            stage_id=stage_id,
            task_id=task_id,
            worker_id=worker_id,
            attempt=attempt,
            payload=dict(payload or {}),
        )
