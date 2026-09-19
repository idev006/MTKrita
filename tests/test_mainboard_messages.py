from pathlib import Path

from mtkrita.event_bus import InProcessEventBus
from mtkrita.job_store import JobStore
from mtkrita.mainboard import MainBoard
from mtkrita.messages import MESSAGE_SCHEMA_VERSION, MessageEnvelope, MessageKind
from mtkrita.path_manager import PathManager


def test_message_envelope_carries_correlation_and_attempt() -> None:
    message = MessageEnvelope.create(
        kind=MessageKind.EVENT,
        message_type="TaskSucceeded",
        job_id="job-1",
        frame_id=7,
        task_id="task-7",
        worker_id="worker-2",
        attempt=3,
        payload={"status": "PASS"},
    )
    assert message.schema_version == MESSAGE_SCHEMA_VERSION
    assert message.correlation_id == message.message_id
    assert message.attempt == 3
    assert message.payload["status"] == "PASS"


def test_event_bus_routes_typed_and_global_subscribers() -> None:
    bus = InProcessEventBus()
    typed: list[str] = []
    all_events: list[str] = []
    unsubscribe_typed = bus.subscribe("TaskSucceeded", lambda event: typed.append(event.message_id))
    bus.subscribe_all(lambda event: all_events.append(event.message_type))

    event = MessageEnvelope.create(
        kind=MessageKind.EVENT,
        message_type="TaskSucceeded",
        job_id="job-1",
    )
    bus.publish(event)
    unsubscribe_typed()
    bus.publish(event)

    assert typed == [event.message_id]
    assert all_events == ["TaskSucceeded", "TaskSucceeded"]


def test_mainboard_composes_services_without_business_logic(tmp_path: Path) -> None:
    paths = PathManager(tmp_path / "workspace")
    paths.prepare_job("job-1")
    store_path = paths.evidence("job-1", "jobs.sqlite3").path
    store = JobStore(store_path)
    store.initialize()
    bus = InProcessEventBus()

    board = MainBoard.compose(paths=paths, jobs=store, events=bus)

    assert board.paths is paths
    assert board.jobs is store
    assert board.events is bus
    assert board.resources is not None
    assert board.leases is not None
    assert board.lifecycle.jobs is store
    assert board.recovery.jobs is store
    assert board.artifact_journal is not None
    assert board.artifact_commits.journal is board.artifact_journal
    assert board.artifact_commits.broker is board.resources
    assert board.artifact_recovery.journal is board.artifact_journal
    assert board.artifact_recovery.broker is board.resources
    assert board.artifact_recovery.jobs is store
