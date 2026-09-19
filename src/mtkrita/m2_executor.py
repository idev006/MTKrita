from __future__ import annotations

import hashlib
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from PIL import Image

from .m2_task_descriptor import M2PipelineConfigSnapshot, parse_m2_frame_descriptor
from .worker_tasks import (
    ExecuteTaskRequest,
    ProvisionalArtifact,
    TaskCandidateResult,
    TaskCandidateStatus,
)


class M2FrameExecutorError(RuntimeError):
    """Raised when the M2 worker adapter cannot safely execute its contract."""


class FrameProcessor(Protocol):
    def __call__(
        self,
        image: Image.Image,
        *,
        index: int,
        row: int,
        column: int,
        extraction_rect: tuple[int, int, int, int] | None,
        extraction_method: str | None,
        extraction_confidence: float | None,
        config: object,
    ) -> object: ...


class PipelineConfigFactory(Protocol):
    def __call__(self, snapshot: M2PipelineConfigSnapshot) -> object: ...


class PngWriter(Protocol):
    def __call__(
        self,
        image: Image.Image,
        target_path: str | Path,
        *,
        allow_overwrite: bool = False,
    ) -> object: ...


ImageLoader = Callable[[str], Image.Image]


class M2FrameTaskExecutor:
    """Adapt the headless M2 frame pipeline to the generic worker TaskExecutor contract."""

    def __init__(
        self,
        *,
        frame_processor: FrameProcessor,
        config_factory: PipelineConfigFactory,
        png_writer: PngWriter,
        image_loader: ImageLoader | None = None,
    ) -> None:
        self._frame_processor = frame_processor
        self._config_factory = config_factory
        self._png_writer = png_writer
        self._image_loader = image_loader or _load_image_detached

    def execute(self, request: ExecuteTaskRequest) -> TaskCandidateResult:
        descriptor = parse_m2_frame_descriptor(
            request.descriptor,
            descriptor_version=request.descriptor_version,
        )
        if len(request.inputs) != 1:
            raise M2FrameExecutorError("M2 frame task requires exactly one immutable input")
        task_input = request.inputs[0]
        if task_input.name != descriptor.input_name or task_input.sha256 != descriptor.input_sha256:
            raise M2FrameExecutorError("M2 task input identity does not match durable descriptor")
        input_path = Path(task_input.path)
        self._verify_input(
            input_path,
            expected_sha256=task_input.sha256,
            expected_byte_size=task_input.byte_size,
        )

        scratch = Path(request.scratch_path)
        if not scratch.is_dir():
            raise M2FrameExecutorError("worker scratch directory is not prepared")

        image = self._image_loader(str(input_path))
        config = self._config_factory(descriptor.pipeline_config)
        output = self._frame_processor(
            image,
            index=descriptor.frame_index,
            row=descriptor.row,
            column=descriptor.column,
            extraction_rect=descriptor.extraction_rect,
            extraction_method=descriptor.extraction_method,
            extraction_confidence=descriptor.extraction_confidence,
            config=config,
        )
        result = getattr(output, "result", None)
        processed_image = getattr(output, "image", None)
        if result is None or processed_image is None:
            raise M2FrameExecutorError("frame processor returned an invalid result contract")

        status = _enum_value(getattr(result, "status", None))
        findings = _serialize_findings(result)
        evidence = _serialize_evidence(result, status=status)
        candidate_records = (*findings, evidence)

        if status in {"PASS", "AUTO_FIXED"}:
            filename = _candidate_filename(request.task_id, request.attempt)
            target = scratch / filename
            self._png_writer(processed_image, target, allow_overwrite=False)
            if not target.is_file():
                raise M2FrameExecutorError("PNG writer did not produce the provisional artifact")
            digest = _sha256_file(target)
            return TaskCandidateResult(
                status=TaskCandidateStatus.SUCCEEDED,
                artifacts=(
                    ProvisionalArtifact(
                        filename=filename,
                        sha256=digest,
                        byte_size=target.stat().st_size,
                    ),
                ),
                findings=candidate_records,
            )

        if status == "REVIEW":
            return TaskCandidateResult(
                status=TaskCandidateStatus.REVIEW,
                findings=candidate_records,
            )

        if status == "FAIL":
            error_code, error_message = _failure_identity(result)
            return TaskCandidateResult(
                status=TaskCandidateStatus.FAILED,
                findings=candidate_records,
                error_code=error_code,
                error_message=error_message,
            )

        raise M2FrameExecutorError(f"unsupported M2 frame status: {status!r}")

    @staticmethod
    def _verify_input(
        path: Path,
        *,
        expected_sha256: str,
        expected_byte_size: int,
    ) -> None:
        if not path.is_file():
            raise M2FrameExecutorError("staged input file is missing")
        if path.is_symlink():
            raise M2FrameExecutorError("staged input must not be a symlink")
        if path.stat().st_size != expected_byte_size:
            raise M2FrameExecutorError("staged input byte-size mismatch")
        if _sha256_file(path) != expected_sha256:
            raise M2FrameExecutorError("staged input hash mismatch")


