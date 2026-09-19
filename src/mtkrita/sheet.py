from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


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


def split_grid(image: Image.Image, spec: GridSpec | None = None) -> list[ExtractedFrame]:
    resolved_spec = spec or GridSpec()
    if resolved_spec.rows <= 0 or resolved_spec.columns <= 0:
        raise ValueError("rows and columns must be positive")

    usable_width = (
        image.width
        - (2 * resolved_spec.margin_x)
        - ((resolved_spec.columns - 1) * resolved_spec.gap_x)
    )
    usable_height = (
        image.height
        - (2 * resolved_spec.margin_y)
        - ((resolved_spec.rows - 1) * resolved_spec.gap_y)
    )
    if usable_width <= 0 or usable_height <= 0:
        raise ValueError("grid margins/gaps exceed image size")
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
