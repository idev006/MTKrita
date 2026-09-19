from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class ContentBounds:
    bbox: tuple[int, int, int, int] | None
    occupancy_ratio: float
    touches_edge: bool


def analyze_alpha_content(image: Image.Image, *, alpha_threshold: int = 8) -> ContentBounds:
    if not 0 <= alpha_threshold <= 255:
        raise ValueError("alpha_threshold must be between 0 and 255")

    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    mask = alpha.point(lambda value: 255 if value > alpha_threshold else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return ContentBounds(bbox=None, occupancy_ratio=0.0, touches_edge=False)

    left, top, right, bottom = bbox
    area = (right - left) * (bottom - top)
    canvas_area = rgba.width * rgba.height
    touches_edge = left == 0 or top == 0 or right == rgba.width or bottom == rgba.height
    return ContentBounds(
        bbox=bbox,
        occupancy_ratio=area / canvas_area,
        touches_edge=touches_edge,
    )
