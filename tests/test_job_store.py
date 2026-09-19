from pathlib import Path

from mtkrita.job_store import JobStore


def test_job_store_persists_job_and_event_history(tmp_path: Path) -> None:
    store_path = tmp_path / "jobs.sqlite3"
    store = JobStore(store_path)
    store.initialize()

    created = store.create_job("job-1", source_hash="src", config_hash="cfg")
    assert created.state == "CREATED"
    assert created.generation == 0

    ready = store.transition(
        "job-1",
        expected_state="CREATED",
        expected_generation=0,
        new_state="READY",
        event_code="JOB.READY",
        detail={"reason": "source_valid"},
    )
    assert ready.state == "READY"
    assert ready.generation == 1

    reopened = JobStore(store_path)
    reopened.initialize()
    persisted = reopened.get_job("job-1")
    assert persisted == ready
    events = reopened.list_events("job-1")
    assert [event.event_code for event in events] == ["JOB.CREATED", "JOB.READY"]
    assert events[-1].detail == {"reason": "source_valid"}


def test_job_store_rejects_stale_transition_atomically(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    store.create_job("job-1")
    store.transition(
        "job-1",
        expected_state="CREATED",
        expected_generation=0,
        new_state="READY",
        event_code="JOB.READY",
    )

    try:
        store.transition(
            "job-1",
            expected_state="CREATED",
            expected_generation=0,
            new_state="FAILED",
            event_code="JOB.FAILED",
        )
    except RuntimeError as exc:
        assert "stale or invalid" in str(exc)
    else:
        raise AssertionError("expected stale transition rejection")

    current = store.get_job("job-1")
    assert current.state == "READY"
    assert current.generation == 1
    assert len(store.list_events("job-1")) == 2


def test_job_store_requires_prepared_parent(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "missing" / "jobs.sqlite3")
    try:
        store.initialize()
    except ValueError as exc:
        assert "parent directory" in str(exc)
    else:
        raise AssertionError("expected unprepared parent rejection")
