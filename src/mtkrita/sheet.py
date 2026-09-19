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


def split_grid(image: Image.Image, spec: GridSpec = GridSpec()) -> list[ExtractedFrame]:
    if spec.rows <= 0 or spec.columns <= 0:
        raise ValueError("rows and columns must be positive")

    usable_width = image.width - (2 * spec.margin_x) - ((spec.columns - 1) * spec.gap_x)
    usable_height = image.height - (2 * spec.margin_y) - ((spec.rows - 1) * spec.gap_y)
    if usable_width <= 0 or usable_height <= 0:
        raise ValueError("grid margins/gaps exceed image size")
    if usable_width % spec.columns or usable_height % spec.rows:
        raise ValueError("sheet geometry does not divide evenly; hybrid refinement required")

    frame_width = usable_width // spec.columns
    frame_height = usable_height // spec.rows
    frames: list[ExtractedFrame] = []

    for row in range(spec.rows):
        for column in range(spec.columns):
            left = spec.margin_x + column * (frame_width + spec.gap_x)
            top = spec.margin_y + row * (frame_height + spec.gap_y)
            box = (left, top, left + frame_width, top + frame_height)
            frames.append(
                ExtractedFrame(
                    index=(row * spec.columns) + column + 1,
                    row=row,
                    column=column,
                    box=box,
                    image=image.crop(box),
                )
            )
    return frames
