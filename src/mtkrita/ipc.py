from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Protocol

from .messages import MESSAGE_SCHEMA_VERSION, MessageEnvelope, MessageKind

DEFAULT_MAX_MESSAGE_BYTES = 1024 * 1024


class ByteSender(Protocol):
    def send_bytes(self, buf: bytes) -> None: ...


class ByteReceiver(Protocol):
    def recv_bytes(self, maxlength: int | None = None) -> bytes: ...


class WireMessageError(ValueError):
    """Raised when a process-boundary message violates the explicit wire contract."""


class JsonMessageCodec:
    def __init__(self, *, max_message_bytes: int = DEFAULT_MAX_MESSAGE_BYTES) -> None:
        if max_message_bytes <= 0:
            raise ValueError("max_message_bytes must be positive")
        self._max_message_bytes = max_message_bytes

    @property
    def max_message_bytes(self) -> int:
        return self._max_message_bytes

    def encode(self, message: MessageEnvelope) -> bytes:
        data = asdict(message)
        data["kind"] = message.kind.value
        try:
            wire = json.dumps(
                data,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise WireMessageError("message payload is not valid JSON data") from exc
        if len(wire) > self._max_message_bytes:
            raise WireMessageError("message exceeds maximum wire size")
        return wire

    def decode(
        self,
        wire: bytes,
        *,
        expected_worker_id: str | None = None,
    ) -> MessageEnvelope:
        if len(wire) > self._max_message_bytes:
            raise WireMessageError("message exceeds maximum wire size")
        try:
            data = json.loads(wire.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WireMessageError("malformed UTF-8 JSON message") from exc
        if not isinstance(data, dict):
            raise WireMessageError("wire message must be a JSON object")

        self._require_exact_int(data, "schema_version")
        if data["schema_version"] != MESSAGE_SCHEMA_VERSION:
            raise WireMessageError("unsupported message schema version")
        kind_value = self._require_str(data, "kind")
        try:
            kind = MessageKind(kind_value)
        except ValueError as exc:
            raise WireMessageError("unsupported message kind") from exc

        message_id = self._require_str(data, "message_id")
        message_type = self._require_str(data, "message_type")
        occurred_at = self._require_str(data, "occurred_at")
        job_id = self._require_str(data, "job_id")
        correlation_id = self._require_str(data, "correlation_id")
        payload = data.get("payload")
        if not isinstance(payload, dict):
            raise WireMessageError("payload must be a JSON object")

        worker_id = self._optional_str(data, "worker_id")
        if expected_worker_id is not None and worker_id != expected_worker_id:
            raise WireMessageError("worker identity mismatch")

        return MessageEnvelope(
            message_id=message_id,
            schema_version=data["schema_version"],
            kind=kind,
            message_type=message_type,
            occurred_at=occurred_at,
            job_id=job_id,
            correlation_id=correlation_id,
            causation_id=self._optional_str(data, "causation_id"),
            frame_id=self._optional_int(data, "frame_id"),
            stage_id=self._optional_str(data, "stage_id"),
            task_id=self._optional_str(data, "task_id"),
            worker_id=worker_id,
            attempt=self._optional_int(data, "attempt"),
            payload=payload,
        )

    @staticmethod
    def _require_str(data: dict[str, Any], key: str) -> str:
        value = data.get(key)
        if not isinstance(value, str) or not value:
            raise WireMessageError(f"{key} must be a non-empty string")
        return value

    @staticmethod
    def _require_exact_int(data: dict[str, Any], key: str) -> int:
        value = data.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise WireMessageError(f"{key} must be an integer")
        return value

    @staticmethod
    def _optional_str(data: dict[str, Any], key: str) -> str | None:
        value = data.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            raise WireMessageError(f"{key} must be null or a non-empty string")
        return value

    @staticmethod
    def _optional_int(data: dict[str, Any], key: str) -> int | None:
        value = data.get(key)
        if value is None:
            return None
        if not isinstance(value, int) or isinstance(value, bool):
            raise WireMessageError(f"{key} must be null or an integer")
        return value


class JsonMessageSender:
    def __init__(self, channel: ByteSender, codec: JsonMessageCodec | None = None) -> None:
        self._channel = channel
        self._codec = codec or JsonMessageCodec()

    def send(self, message: MessageEnvelope) -> None:
        self._channel.send_bytes(self._codec.encode(message))


class JsonMessageReceiver:
    def __init__(self, channel: ByteReceiver, codec: JsonMessageCodec | None = None) -> None:
        self._channel = channel
        self._codec = codec or JsonMessageCodec()

    def receive(self, *, expected_worker_id: str | None = None) -> MessageEnvelope:
        try:
            wire = self._channel.recv_bytes(self._codec.max_message_bytes + 1)
        except OSError as exc:
            raise WireMessageError("wire message exceeds maximum size or channel failed") from exc
        return self._codec.decode(wire, expected_worker_id=expected_worker_id)
