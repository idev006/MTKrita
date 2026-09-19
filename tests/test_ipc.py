import json

from mtkrita.ipc import JsonMessageCodec, JsonMessageReceiver, JsonMessageSender, WireMessageError
from mtkrita.messages import MESSAGE_SCHEMA_VERSION, MessageEnvelope, MessageKind


class MemoryChannel:
    def __init__(self) -> None:
        self.payload: bytes | None = None

    def send_bytes(self, buf: bytes) -> None:
        self.payload = bytes(buf)

    def recv_bytes(self, maxlength: int | None = None) -> bytes:
        if self.payload is None:
            raise EOFError
        if maxlength is not None and len(self.payload) > maxlength:
            raise OSError("message too large")
        return self.payload


def _message() -> MessageEnvelope:
    return MessageEnvelope.create(
        kind=MessageKind.EVENT,
        message_type="WorkerHeartbeat",
        job_id="job-1",
        correlation_id="corr-1",
        task_id="task-1",
        worker_id="worker-1",
        attempt=2,
        payload={"status": "BUSY", "unicode": "ทดสอบ"},
    )


def test_json_wire_round_trip_preserves_message_contract() -> None:
    codec = JsonMessageCodec()
    original = _message()

    decoded = codec.decode(codec.encode(original), expected_worker_id="worker-1")

    assert decoded == original


def test_sender_receiver_use_byte_channel_not_python_object_pickle() -> None:
    channel = MemoryChannel()
    sender = JsonMessageSender(channel)
    receiver = JsonMessageReceiver(channel)
    original = _message()

    sender.send(original)

    assert channel.payload is not None
    raw = json.loads(channel.payload.decode("utf-8"))
    assert raw["message_type"] == "WorkerHeartbeat"
    assert raw["payload"]["unicode"] == "ทดสอบ"
    assert receiver.receive(expected_worker_id="worker-1") == original


def test_codec_rejects_unsupported_schema_before_message_publish() -> None:
    codec = JsonMessageCodec()
    raw = json.loads(codec.encode(_message()).decode("utf-8"))
    raw["schema_version"] = MESSAGE_SCHEMA_VERSION + 1

    try:
        codec.decode(json.dumps(raw).encode("utf-8"))
    except WireMessageError as exc:
        assert "unsupported message schema" in str(exc)
    else:
        raise AssertionError("expected unsupported schema rejection")


def test_codec_rejects_worker_identity_mismatch() -> None:
    codec = JsonMessageCodec()

    try:
        codec.decode(codec.encode(_message()), expected_worker_id="worker-other")
    except WireMessageError as exc:
        assert "worker identity mismatch" in str(exc)
    else:
        raise AssertionError("expected worker identity rejection")


def test_codec_rejects_malformed_types_and_non_json_payload() -> None:
    codec = JsonMessageCodec()
    raw = json.loads(codec.encode(_message()).decode("utf-8"))
    raw["attempt"] = True
    try:
        codec.decode(json.dumps(raw).encode("utf-8"))
    except WireMessageError as exc:
        assert "attempt" in str(exc)
    else:
        raise AssertionError("expected invalid attempt type rejection")

    invalid = _message()
    invalid.payload["not-json"] = {1, 2, 3}
    try:
        codec.encode(invalid)
    except WireMessageError as exc:
        assert "not valid JSON" in str(exc)
    else:
        raise AssertionError("expected non-JSON payload rejection")


def test_codec_enforces_message_size_limit_on_encode_and_decode() -> None:
    codec = JsonMessageCodec(max_message_bytes=200)
    oversized = MessageEnvelope.create(
        kind=MessageKind.EVENT,
        message_type="TaskFailed",
        job_id="job-1",
        payload={"detail": "x" * 500},
    )
    try:
        codec.encode(oversized)
    except WireMessageError as exc:
        assert "maximum wire size" in str(exc)
    else:
        raise AssertionError("expected oversized encode rejection")

    try:
        codec.decode(b"{" + b"x" * 500 + b"}")
    except WireMessageError as exc:
        assert "maximum wire size" in str(exc)
    else:
        raise AssertionError("expected oversized decode rejection")
