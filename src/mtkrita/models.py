from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class ProcessingMode(StrEnum):
    AUTO = "auto"
    TRANSPARENT = "transparent"
    OPAQUE = "opaque"


class FrameStatus(StrEnum):
    PASS = "PASS"
    AUTO_FIXED = "AUTO_FIXED"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    measurements: dict[str, Any] = field(default_factory=dict)


@dataclass
class FrameResult:
    index: int
    row: int
    column: int
    status: FrameStatus = FrameStatus.REVIEW
    extraction_rect: tuple[int, int, int, int] | None = None
    extraction_method: str | None = None
    extraction_confidence: float | None = None
    processing_mode: ProcessingMode | None = None
    content_bbox: tuple[int, int, int, int] | None = None
    findings: list[Finding] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    providers: dict[str, str] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    output_file: str | None = None
    output_sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class JobManifest:
    job_id: str
    created_at: str
    input_file: str
    input_hash: str
    engine_version: str
    config_hash: str | None = None
    frames: list[FrameResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FileInspection:
    path: Path
    format: str
    width: int
    height: int
    mode: str
    has_alpha: bool
    alpha_min: int | None
    alpha_max: int | None
    transparent_pixel_ratio: float | None
    sha256: str
