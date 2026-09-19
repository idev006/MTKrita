from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from PIL import Image


@dataclass(frozen=True)
class BorderSide:
    side: str
    thickness: int
    color: tuple[int, int, int]
    confidence: float


@dataclass(frozen=True)
class BorderDetection:
    left: BorderSide | None
    top: BorderSide | None
    right: BorderSide | None
    bottom: BorderSide | None

    @property
    def detected(self) -> bool:
        return any((self.left, self.top, self.right, self.bottom))

    @property
    def confidence(self) -> float:
        values = [s.confidence for s in (self.left, self.top, self.right, self.bottom) if s]
        return mean(values) if values else 0.0


def _rgb(pixel: tuple[int, ...] | int) -> tuple[int, int, int]:
    if isinstance(pixel, int):
        return (pixel, pixel, pixel)
    if len(pixel) >= 3:
        return (int(pixel[0]), int(pixel[1]), int(pixel[2]))
    return (int(pixel[0]), int(pixel[0]), int(pixel[0]))


def _distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return max(abs(a[i] - b[i]) for i in range(3))


def _dominant_color(pixels: list[tuple[int, int, int]], tolerance: int) -> tuple[tuple[int, int, int], float]:
    if not pixels:
        return (0, 0, 0), 0.0
    best_color = pixels[0]
    best_count = 0
    for candidate in pixels:
        count = sum(_distance(candidate, p) <= tolerance for p in pixels)
        if count > best_count:
            best_color = candidate
            best_count = count
    return best_color, best_count / len(pixels)


def _strip_pixels(image: Image.Image, side: str, offset: int) -> list[tuple[int, int, int]]:
    px = image.load()
    if side == "top":
        return [_rgb(px[x, offset]) for x in range(image.width)]
    if side == "bottom":
        y = image.height - 1 - offset
        return [_rgb(px[x, y]) for x in range(image.width)]
    if side == "left":
        return [_rgb(px[offset, y]) for y in range(image.height)]
    x = image.width - 1 - offset
    return [_rgb(px[x, y]) for y in range(image.height)]


def _detect_side(
    image: Image.Image,
    side: str,
    *,
    max_thickness: int,
    color_tolerance: int,
    min_coverage: float,
) -> BorderSide | None:
    outer_color, outer_coverage = _dominant_color(_strip_pixels(image, side, 0), color_tolerance)
    if outer_coverage < min_coverage:
        return None

    coverages: list[float] = []
    thickness = 0
    for offset in range(max_thickness):
        color, coverage = _dominant_color(_strip_pixels(image, side, offset), color_tolerance)
        if coverage < min_coverage or _distance(color, outer_color) > color_tolerance:
            break
        thickness += 1
        coverages.append(coverage)

    if thickness == 0:
        return None
    return BorderSide(side=side, thickness=thickness, color=outer_color, confidence=mean(coverages))


def detect_border(
    image: Image.Image,
    *,
    max_fraction: float = 0.12,
    color_tolerance: int = 8,
    min_coverage: float = 0.985,
) -> BorderDetection:
    if not 0 < max_fraction <= 0.5:
        raise ValueError("max_fraction must be in (0, 0.5]")
    rgba = image.convert("RGBA")
    max_thickness = max(1, int(min(rgba.size) * max_fraction))
    return BorderDetection(
        left=_detect_side(rgba, "left", max_thickness=max_thickness, color_tolerance=color_tolerance, min_coverage=min_coverage),
        top=_detect_side(rgba, "top", max_thickness=max_thickness, color_tolerance=color_tolerance, min_coverage=min_coverage),
        right=_detect_side(rgba, "right", max_thickness=max_thickness, color_tolerance=color_tolerance, min_coverage=min_coverage),
        bottom=_detect_side(rgba, "bottom", max_thickness=max_thickness, color_tolerance=color_tolerance, min_coverage=min_coverage),
    )


def remove_border(
    image: Image.Image,
    detection: BorderDetection,
    *,
    auto_threshold: float = 0.995,
) -> Image.Image:
    if detection.detected and detection.confidence < auto_threshold:
        raise ValueError("border confidence below automatic removal threshold")

    left = detection.left.thickness if detection.left else 0
    top = detection.top.thickness if detection.top else 0
    right = detection.right.thickness if detection.right else 0
    bottom = detection.bottom.thickness if detection.bottom else 0

    if left + right >= image.width or top + bottom >= image.height:
        raise ValueError("detected border consumes frame")
    return image.crop((left, top, image.width - right, image.height - bottom))