def _load_image_detached(path: str) -> Image.Image:
    with Image.open(path) as image:
        return image.copy()


def _candidate_filename(task_id: str, attempt: int) -> str:
    identity = hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:16]
    return f"candidate-{identity}-a{attempt}.png"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _enum_value(value: object) -> str:
    if isinstance(value, Enum):
        raw = value.value
        if isinstance(raw, str):
            return raw
    if isinstance(value, str):
        return value
    raise M2FrameExecutorError("frame result status is not a supported string enum")


def _serialize_findings(result: object) -> tuple[dict[str, Any], ...]:
    raw_findings = getattr(result, "findings", None)
    if not isinstance(raw_findings, list):
        raise M2FrameExecutorError("frame result findings must be a list")
    serialized: list[dict[str, Any]] = []
    for finding in raw_findings:
        code = getattr(finding, "code", None)
        severity = getattr(finding, "severity", None)
        message = getattr(finding, "message", None)
        measurements = getattr(finding, "measurements", None)
        if not isinstance(code, str) or not isinstance(severity, str) or not isinstance(message, str):
            raise M2FrameExecutorError("frame finding contract is invalid")
        if not isinstance(measurements, dict):
            raise M2FrameExecutorError("frame finding measurements must be a mapping")
        serialized.append(
            {
                "code": code,
                "severity": severity,
                "message": message,
                "measurements": _json_value(measurements),
            }
        )
    return tuple(serialized)


def _serialize_evidence(result: object, *, status: str) -> dict[str, Any]:
    actions = getattr(result, "actions", None)
    evidence = getattr(result, "evidence", None)
    if not isinstance(actions, list) or not isinstance(evidence, dict):
        raise M2FrameExecutorError("frame result evidence contract is invalid")
    processing_mode = getattr(result, "processing_mode", None)
    return {
        "code": "M2.FRAME_EVIDENCE",
        "status": status,
        "actions": _json_value(actions),
        "processing_mode": _json_value(processing_mode),
        "content_bbox": _json_value(getattr(result, "content_bbox", None)),
        "evidence": _json_value(evidence),
    }


def _failure_identity(result: object) -> tuple[str, str | None]:
    findings = getattr(result, "findings", [])
    if findings:
        first = findings[0]
        code = getattr(first, "code", None)
        message = getattr(first, "message", None)
        if isinstance(code, str) and code:
            return code, message if isinstance(message, str) and message else None
    return "M2.FRAME_FAIL", "M2 frame pipeline returned FAIL"


def _json_value(value: object) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return _json_value(value.value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise M2FrameExecutorError("evidence mappings require string keys")
        return {key: _json_value(item) for key, item in value.items()}
    raise M2FrameExecutorError(f"evidence contains non-JSON value: {type(value).__name__}")
