from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from PIL import Image


class ExtractionMethod(StrEnum):
    CONFIGURED_EXACT = "configured_exact"
    CONFIGURED_SCALED = "configured_scaled"


@dataclass(frozen=True)
class GridSpec:
    rows: int = 2
    columns: int = 5
    margin_x: int = 0
    margin_y: int = 0
    gap_x: int = 0
    gap_y: int = 0


@dataclass(frozen=True)
class ExtractedFrame:
    index: int
    row: int
    column: int
    box: tuple[int, int, int, int]
    image: Image.Image


@dataclass(frozen=True)
class GridSplitResult:
    frames: tuple[ExtractedFrame, ...]
    method: ExtractionMethod
    confidence: float
    max_width_variation_px: int
    max_height_variation_px: int


def _validate_geometry(image: Image.Image, spec: GridSpec) -> tuple[int, int]:
    if spec.rows <= 0 or spec.columns <= 0:
        raise ValueError("rows and columns must be positive")
    if min(spec.margin_x, spec.margin_y, spec.gap_x, spec.gap_y) < 0:
        raise ValueError("grid margins/gaps must be non-negative")

    usable_width = image.width - (2 * spec.margin_x) - ((spec.columns - 1) * spec.gap_x)
    usable_height = image.height - (2 * spec.margin_y) - ((spec.rows - 1) * spec.gap_y)
    if usable_width <= 0 or usable_height <= 0:
        raise ValueError("grid margins/gaps exceed image size")
    return usable_width, usable_height


def split_grid(image: Image.Image, spec: GridSpec | None = None) -> list[ExtractedFrame]:
    """Split exact configured geometry.

    This strict function deliberately refuses fractional cell geometry so callers do
    not silently change extraction behavior. Use ``split_grid_scaled`` explicitly
    for resized/non-divisible sheets.
    """
    resolved_spec = spec or GridSpec()
    usable_width, usable_height = _validate_geometry(image, resolved_spec)
    if usable_width % resolved_spec.columns or usable_height % resolved_spec.rows:
        raise ValueError("sheet geometry does not divide evenly; hybrid refinement required")

    frame_width = usable_width // resolved_spec.columns
    frame_height = usable_height // resolved_spec.rows
    frames: list[ExtractedFrame] = []
    for row in range(resolved_spec.rows):
        for column in range(resolved_spec.columns):
            left = resolved_spec.margin_x + column * (frame_width + resolved_spec.gap_x)
            top = resolved_spec.margin_y + row * (frame_height + resolved_spec.gap_y)
            box = (left, top, left + frame_width, top + frame_height)
            frames.append(
                ExtractedFrame(
                    index=(row * resolved_spec.columns) + column + 1,
                    row=row,
                    column=column,
                    box=box,
                    image=image.crop(box),
                )
            )
    return frames


def split_grid_scaled(
    image: Image.Image,
    spec: GridSpec | None = None,
    *,
    max_cell_variation_px: int = 1,
) -> GridSplitResult:
    """Split a uniformly resized configured grid using proportional boundaries.

    This is a controlled fallback for known row/column layouts whose usable size no
    longer divides evenly after scaling. It does not claim to replace future visual
    separator refinement for genuinely ambiguous layouts.
    """
    resolved_spec = spec or GridSpec()
    if max_cell_variation_px < 0:
        raise ValueError("max_cell_variation_px must be non-negative")
    usable_width, usable_height = _validate_geometry(image, resolved_spec)

    if usable_width % resolved_spec.columns == 0 and usable_height % resolved_spec.rows == 0:
        frames = tuple(split_grid(image, resolved_spec))
        return GridSplitResult(
            frames=frames,
            method=ExtractionMethod.CONFIGURED_EXACT,
            confidence=1.0,
            max_width_variation_px=0,
            max_height_variation_px=0,
        )

    x_edges = [
        resolved_spec.margin_x + round((usable_width * i) / resolved_spec.columns) + (i * resolved_spec.gap_x)
        for i in range(resolved_spec.columns + 1)
    ]
    y_edges = [
        resolved_spec.margin_y + round((usable_height * i) / resolved_spec.rows) + (i * resolved_spec.gap_y)
        for i in range(resolved_spec.rows + 1)
    ]

    widths = [x_edges[i + 1] - x_edges[i] - (resolved_spec.gap_x if i < resolved_spec.columns - 1 else 0) for i in range(resolved_spec.columns)]
    heights = [y_edges[i + 1] - y_edges[i] - (resolved_spec.gap_y if i < resolved_spec.rows - 1 else 0) for i in range(resolved_spec.rows)]
    width_variation = max(widths) - min(widths)
    height_variation = max(heights) - min(heights)
    if width_variation > max_cell_variation_px or height_variation > max_cell_variation_px:
        raise ValueError("scaled grid variation exceeds configured safety limit")

    frames: list[ExtractedFrame] = []
    for row in range(resolved_spec.rows):
        for column in range(resolved_spec.columns):
            left = x_edges[column]
            right = x_edges[column + 1] - (resolved_spec.gap_x if column < resolved_spec.columns - 1 else 0)
            top = y_edges[row]
            bottom = y_edges[row + 1] - (resolved_spec.gap_y if row < resolved_spec.rows - 1 else 0)
            if right <= left or bottom <= top:
                raise ValueError("scaled grid produced invalid frame geometry")
            box = (left, top, right, bottom)
            frames.append(
                ExtractedFrame(
                    index=(row * resolved_spec.columns) + column + 1,
                    row=row,
                    column=column,
                    box=box,
                    image=image.crop(box),
                )
            )

    confidence = 0.97 if max(width_variation, height_variation) <= 1 else 0.90
    return GridSplitResult(
        frames=tuple(frames),
        method=ExtractionMethod.CONFIGURED_SCALED,
        confidence=confidence,
        max_width_variation_px=width_variation,
        max_height_variation_px=height_variation,
    )
