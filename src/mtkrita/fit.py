from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from .content import analyze_alpha_content


@dataclass(frozen=True)
class FitResult:
    image: Image.Image
    scale: float
    offset: tuple[int, int]
    source_bbox: tuple[int, int, int, int] | None


def fit_rgba_to_canvas(
    image: Image.Image,
    target_size: tuple[int, int],
    *,
    margin: int = 10,
    allow_upscale: bool = False,
) -> FitResult:
    target_width, target_height = target_size
    if target_width <= 0 or target_height <= 0:
        raise ValueError("target dimensions must be positive")
    if margin < 0 or margin * 2 >= min(target_size):
        raise ValueError("invalid margin")

    rgba = image.convert("RGBA")
    analysis = analyze_alpha_content(rgba)
    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    if analysis.bbox is None:
        return FitResult(canvas, 1.0, (0, 0), None)

    crop = rgba.crop(analysis.bbox)
    available_width = target_width - (2 * margin)
    available_height = target_height - (2 * margin)
    scale = min(available_width / crop.width, available_height / crop.height)
    if not allow_upscale:
        scale = min(scale, 1.0)

    new_width = max(1, round(crop.width * scale))
    new_height = max(1, round(crop.height * scale))
    if (new_width, new_height) != crop.size:
        crop = crop.resize((new_width, new_height), Image.Resampling.LANCZOS)

    offset = ((target_width - new_width) // 2, (target_height - new_height) // 2)
    canvas.alpha_composite(crop, dest=offset)
    return FitResult(canvas, scale, offset, analysis.bbox)
