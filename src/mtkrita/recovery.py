from __future__ import annotations

from dataclasses import dataclass

from .job_store import JobStore


@dataclass(frozen=True)
class ReconciledJob:
    job_id: str
    prior_state: str
    interrupted_tasks: tuple[str, ...]


@dataclass(frozen=True)
class StartupReconciler:
    """Convert orphaned active state from a previous process into durable INTERRUPTED state."""

    jobs: JobStore

    def reconcile(self) -> tuple[ReconciledJob, ...]:
        results: list[ReconciledJob] = []
        active_jobs = self.jobs.list_jobs(states=("PROCESSING", "PAUSING", "STOPPING"))
        for job in active_jobs:
            interrupted: list[str] = []
            for task in self.jobs.list_tasks(job.job_id, state="RUNNING"):
                if task.worker_id is None or task.attempt <= 0:
                    raise RuntimeError("RUNNING task lacks durable worker/attempt identity")
                self.jobs.finish_task(
                    task.task_id,
                    expected_generation=task.generation,
                    worker_id=task.worker_id,
                    attempt=task.attempt,
                    new_state="INTERRUPTED",
                    event_code="TASK.INTERRUPTED_BY_STARTUP_RECOVERY",
                )
                interrupted.append(task.task_id)

            current = self.jobs.get_job(job.job_id)
            self.jobs.transition(
                job.job_id,
                expected_state=current.state,
                expected_generation=current.generation,
                new_state="INTERRUPTED",
                event_code="JOB.INTERRUPTED_BY_STARTUP_RECOVERY",
                detail={"interrupted_tasks": interrupted},
            )
            results.append(
                ReconciledJob(
                    job_id=job.job_id,
                    prior_state=job.state,
                    interrupted_tasks=tuple(interrupted),
                )
            )
        return tuple(results)
