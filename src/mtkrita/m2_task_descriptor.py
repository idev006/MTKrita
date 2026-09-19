from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .path_manager import PathManager, PathRef

if TYPE_CHECKING:
    from .job_store import TaskDescriptorRecord, TaskRecord
    from .worker_tasks import ProvisionalArtifact

M2_FRAME_TASK_TYPE = "m2.frame"
M2_FRAME_DESCRIPTOR_VERSION = 1


class M2TaskDescriptorError(ValueError):
    """Raised when a durable M2 frame descriptor violates its production schema."""


@dataclass(frozen=True)
class M2PipelineConfigSnapshot:
    target_width: int
    target_height: int
    margin: int
    remove_border: bool
    remove_metadata: bool
    border_auto_threshold: float
    metadata_auto_threshold: float


@dataclass(frozen=True)
class M2FrameTaskDescriptor:
    task_type: str
    input_name: str
    input_sha256: str
    output_name: str
    frame_index: int
    row: int
    column: int
    extraction_rect: tuple[int, int, int, int]
    extraction_method: str
    extraction_confidence: float
    pipeline_config: M2PipelineConfigSnapshot


_DESCRIPTOR_FIELDS = frozenset(
    {
        "task_type",
        "input_name",
        "input_sha256",
        "output_name",
        "frame_index",
        "row",
        "column",
        "extraction_rect",
        "extraction_method",
        "extraction_confidence",
        "pipeline_config",
    }
)
_CONFIG_FIELDS = frozenset(
    {
        "target_width",
        "target_height",
        "margin",
        "remove_border",
        "remove_metadata",
        "border_auto_threshold",
        "metadata_auto_threshold",
    }
)


def parse_m2_frame_descriptor(
    descriptor: dict[str, Any],
    *,
    descriptor_version: int = M2_FRAME_DESCRIPTOR_VERSION,
) -> M2FrameTaskDescriptor:
    if descriptor_version != M2_FRAME_DESCRIPTOR_VERSION:
        raise M2TaskDescriptorError("unsupported M2 frame descriptor version")
    if set(descriptor) != _DESCRIPTOR_FIELDS:
        raise M2TaskDescriptorError("M2 frame descriptor fields do not match schema")
    if descriptor.get("task_type") != M2_FRAME_TASK_TYPE:
        raise M2TaskDescriptorError("unsupported M2 task_type")

    input_name = _safe_filename(descriptor.get("input_name"), "input_name")
    input_sha256 = _sha256(descriptor.get("input_sha256"), "input_sha256")
    output_name = _safe_filename(descriptor.get("output_name"), "output_name")
    if Path(output_name).suffix.lower() != ".png":
        raise M2TaskDescriptorError("output_name must use .png extension")

    frame_index = _non_negative_int(descriptor.get("frame_index"), "frame_index")
    row = _non_negative_int(descriptor.get("row"), "row")
    column = _non_negative_int(descriptor.get("column"), "column")

    raw_rect = descriptor.get("extraction_rect")
    if not isinstance(raw_rect, list) or len(raw_rect) != 4:
        raise M2TaskDescriptorError("extraction_rect must be a four-integer list")
    rect = tuple(_exact_int(value, "extraction_rect item") for value in raw_rect)
    left, top, right, bottom = rect
    if left < 0 or top < 0 or right <= left or bottom <= top:
        raise M2TaskDescriptorError("extraction_rect geometry is invalid")

    extraction_method = descriptor.get("extraction_method")
    if not isinstance(extraction_method, str) or not extraction_method:
        raise M2TaskDescriptorError("extraction_method must be a non-empty string")
    extraction_confidence = _ratio(descriptor.get("extraction_confidence"), "extraction_confidence")

    raw_config = descriptor.get("pipeline_config")
    if not isinstance(raw_config, dict) or set(raw_config) != _CONFIG_FIELDS:
        raise M2TaskDescriptorError("pipeline_config fields do not match schema")
    target_width = _positive_int(raw_config.get("target_width"), "target_width")
    target_height = _positive_int(raw_config.get("target_height"), "target_height")
    margin = _non_negative_int(raw_config.get("margin"), "margin")
    if margin * 2 >= min(target_width, target_height):
        raise M2TaskDescriptorError("margin leaves no usable output canvas")
    remove_border = _exact_bool(raw_config.get("remove_border"), "remove_border")
    remove_metadata = _exact_bool(raw_config.get("remove_metadata"), "remove_metadata")
    border_auto_threshold = _ratio(
        raw_config.get("border_auto_threshold"), "border_auto_threshold"
    )
    metadata_auto_threshold = _ratio(
        raw_config.get("metadata_auto_threshold"), "metadata_auto_threshold"
    )

    return M2FrameTaskDescriptor(
        task_type=M2_FRAME_TASK_TYPE,
        input_name=input_name,
        input_sha256=input_sha256,
        output_name=output_name,
        frame_index=frame_index,
        row=row,
        column=column,
        extraction_rect=(left, top, right, bottom),
        extraction_method=extraction_method,
        extraction_confidence=extraction_confidence,
        pipeline_config=M2PipelineConfigSnapshot(
            target_width=target_width,
            target_height=target_height,
            margin=margin,
            remove_border=remove_border,
            remove_metadata=remove_metadata,
            border_auto_threshold=border_auto_threshold,
            metadata_auto_threshold=metadata_auto_threshold,
        ),
    )


class M2FrameTargetResolver:
    """Resolve final M2 output only from a validated durable descriptor."""

    def __init__(self, paths: PathManager) -> None:
        self._paths = paths

    def resolve(
        self,
        *,
        task: TaskRecord,
        descriptor: TaskDescriptorRecord,
        artifact: ProvisionalArtifact,
    ) -> PathRef:
        del artifact
        if descriptor.task_id != task.task_id or descriptor.job_id != task.job_id:
            raise M2TaskDescriptorError("M2 target descriptor identity mismatch")
        parsed = parse_m2_frame_descriptor(
            descriptor.descriptor,
            descriptor_version=descriptor.descriptor_version,
        )
        return self._paths.output(task.job_id, parsed.output_name)


def _safe_filename(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise M2TaskDescriptorError(f"{label} must be a non-empty string")
    candidate = Path(value)
    if candidate.name != value or value in {".", ".."} or "\x00" in value:
        raise M2TaskDescriptorError(f"{label} must be one safe path component")
    return value


def _sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise M2TaskDescriptorError(f"{label} must be lowercase SHA-256 hexadecimal")
    return value


def _exact_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise M2TaskDescriptorError(f"{label} must be an integer")
    return value


def _non_negative_int(value: object, label: str) -> int:
    parsed = _exact_int(value, label)
    if parsed < 0:
        raise M2TaskDescriptorError(f"{label} must be non-negative")
    return parsed


def _positive_int(value: object, label: str) -> int:
    parsed = _exact_int(value, label)
    if parsed <= 0:
        raise M2TaskDescriptorError(f"{label} must be positive")
    return parsed


def _exact_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise M2TaskDescriptorError(f"{label} must be a boolean")
    return value


def _ratio(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise M2TaskDescriptorError(f"{label} must be numeric")
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise M2TaskDescriptorError(f"{label} must be between 0 and 1")
    return parsed
