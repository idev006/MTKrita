import sqlite3
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


def test_job_store_migrates_v1_to_v3_without_losing_jobs(tmp_path: Path) -> None:
    path = tmp_path / "jobs.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT INTO metadata(key, value) VALUES('schema_version', '1');
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            generation INTEGER NOT NULL,
            source_hash TEXT,
            config_hash TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            event_code TEXT NOT NULL,
            from_state TEXT,
            to_state TEXT,
            generation INTEGER NOT NULL,
            occurred_at TEXT NOT NULL,
            detail_json TEXT NOT NULL
        );
        INSERT INTO jobs VALUES('job-legacy', 'READY', 2, 'src', 'cfg', 't0', 't1');
        """
    )
    connection.commit()
    connection.close()

    store = JobStore(path)
    store.initialize()

    assert store.get_job("job-legacy").state == "READY"
    migrated = sqlite3.connect(path)
    version = migrated.execute(
        "SELECT value FROM metadata WHERE key = 'schema_version'"
    ).fetchone()
    task_table = migrated.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
    ).fetchone()
    descriptor_table = migrated.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'task_descriptors'"
    ).fetchone()
    migrated.close()
    assert version == ("3",)
    assert task_table == ("tasks",)
    assert descriptor_table == ("task_descriptors",)


def test_v2_task_migration_is_explicitly_not_reconstructable(tmp_path: Path) -> None:
    path = tmp_path / "jobs.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT INTO metadata(key, value) VALUES('schema_version', '2');
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            generation INTEGER NOT NULL,
            source_hash TEXT,
            config_hash TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            event_code TEXT NOT NULL,
            from_state TEXT,
            to_state TEXT,
            generation INTEGER NOT NULL,
            occurred_at TEXT NOT NULL,
            detail_json TEXT NOT NULL
        );
        CREATE TABLE tasks (
            task_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            state TEXT NOT NULL,
            generation INTEGER NOT NULL,
            attempt INTEGER NOT NULL,
            worker_id TEXT,
            lease_expires_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO jobs VALUES('job-1', 'READY', 0, NULL, NULL, 't0', 't0');
        INSERT INTO tasks VALUES('legacy-task', 'job-1', 'PENDING', 0, 0, NULL, NULL, 't0', 't0');
        """
    )
    connection.commit()
    connection.close()

    store = JobStore(path)
    store.initialize()

    descriptor = store.get_task_descriptor("legacy-task")
    assert descriptor.priority == 20
    assert descriptor.descriptor_version == 0
    assert descriptor.descriptor == {}
    assert descriptor.reconstructable is False
    assert store.list_reconstructable_tasks("job-1") == ()


def test_new_task_descriptor_priority_and_payload_persist_across_reopen(tmp_path: Path) -> None:
    path = tmp_path / "jobs.sqlite3"
    store = JobStore(path)
    store.initialize()
    store.create_job("job-1")
    store.create_task(
        "task-01",
        job_id="job-1",
        priority=10,
        descriptor={"frame_id": 1, "stage_plan": "frame-v1"},
        descriptor_version=1,
    )

    reopened = JobStore(path)
    reopened.initialize()
    descriptor = reopened.get_task_descriptor("task-01")
    assert descriptor.priority == 10
    assert descriptor.descriptor_version == 1
    assert descriptor.descriptor == {"frame_id": 1, "stage_plan": "frame-v1"}
    assert descriptor.reconstructable is True
    reconstructable = reopened.list_reconstructable_tasks("job-1")
    assert len(reconstructable) == 1
    assert reconstructable[0][0].task_id == "task-01"
    assert reconstructable[0][1] == descriptor


def test_task_without_descriptor_remains_non_reconstructable(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    store.create_job("job-1")
    store.create_task("task-01", job_id="job-1")

    descriptor = store.get_task_descriptor("task-01")
    assert descriptor.reconstructable is False
    assert store.list_reconstructable_tasks("job-1") == ()


def test_task_attempt_and_lease_state_persist_across_reopen(tmp_path: Path) -> None:
    path = tmp_path / "jobs.sqlite3"
    store = JobStore(path)
    store.initialize()
    store.create_job("job-1")
    created = store.create_task("task-01", job_id="job-1")
    assert created.state == "PENDING"
    assert created.attempt == 0

    assigned = store.assign_task(
        "task-01",
        expected_generation=0,
        worker_id="worker-1",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )
    assert assigned.state == "RUNNING"
    assert assigned.attempt == 1
    assert assigned.generation == 1

    reopened = JobStore(path)
    reopened.initialize()
    persisted = reopened.get_task("task-01")
    assert persisted == assigned
    assert reopened.list_tasks("job-1", state="RUNNING") == (assigned,)


def test_task_store_rejects_stale_attempt_and_worker_completion(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    store.create_job("job-1")
    store.create_task("task-01", job_id="job-1")
    running = store.assign_task(
        "task-01",
        expected_generation=0,
        worker_id="worker-new",
        attempt=2,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )

    try:
        store.finish_task(
            "task-01",
            expected_generation=running.generation,
            worker_id="worker-old",
            attempt=1,
            new_state="SUCCEEDED",
            event_code="TASK.SUCCEEDED",
        )
    except RuntimeError as exc:
        assert "stale or invalid" in str(exc)
    else:
        raise AssertionError("expected stale completion rejection")

    current = store.get_task("task-01")
    assert current.state == "RUNNING"
    assert current.worker_id == "worker-new"
    assert current.attempt == 2


def test_task_lease_renewal_requires_authoritative_attempt(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    store.create_job("job-1")
    store.create_task("task-01", job_id="job-1")
    running = store.assign_task(
        "task-01",
        expected_generation=0,
        worker_id="worker-1",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )

    renewed = store.renew_task_lease(
        "task-01",
        expected_generation=running.generation,
        worker_id="worker-1",
        attempt=1,
        lease_expires_at="2030-01-01T00:02:00+00:00",
    )
    assert renewed.generation == 2
    assert renewed.lease_expires_at == "2030-01-01T00:02:00+00:00"

    try:
        store.renew_task_lease(
            "task-01",
            expected_generation=renewed.generation,
            worker_id="worker-1",
            attempt=0,
            lease_expires_at="2030-01-01T00:03:00+00:00",
        )
    except RuntimeError as exc:
        assert "stale or invalid" in str(exc)
    else:
        raise AssertionError("expected stale lease renewal rejection")
