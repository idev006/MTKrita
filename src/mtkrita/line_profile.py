from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class LineValidation:
    valid: bool
    findings: tuple[str, ...]


def validate_static_sticker(
    image: Image.Image,
    *,
    max_width: int = 370,
    max_height: int = 320,
    require_even_dimensions: bool = True,
    require_transparency: bool = True,
) -> LineValidation:
    findings: list[str] = []
    width, height = image.size

    if width > max_width or height > max_height:
        findings.append("DIMENSIONS_EXCEED_PROFILE")
    if require_even_dimensions and ((width % 2) or (height % 2)):
        findings.append("DIMENSIONS_NOT_EVEN")

    if require_transparency:
        rgba = image.convert("RGBA")
        alpha_min, alpha_max = rgba.getchannel("A").getextrema()
        if alpha_min == alpha_max == 255:
            findings.append("NO_TRANSPARENT_PIXELS")
        elif alpha_max == 0:
            findings.append("NO_VISIBLE_CONTENT")

    return LineValidation(valid=not findings, findings=tuple(findings))
