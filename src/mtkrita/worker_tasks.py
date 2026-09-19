from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from .job_store import JobStore
from .messages import MessageEnvelope, MessageKind
from .path_manager import PathManager

EXECUTE_TASK_PAYLOAD_VERSION = 1
TASK_RESULT_PAYLOAD_VERSION = 1


class WorkerTaskContractError(ValueError):
    """Raised when an ExecuteTask or candidate-result payload violates its contract."""


@dataclass(frozen=True)
class ExecuteTaskRequest:
    job_id: str
    task_id: str
    worker_id: str
    attempt: int
    descriptor_version: int
    descriptor: dict[str, Any]
    scratch_path: str


class TaskCandidateStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    REVIEW = "REVIEW"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ProvisionalArtifact:
    filename: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        candidate = Path(self.filename)
        if not self.filename or candidate.name != self.filename or self.filename in {".", ".."}:
            raise WorkerTaskContractError("artifact filename must be one safe path component")
        if len(self.sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.sha256):
            raise WorkerTaskContractError("artifact sha256 must be lowercase hexadecimal")
        if self.byte_size < 0:
            raise WorkerTaskContractError("artifact byte_size must be non-negative")


@dataclass(frozen=True)
class TaskCandidateResult:
    status: TaskCandidateStatus
    artifacts: tuple[ProvisionalArtifact, ...] = ()
    findings: tuple[dict[str, Any], ...] = ()
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.status == TaskCandidateStatus.FAILED:
            if not self.error_code:
                raise WorkerTaskContractError("FAILED candidate requires error_code")
        elif self.error_code is not None or self.error_message is not None:
            raise WorkerTaskContractError("non-FAILED candidate must not carry failure fields")


class TaskExecutor(Protocol):
    def execute(self, request: ExecuteTaskRequest) -> TaskCandidateResult: ...


class ExecuteTaskCommandBuilder:
    """Build worker commands only from current durable authority and PathManager refs."""

    def __init__(self, *, jobs: JobStore, paths: PathManager) -> None:
        self._jobs = jobs
        self._paths = paths

    def build(self, task_id: str) -> MessageEnvelope:
        task = self._jobs.get_task(task_id)
        descriptor = self._jobs.get_task_descriptor(task_id)
        if task.state != "RUNNING" or task.worker_id is None or task.attempt <= 0:
            raise RuntimeError("ExecuteTask requires authoritative RUNNING task assignment")
        if descriptor.job_id != task.job_id or descriptor.task_id != task.task_id:
            raise RuntimeError("durable task descriptor identity mismatch")
        if not descriptor.reconstructable or descriptor.descriptor_version <= 0:
            raise RuntimeError("task has no executable durable descriptor")

        scratch = self._paths.prepare_worker_scratch(task.job_id, task.worker_id)
        self._paths.assert_owned(scratch.path)
        return MessageEnvelope.create(
            kind=MessageKind.COMMAND,
            message_type="ExecuteTask",
            job_id=task.job_id,
            task_id=task.task_id,
            worker_id=task.worker_id,
            attempt=task.attempt,
            payload={
                "execute_schema_version": EXECUTE_TASK_PAYLOAD_VERSION,
                "descriptor_version": descriptor.descriptor_version,
                "descriptor": descriptor.descriptor,
                "scratch_path": str(scratch.path),
            },
        )


def parse_execute_task(message: MessageEnvelope) -> ExecuteTaskRequest:
    if message.kind != MessageKind.COMMAND or message.message_type != "ExecuteTask":
        raise WorkerTaskContractError("message is not an ExecuteTask command")
    if not message.job_id or not message.task_id or not message.worker_id:
        raise WorkerTaskContractError("ExecuteTask requires job/task/worker identity")
    if message.attempt is None or message.attempt <= 0:
        raise WorkerTaskContractError("ExecuteTask requires positive attempt")

    payload = message.payload
    required = {
        "execute_schema_version",
        "descriptor_version",
        "descriptor",
        "scratch_path",
    }
    if set(payload) != required:
        raise WorkerTaskContractError("ExecuteTask payload fields do not match schema")
    schema_version = _exact_int(payload["execute_schema_version"], "execute_schema_version")
    if schema_version != EXECUTE_TASK_PAYLOAD_VERSION:
        raise WorkerTaskContractError("unsupported ExecuteTask payload version")
    descriptor_version = _exact_int(payload["descriptor_version"], "descriptor_version")
    if descriptor_version <= 0:
        raise WorkerTaskContractError("descriptor_version must be positive")
    descriptor = payload["descriptor"]
    if not isinstance(descriptor, dict):
        raise WorkerTaskContractError("descriptor must be a JSON object")
    scratch_path = payload["scratch_path"]
    if not isinstance(scratch_path, str) or not scratch_path:
        raise WorkerTaskContractError("scratch_path must be a non-empty string")

    return ExecuteTaskRequest(
        job_id=message.job_id,
        task_id=message.task_id,
        worker_id=message.worker_id,
        attempt=message.attempt,
        descriptor_version=descriptor_version,
        descriptor=dict(descriptor),
        scratch_path=scratch_path,
    )


