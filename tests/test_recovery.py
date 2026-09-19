from pathlib import Path

from mtkrita.job_lifecycle import JobLifecycleController
from mtkrita.job_store import JobStore
from mtkrita.recovery import StartupReconciler


def _active_job(store: JobStore, job_id: str) -> None:
    store.create_job(job_id)
    store.transition(
        job_id,
        expected_state="CREATED",
        expected_generation=0,
        new_state="READY",
        event_code="JOB.READY",
    )
    JobLifecycleController(store).start_processing(job_id)


def test_startup_recovery_interrupts_orphaned_running_tasks_and_job(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    _active_job(store, "job-1")
    store.create_task("task-1", job_id="job-1")
    store.assign_task(
        "task-1",
        expected_generation=0,
        worker_id="worker-old",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )

    result = StartupReconciler(store).reconcile()

    assert len(result) == 1
    assert result[0].job_id == "job-1"
    assert result[0].prior_state == "PROCESSING"
    assert result[0].interrupted_tasks == ("task-1",)
    assert store.get_task("task-1").state == "INTERRUPTED"
    assert store.get_job("job-1").state == "INTERRUPTED"
    event_codes = [event.event_code for event in store.list_events("job-1")]
    assert "TASK.INTERRUPTED_BY_STARTUP_RECOVERY" in event_codes
    assert "JOB.INTERRUPTED_BY_STARTUP_RECOVERY" in event_codes


def test_startup_recovery_is_idempotent_after_first_reconciliation(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    _active_job(store, "job-1")

    reconciler = StartupReconciler(store)
    first = reconciler.reconcile()
    events_after_first = store.list_events("job-1")
    second = reconciler.reconcile()

    assert len(first) == 1
    assert second == ()
    assert store.list_events("job-1") == events_after_first


def test_startup_recovery_leaves_durable_paused_job_unchanged(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    _active_job(store, "job-1")
    controller = JobLifecycleController(store)
    controller.request_pause("job-1")
    controller.finalize_pause("job-1")
    before = store.get_job("job-1")

    result = StartupReconciler(store).reconcile()

    assert result == ()
    assert store.get_job("job-1") == before
