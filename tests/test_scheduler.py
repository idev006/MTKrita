from mtkrita.scheduler import BoundedFairScheduler, ScheduledTask, TaskPriority


def test_scheduler_enforces_queue_and_inflight_bounds() -> None:
    scheduler = BoundedFairScheduler(max_inflight_tasks=1, max_queued_tasks=2)
    assert scheduler.submit(ScheduledTask("t1", "job-1")) is True
    assert scheduler.submit(ScheduledTask("t2", "job-1")) is True
    assert scheduler.submit(ScheduledTask("t3", "job-1")) is False

    first = scheduler.dispatch_next()
    assert first is not None and first.task_id == "t1"
    assert scheduler.dispatch_next() is None
    scheduler.complete("t1")
    second = scheduler.dispatch_next()
    assert second is not None and second.task_id == "t2"


def test_scheduler_round_robins_jobs_at_same_priority() -> None:
    scheduler = BoundedFairScheduler(max_inflight_tasks=4, max_queued_tasks=8)
    for task in (
        ScheduledTask("a1", "job-a"),
        ScheduledTask("a2", "job-a"),
        ScheduledTask("b1", "job-b"),
        ScheduledTask("b2", "job-b"),
    ):
        assert scheduler.submit(task)

    dispatched = [scheduler.dispatch_next() for _ in range(4)]
    assert [task.task_id for task in dispatched if task is not None] == ["a1", "b1", "a2", "b2"]


def test_scheduler_respects_job_admission_without_dropping_blocked_tasks() -> None:
    blocked = {"job-paused"}
    scheduler = BoundedFairScheduler(
        max_inflight_tasks=2,
        max_queued_tasks=4,
        job_dispatchable=lambda job_id: job_id not in blocked,
    )
    scheduler.submit(ScheduledTask("paused-1", "job-paused"))
    scheduler.submit(ScheduledTask("ready-1", "job-ready"))

    task = scheduler.dispatch_next()
    assert task is not None and task.task_id == "ready-1"
    scheduler.complete("ready-1")
    assert scheduler.dispatch_next() is None
    assert scheduler.queued_count == 1

    blocked.clear()
    resumed = scheduler.dispatch_next()
    assert resumed is not None and resumed.task_id == "paused-1"


def test_priority_burst_limit_prevents_lower_priority_starvation() -> None:
    scheduler = BoundedFairScheduler(
        max_inflight_tasks=8,
        max_queued_tasks=16,
        priority_burst_limit=2,
    )
    scheduler.submit(ScheduledTask("high-1", "job-a", TaskPriority.HIGH))
    scheduler.submit(ScheduledTask("high-2", "job-b", TaskPriority.HIGH))
    scheduler.submit(ScheduledTask("high-3", "job-c", TaskPriority.HIGH))
    scheduler.submit(ScheduledTask("normal-1", "job-d", TaskPriority.NORMAL))

    first = scheduler.dispatch_next()
    second = scheduler.dispatch_next()
    third = scheduler.dispatch_next()

    assert first is not None and first.priority == TaskPriority.HIGH
    assert second is not None and second.priority == TaskPriority.HIGH
    assert third is not None and third.task_id == "normal-1"


def test_scheduler_rejects_duplicate_task_identity() -> None:
    scheduler = BoundedFairScheduler(max_inflight_tasks=2, max_queued_tasks=4)
    scheduler.submit(ScheduledTask("task-1", "job-1"))
    try:
        scheduler.submit(ScheduledTask("task-1", "job-2"))
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("expected duplicate task rejection")
