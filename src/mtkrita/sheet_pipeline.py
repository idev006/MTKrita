from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from .exporter import bind_export_artifact, export_png_atomic
from .frame_pipeline import FramePipelineConfig
from .frame_pipeline_m3 import process_frame_with_m3
from .models import FrameResult, FrameStatus
from .sheet import GridSpec, GridSplitResult, split_grid_scaled


@dataclass(frozen=True)
class SheetPipelineSummary:
    input_file: str
    input_width: int
    input_height: int
    extraction_method: str
    extraction_confidence: float
    frame_count: int
    pass_count: int
    auto_fixed_count: int
    review_count: int
    fail_count: int
    output_directory: str
    report_file: str


@dataclass(frozen=True)
class SheetPipelineOutput:
    summary: SheetPipelineSummary
    frames: tuple[FrameResult, ...]


def _json_value(value: Any) -> Any:
    if hasattr(value, "value"):
        return _json_value(value.value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


def _prepare_output_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise ValueError("output path is not a directory")


def _split_sheet(image: Image.Image, grid: GridSpec) -> GridSplitResult:
    return split_grid_scaled(image, grid)


def process_sheet_file(
    input_path: str | Path,
    output_directory: str | Path,
    *,
    grid: GridSpec | None = None,
    frame_config: FramePipelineConfig | None = None,
    start_number: int = 1,
    allow_overwrite: bool = False,
) -> SheetPipelineOutput:
    """Process a complete sticker sheet into independent PNG frame artifacts."""
    source = Path(input_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    if start_number <= 0:
        raise ValueError("start_number must be positive")

    target_dir = Path(output_directory)
    _prepare_output_directory(target_dir)
    with Image.open(source) as opened:
        image = opened.copy()

    resolved_grid = grid or GridSpec(rows=2, columns=5)
    split = _split_sheet(image, resolved_grid)
    frame_results: list[FrameResult] = []
    cfg = frame_config or FramePipelineConfig()

    for offset, frame in enumerate(split.frames):
        output = process_frame_with_m3(
            frame.image,
            index=start_number + offset,
            row=frame.row,
            column=frame.column,
            extraction_rect=frame.box,
            extraction_method=split.method.value,
            extraction_confidence=split.confidence,
            config=cfg,
        )
        result = output.result
        if result.status in {FrameStatus.PASS, FrameStatus.AUTO_FIXED}:
            filename = f"{start_number + offset:02d}.png"
            artifact = export_png_atomic(
                output.image,
                target_dir / filename,
                allow_overwrite=allow_overwrite,
            )
            bind_export_artifact(result, artifact)
        frame_results.append(result)

    counts = {status: 0 for status in FrameStatus}
    for result in frame_results:
        counts[result.status] += 1

    report_path = target_dir / "report.json"
    report_payload = {
        "input_file": str(source),
        "input_size": [image.width, image.height],
        "extraction": {
            "method": split.method.value,
            "confidence": split.confidence,
            "frame_count": len(split.frames),
            "predicted_x_edges": split.predicted_x_edges,
            "refined_x_edges": split.refined_x_edges,
            "predicted_y_edges": split.predicted_y_edges,
            "refined_y_edges": split.refined_y_edges,
        },
        "frames": [_json_value(asdict(result)) for result in frame_results],
    }
    report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = SheetPipelineSummary(
        input_file=str(source),
        input_width=image.width,
        input_height=image.height,
        extraction_method=split.method.value,
        extraction_confidence=split.confidence,
        frame_count=len(frame_results),
        pass_count=counts[FrameStatus.PASS],
        auto_fixed_count=counts[FrameStatus.AUTO_FIXED],
        review_count=counts[FrameStatus.REVIEW],
        fail_count=counts[FrameStatus.FAIL],
        output_directory=str(target_dir),
        report_file=str(report_path),
    )
    return SheetPipelineOutput(summary=summary, frames=tuple(frame_results))