def candidate_event(
    *,
    result: TaskCandidateResult,
    causation: MessageEnvelope,
) -> MessageEnvelope:
    request = parse_execute_task(causation)
    message_type = {
        TaskCandidateStatus.SUCCEEDED: "TaskSucceededCandidate",
        TaskCandidateStatus.REVIEW: "TaskReviewCandidate",
        TaskCandidateStatus.FAILED: "TaskFailed",
    }[result.status]
    return MessageEnvelope.create(
        kind=MessageKind.EVENT,
        message_type=message_type,
        job_id=request.job_id,
        correlation_id=causation.correlation_id,
        causation_id=causation.message_id,
        task_id=request.task_id,
        worker_id=request.worker_id,
        attempt=request.attempt,
        payload={
            "result_schema_version": TASK_RESULT_PAYLOAD_VERSION,
            "artifacts": [asdict(artifact) for artifact in result.artifacts],
            "findings": list(result.findings),
            "error_code": result.error_code,
            "error_message": result.error_message,
        },
    )


def parse_candidate_event(message: MessageEnvelope) -> TaskCandidateResult:
    status_by_type = {
        "TaskSucceededCandidate": TaskCandidateStatus.SUCCEEDED,
        "TaskReviewCandidate": TaskCandidateStatus.REVIEW,
        "TaskFailed": TaskCandidateStatus.FAILED,
    }
    if message.kind != MessageKind.EVENT or message.message_type not in status_by_type:
        raise WorkerTaskContractError("message is not a task candidate event")
    if not message.job_id or not message.task_id or not message.worker_id:
        raise WorkerTaskContractError("candidate event requires job/task/worker identity")
    if message.attempt is None or message.attempt <= 0:
        raise WorkerTaskContractError("candidate event requires positive attempt")

    payload = message.payload
    required = {
        "result_schema_version",
        "artifacts",
        "findings",
        "error_code",
        "error_message",
    }
    if set(payload) != required:
        raise WorkerTaskContractError("candidate result fields do not match schema")
    schema_version = _exact_int(payload["result_schema_version"], "result_schema_version")
    if schema_version != TASK_RESULT_PAYLOAD_VERSION:
        raise WorkerTaskContractError("unsupported task result payload version")

    raw_artifacts = payload["artifacts"]
    if not isinstance(raw_artifacts, list):
        raise WorkerTaskContractError("artifacts must be a list")
    artifacts: list[ProvisionalArtifact] = []
    for item in raw_artifacts:
        if not isinstance(item, dict) or set(item) != {"filename", "sha256", "byte_size"}:
            raise WorkerTaskContractError("invalid provisional artifact payload")
        filename = item["filename"]
        sha256 = item["sha256"]
        byte_size = item["byte_size"]
        if not isinstance(filename, str) or not isinstance(sha256, str):
            raise WorkerTaskContractError("artifact filename/hash must be strings")
        artifacts.append(
            ProvisionalArtifact(
                filename=filename,
                sha256=sha256,
                byte_size=_exact_int(byte_size, "byte_size"),
            )
        )

    raw_findings = payload["findings"]
    if not isinstance(raw_findings, list) or any(not isinstance(item, dict) for item in raw_findings):
        raise WorkerTaskContractError("findings must be a list of JSON objects")
    error_code = _optional_str(payload["error_code"], "error_code")
    error_message = _optional_str(payload["error_message"], "error_message")
    return TaskCandidateResult(
        status=status_by_type[message.message_type],
        artifacts=tuple(artifacts),
        findings=tuple(dict(item) for item in raw_findings),
        error_code=error_code,
        error_message=error_message,
    )


def _exact_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise WorkerTaskContractError(f"{label} must be an integer")
    return value


def _optional_str(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise WorkerTaskContractError(f"{label} must be null or a non-empty string")
    return value
