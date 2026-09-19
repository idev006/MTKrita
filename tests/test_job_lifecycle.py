from pathlib import Path

from mtkrita.job_lifecycle import JobLifecycleController
from mtkrita.job_store import JobStore


def _processing_job(tmp_path: Path) -> tuple[JobStore, JobLifecycleController]:
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
    controller = JobLifecycleController(store)
    controller.start_processing("job-1")
    return store, controller


def test_pause_requires_safe_boundary_then_resume(tmp_path: Path) -> None:
    store, controller = _processing_job(tmp_path)
    store.create_task("task-1", job_id="job-1")
    running = store.assign_task(
        "task-1",
        expected_generation=0,
        worker_id="worker-1",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )

    pausing = controller.request_pause("job-1")
    assert pausing.state == "PAUSING"

    try:
        controller.finalize_pause("job-1")
    except RuntimeError as exc:
        assert "RUNNING tasks" in str(exc)
    else:
        raise AssertionError("pause must wait for safe boundary")

    store.finish_task(
        "task-1",
        expected_generation=running.generation,
        worker_id="worker-1",
        attempt=1,
        new_state="INTERRUPTED",
        event_code="TASK.PAUSE_BOUNDARY",
    )
    paused = controller.finalize_pause("job-1")
    assert paused.state == "PAUSED"

    resumed = controller.resume("job-1")
    assert resumed.state == "PROCESSING"


def test_stop_can_supersede_pause_and_requires_no_running_tasks(tmp_path: Path) -> None:
    _, controller = _processing_job(tmp_path)
    controller.request_pause("job-1")
    stopping = controller.request_stop("job-1")
    assert stopping.state == "STOPPING"
    stopped = controller.finalize_stop("job-1")
    assert stopped.state == "STOPPED"


def test_resume_rejects_non_resumable_state(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    store.create_job("job-1")
    controller = JobLifecycleController(store)

    try:
        controller.resume("job-1")
    except RuntimeError as exc:
        assert "cannot transition" in str(exc)
    else:
        raise AssertionError("CREATED job must not resume directly")
