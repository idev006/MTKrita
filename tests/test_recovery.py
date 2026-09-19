from pathlib import Path

from mtkrita.job_lifecycle import JobLifecycleController
from mtkrita.job_store import JobStore
from mtkrita.mainboard import MainBoard
from mtkrita.path_manager import PathManager
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


def test_ordered_startup_recovery_finalizes_promoted_artifact_before_interrupt(tmp_path: Path) -> None:
    paths = PathManager(tmp_path / "workspace")
    paths.prepare_job("job-1")
    paths.prepare_worker_scratch("job-1", "worker-1")
    store = JobStore(paths.evidence("job-1", "jobs.sqlite3").path)
    store.initialize()
    _active_job(store, "job-1")
    store.create_task("task-1", job_id="job-1")
    task = store.assign_task(
        "task-1",
        expected_generation=0,
        worker_id="worker-1",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )
    board = MainBoard.compose(paths=paths, jobs=store)
    source = paths.worker_file("job-1", "worker-1", "candidate.bin")
    target = paths.output("job-1", "01.bin")
    source.path.write_bytes(b"survived-crash")
    candidate = board.resources.validate_worker_file(source)
    board.artifact_journal.create_intent(
        commit_id="commit-1",
        task=task,
        source=source,
        target=target,
        expected_sha256=candidate.sha256,
        byte_size=candidate.byte_size,
    )
    board.resources.commit_worker_file(source, target, expected_sha256=candidate.sha256)
    # Simulate crash after atomic filesystem promotion but before durable finalization.

    report = board.startup_recovery.reconcile()

    assert report.finalized_artifact_commits == ("commit-1",)
    assert board.artifact_journal.get("commit-1").state == "COMMITTED"
    assert store.get_task("task-1").state == "SUCCEEDED"
    assert store.get_job("job-1").state == "INTERRUPTED"
    assert report.reconciled_jobs[0].interrupted_tasks == ()
    assert target.path.read_bytes() == b"survived-crash"
