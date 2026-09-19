from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .artifact_commit import ArtifactCommitCoordinator
from .job_store import JobStore, TaskDescriptorRecord, TaskRecord
from .messages import MessageEnvelope
from .path_manager import PathKind, PathManager, PathRef
from .resource_broker import CommittedArtifact, ResourceBroker
from .task_leases import TaskLeaseRegistry
from .worker_manager import WorkerManager, WorkerState
from .worker_tasks import (
    ProvisionalArtifact,
    TaskCandidateResult,
    TaskCandidateStatus,
    WorkerTaskContractError,
    parse_candidate_event,
)


class CandidateResultError(RuntimeError):
    """Raised when a worker candidate cannot be accepted by durable authority."""


class CandidateTargetResolver(Protocol):
    def resolve(
        self,
        *,
        task: TaskRecord,
        descriptor: TaskDescriptorRecord,
        artifact: ProvisionalArtifact,
    ) -> PathRef: ...


class InflightCompletion(Protocol):
    def complete(self, task_id: str) -> object: ...


@dataclass(frozen=True)
class CandidateOutcome:
    task: TaskRecord
    status: TaskCandidateStatus
    committed_artifact: CommittedArtifact | None = None


class CandidateResultCoordinator:
    """Accept worker candidates only through durable task/artifact authority."""

    def __init__(
        self,
        *,
        jobs: JobStore,
        paths: PathManager,
        resources: ResourceBroker,
        commits: ArtifactCommitCoordinator,
        leases: TaskLeaseRegistry,
        workers: WorkerManager,
        targets: CandidateTargetResolver,
        inflight: InflightCompletion | None = None,
    ) -> None:
        self._jobs = jobs
        self._paths = paths
        self._resources = resources
        self._commits = commits
        self._leases = leases
        self._workers = workers
        self._targets = targets
        self._inflight = inflight

    def accept(self, message: MessageEnvelope) -> CandidateOutcome:
        try:
            result = parse_candidate_event(message)
        except WorkerTaskContractError as exc:
            raise CandidateResultError(str(exc)) from exc

        task = self._require_authority(message)
        if result.status == TaskCandidateStatus.SUCCEEDED:
            return self._accept_success(task, result)
        if result.artifacts:
            raise CandidateResultError("non-success candidate must not publish artifacts")
        worker_id = self._require_worker_id(task)
        if result.status == TaskCandidateStatus.REVIEW:
            updated = self._jobs.finish_task(
                task.task_id,
                expected_generation=task.generation,
                worker_id=worker_id,
                attempt=task.attempt,
                new_state="REVIEW",
                event_code="TASK.REVIEW_FROM_WORKER_CANDIDATE",
            )
        else:
            updated = self._jobs.finish_task(
                task.task_id,
                expected_generation=task.generation,
                worker_id=worker_id,
                attempt=task.attempt,
                new_state="FAILED",
                event_code="TASK.FAILED_FROM_WORKER_CANDIDATE",
            )
        self._release_runtime(task)
        return CandidateOutcome(task=updated, status=result.status)

    def _accept_success(
        self,
        task: TaskRecord,
        result: TaskCandidateResult,
    ) -> CandidateOutcome:
        if len(result.artifacts) != 1:
            raise CandidateResultError("success candidate requires exactly one primary artifact")
        artifact = result.artifacts[0]
        worker_id = self._require_worker_id(task)

        source = self._paths.worker_file(task.job_id, worker_id, artifact.filename)
        try:
            candidate = self._resources.validate_worker_file(
                source,
                expected_sha256=artifact.sha256,
            )
        except (FileNotFoundError, ValueError) as exc:
            raise CandidateResultError(str(exc)) from exc
        if candidate.byte_size != artifact.byte_size:
            raise CandidateResultError("artifact byte-size mismatch")

        descriptor = self._jobs.get_task_descriptor(task.task_id)
        target = self._targets.resolve(task=task, descriptor=descriptor, artifact=artifact)
        self._validate_target(task, target)
        commit_id = f"{task.task_id}:attempt:{task.attempt}:primary"
        committed = self._commits.commit_task_artifact(
            commit_id=commit_id,
            task=task,
            source=source,
            target=target,
            expected_sha256=artifact.sha256,
        )
        updated = self._jobs.get_task(task.task_id)
        if updated.state != "SUCCEEDED":
            raise CandidateResultError("artifact commit did not finalize durable task success")
        self._release_runtime(task)
        return CandidateOutcome(
            task=updated,
            status=TaskCandidateStatus.SUCCEEDED,
            committed_artifact=committed,
        )

    def _require_authority(self, message: MessageEnvelope) -> TaskRecord:
        if message.task_id is None or message.worker_id is None or message.attempt is None:
            raise CandidateResultError("candidate identity is incomplete")
        task = self._jobs.get_task(message.task_id)
        if (
            task.job_id != message.job_id
            or task.state != "RUNNING"
            or task.worker_id != message.worker_id
            or task.attempt != message.attempt
        ):
            raise CandidateResultError("candidate does not match authoritative RUNNING task attempt")

        worker = self._workers.get(message.worker_id)
        if (
            worker.state != WorkerState.BUSY
            or worker.active_task_id != task.task_id
            or worker.active_attempt != task.attempt
        ):
            raise CandidateResultError("worker does not own authoritative task attempt")
        try:
            self._leases.require_active(
                task.task_id,
                worker_id=message.worker_id,
                attempt=message.attempt,
            )
        except ValueError as exc:
            raise CandidateResultError(str(exc)) from exc
        return task

    @staticmethod
    def _require_worker_id(task: TaskRecord) -> str:
        if task.worker_id is None:
            raise CandidateResultError("RUNNING task has no worker identity")
        return task.worker_id

    @staticmethod
    def _validate_target(task: TaskRecord, target: PathRef) -> None:
        if target.job_id != task.job_id:
            raise CandidateResultError("candidate target resolver returned cross-job target")
        if target.kind not in {PathKind.OUTPUT, PathKind.EVIDENCE}:
            raise CandidateResultError("candidate target must be authoritative output or evidence")
        if target.worker_id is not None:
            raise CandidateResultError("authoritative candidate target must not be worker-owned")

    def _release_runtime(self, task: TaskRecord) -> None:
        worker_id = self._require_worker_id(task)
        self._leases.discard(task.task_id, worker_id=worker_id, attempt=task.attempt)
        self._workers.release_task(worker_id, task_id=task.task_id, attempt=task.attempt)
        if self._inflight is not None:
            self._inflight.complete(task.task_id)
