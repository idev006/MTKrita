import json
from pathlib import Path

from mtkrita.event_bus import InProcessEventBus
from mtkrita.log_sink import JsonlLogSink, LogSeverity, StructuredLogRecord
from mtkrita.messages import MessageEnvelope, MessageKind
from mtkrita.path_manager import PathManager


def test_jsonl_log_sink_writes_utf8_structured_record(tmp_path: Path) -> None:
    paths = PathManager(tmp_path / "พื้นที่งาน")
    paths.prepare_job("job-1")
    sink = JsonlLogSink(paths, fsync=False)
    record = StructuredLogRecord(
        timestamp="2026-09-19T00:00:00+00:00",
        severity=LogSeverity.WARNING,
        component="scheduler",
        code="QUEUE.BACKPRESSURE",
        message="คิวเต็มชั่วคราว",
        job_id="job-1",
        correlation_id="corr-1",
        task_id="task-7",
        attempt=2,
        fields={"depth": 8},
    )

    sink.write(record)

    line = paths.log("job-1").path.read_text(encoding="utf-8").splitlines()[0]
    payload = json.loads(line)
    assert payload["severity"] == "WARNING"
    assert payload["message"] == "คิวเต็มชั่วคราว"
    assert payload["task_id"] == "task-7"
    assert payload["attempt"] == 2
    assert payload["fields"] == {"depth": 8}


def test_log_sink_attached_to_event_bus_preserves_correlation_context(tmp_path: Path) -> None:
    paths = PathManager(tmp_path)
    paths.prepare_job("job-1")
    bus = InProcessEventBus()
    sink = JsonlLogSink(paths, fsync=False)
    unsubscribe = sink.attach(bus)
    event = MessageEnvelope.create(
        kind=MessageKind.EVENT,
        message_type="WorkerHeartbeat",
        job_id="job-1",
        correlation_id="corr-heartbeat",
        task_id="task-1",
        worker_id="worker-3",
        attempt=4,
        payload={"healthy": True},
    )

    bus.publish(event)
    unsubscribe()

    payload = json.loads(paths.log("job-1").path.read_text(encoding="utf-8").strip())
    assert payload["code"] == "WorkerHeartbeat"
    assert payload["correlation_id"] == "corr-heartbeat"
    assert payload["worker_id"] == "worker-3"
    assert payload["attempt"] == 4
    assert payload["fields"] == {"healthy": True}


def test_log_sink_keeps_job_logs_isolated(tmp_path: Path) -> None:
    paths = PathManager(tmp_path)
    paths.prepare_job("job-1")
    paths.prepare_job("job-2")
    sink = JsonlLogSink(paths, fsync=False)

    for job_id in ("job-1", "job-2"):
        sink.write(
            sink.create_record(
                severity=LogSeverity.INFO,
                component="test",
                code="TEST.EVENT",
                message=job_id,
                job_id=job_id,
                correlation_id=f"corr-{job_id}",
            )
        )

    assert "job-1" in paths.log("job-1").path.read_text(encoding="utf-8")
    assert "job-2" not in paths.log("job-1").path.read_text(encoding="utf-8")
    assert "job-2" in paths.log("job-2").path.read_text(encoding="utf-8")
