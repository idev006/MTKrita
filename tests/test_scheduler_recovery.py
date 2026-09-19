from pathlib import Path

from mtkrita.job_store import JobStore
from mtkrita.scheduler import BoundedFairScheduler, TaskPriority
from mtkrita.scheduler_recovery import SchedulerReconstructor


def _store(tmp_path: Path) -> JobStore:
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.initialize()
    store.create_job("job-a")
    store.create_job("job-b")
    return store


def test_reconstructor_restores_priority_and_eligible_task_state(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.create_task(
        "a-high",
        job_id="job-a",
        priority=int(TaskPriority.HIGH),
        descriptor={"frame_id": 1, "stage_plan": "frame-v1"},
    )
    store.create_task(
        "a-normal",
        job_id="job-a",
        priority=int(TaskPriority.NORMAL),
        descriptor={"frame_id": 2, "stage_plan": "frame-v1"},
    )
    interrupted = store.create_task(
        "b-low",
        job_id="job-b",
        priority=int(TaskPriority.LOW),
        descriptor={"frame_id": 3, "stage_plan": "frame-v1"},
    )
    running = store.assign_task(
        interrupted.task_id,
        expected_generation=0,
        worker_id="worker-old",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )
    store.finish_task(
        interrupted.task_id,
        expected_generation=running.generation,
        worker_id="worker-old",
        attempt=1,
        new_state="INTERRUPTED",
        event_code="TASK.INTERRUPTED_FOR_TEST",
    )

    scheduler = BoundedFairScheduler(max_inflight_tasks=2, max_queued_tasks=8)
    result = SchedulerReconstructor(store).rebuild_jobs(scheduler, ("job-b", "job-a"))

    assert result.enqueued_task_ids == ("a-high", "a-normal", "b-low")
    assert result.deferred_task_ids == ()
    first = scheduler.dispatch_next()
    second = scheduler.dispatch_next()
    assert first is not None and first.task_id == "a-high"
    assert second is not None and second.task_id == "a-normal"


def test_reconstructor_excludes_running_terminal_and_legacy_nonreconstructable_tasks(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    store.create_task(
        "pending-good",
        job_id="job-a",
        descriptor={"frame_id": 1, "stage_plan": "frame-v1"},
    )
    store.create_task("legacy-style", job_id="job-a")
    store.create_task(
        "running-task",
        job_id="job-a",
        descriptor={"frame_id": 2, "stage_plan": "frame-v1"},
    )
    store.assign_task(
        "running-task",
        expected_generation=0,
        worker_id="worker-1",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )
    store.create_task(
        "success-task",
        job_id="job-a",
        descriptor={"frame_id": 3, "stage_plan": "frame-v1"},
    )
    success_running = store.assign_task(
        "success-task",
        expected_generation=0,
        worker_id="worker-2",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )
    store.finish_task(
        "success-task",
        expected_generation=success_running.generation,
        worker_id="worker-2",
        attempt=1,
        new_state="SUCCEEDED",
        event_code="TASK.SUCCEEDED",
    )

    scheduler = BoundedFairScheduler(max_inflight_tasks=2, max_queued_tasks=8)
    result = SchedulerReconstructor(store).rebuild_jobs(scheduler, ("job-a",))

    assert result.enqueued_task_ids == ("pending-good",)
    assert scheduler.queued_count == 1


def test_reconstructor_reports_deferred_when_queue_is_full(tmp_path: Path) -> None:
    store = _store(tmp_path)
    for index in range(3):
        store.create_task(
            f"task-{index}",
            job_id="job-a",
            descriptor={"frame_id": index, "stage_plan": "frame-v1"},
        )
    scheduler = BoundedFairScheduler(max_inflight_tasks=1, max_queued_tasks=2)

    result = SchedulerReconstructor(store).rebuild_jobs(scheduler, ("job-a",))

    assert result.enqueued_task_ids == ("task-0", "task-1")
    assert result.deferred_task_ids == ("task-2",)
    assert scheduler.queued_count == 2


def test_reconstructor_rejects_unsupported_descriptor_before_partial_enqueue(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.create_task(
        "good-task",
        job_id="job-a",
        descriptor={"frame_id": 1},
        descriptor_version=1,
    )
    store.create_task(
        "future-task",
        job_id="job-a",
        descriptor={"frame_id": 2},
        descriptor_version=99,
    )
    scheduler = BoundedFairScheduler(max_inflight_tasks=2, max_queued_tasks=4)

    try:
        SchedulerReconstructor(store).rebuild_jobs(scheduler, ("job-a",))
    except RuntimeError as exc:
        assert "unsupported task descriptor version" in str(exc)
    else:
        raise AssertionError("expected unsupported descriptor rejection")

    assert scheduler.queued_count == 0
