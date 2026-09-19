from __future__ import annotations

from dataclasses import dataclass

from .job_store import JobRecord, JobStore


@dataclass(frozen=True)
class JobLifecycleController:
    """Own job control-state policy; persistence remains delegated to JobStore."""

    jobs: JobStore

    def start_processing(self, job_id: str) -> JobRecord:
        return self._transition(
            job_id,
            allowed_states={"READY"},
            new_state="PROCESSING",
            event_code="JOB.PROCESSING_STARTED",
        )

    def request_pause(self, job_id: str) -> JobRecord:
        return self._transition(
            job_id,
            allowed_states={"PROCESSING"},
            new_state="PAUSING",
            event_code="JOB.PAUSE_REQUESTED",
        )

    def finalize_pause(self, job_id: str) -> JobRecord:
        self._require_no_running_tasks(job_id)
        return self._transition(
            job_id,
            allowed_states={"PAUSING"},
            new_state="PAUSED",
            event_code="JOB.PAUSED",
        )

    def request_stop(self, job_id: str) -> JobRecord:
        return self._transition(
            job_id,
            allowed_states={"PROCESSING", "PAUSING", "PAUSED"},
            new_state="STOPPING",
            event_code="JOB.STOP_REQUESTED",
        )

    def finalize_stop(self, job_id: str) -> JobRecord:
        self._require_no_running_tasks(job_id)
        return self._transition(
            job_id,
            allowed_states={"STOPPING"},
            new_state="STOPPED",
            event_code="JOB.STOPPED",
        )

    def resume(self, job_id: str) -> JobRecord:
        return self._transition(
            job_id,
            allowed_states={"PAUSED", "STOPPED", "INTERRUPTED"},
            new_state="PROCESSING",
            event_code="JOB.RESUMED",
        )

    def _transition(
        self,
        job_id: str,
        *,
        allowed_states: set[str],
        new_state: str,
        event_code: str,
    ) -> JobRecord:
        current = self.jobs.get_job(job_id)
        if current.state not in allowed_states:
            allowed = ", ".join(sorted(allowed_states))
            raise RuntimeError(
                f"job state {current.state} cannot transition to {new_state}; allowed: {allowed}"
            )
        return self.jobs.transition(
            job_id,
            expected_state=current.state,
            expected_generation=current.generation,
            new_state=new_state,
            event_code=event_code,
        )

    def _require_no_running_tasks(self, job_id: str) -> None:
        running = self.jobs.list_tasks(job_id, state="RUNNING")
        if running:
            raise RuntimeError("job still has authoritative RUNNING tasks")
