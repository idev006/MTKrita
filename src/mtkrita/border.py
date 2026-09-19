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
    contact_risk: bool = False


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
        values = [
            side.confidence
            for side in (self.left, self.top, self.right, self.bottom)
            if side is not None
        ]
        return mean(values) if values else 0.0

    @property
    def contact_risk(self) -> bool:
        return any(
            side is not None and side.contact_risk
            for side in (self.left, self.top, self.right, self.bottom)
        )


def _distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return max(abs(a[i] - b[i]) for i in range(3))


def _dominant_color(
    samples: list[tuple[int, int, int] | None], tolerance: int
) -> tuple[tuple[int, int, int], float]:
    visible = [sample for sample in samples if sample is not None]
    if not visible:
        return (0, 0, 0), 0.0

    buckets: dict[tuple[int, int, int], int] = {}
    quant = max(1, tolerance + 1)
    for pixel in visible:
        key = tuple((channel // quant) * quant for channel in pixel)
        buckets[key] = buckets.get(key, 0) + 1

    seed = max(buckets, key=buckets.get)
    matching = [pixel for pixel in visible if _distance(seed, pixel) <= tolerance]
    if not matching:
        return seed, 0.0

    color = tuple(round(sum(pixel[i] for pixel in matching) / len(matching)) for i in range(3))
    coverage = len(matching) / len(samples)
    return color, coverage


def _strip_samples(
    image: Image.Image, side: str, offset: int
) -> list[tuple[int, int, int] | None]:
    rgba = image.convert("RGBA")
    px = rgba.load()
    coords: list[tuple[int, int]]
    if side == "top":
        coords = [(x, offset) for x in range(rgba.width)]
    elif side == "bottom":
        y = rgba.height - 1 - offset
        coords = [(x, y) for x in range(rgba.width)]
    elif side == "left":
        coords = [(offset, y) for y in range(rgba.height)]
    else:
        x = rgba.width - 1 - offset
        coords = [(x, y) for y in range(rgba.height)]

    samples: list[tuple[int, int, int] | None] = []
    for x, y in coords:
        pixel = px[x, y]
        if pixel[3] <= 8:
            samples.append(None)
        else:
            samples.append((pixel[0], pixel[1], pixel[2]))
    return samples


def _matching_fraction(
    samples: list[tuple[int, int, int] | None],
    color: tuple[int, int, int],
    tolerance: int,
) -> float:
    if not samples:
        return 0.0
    matches = sum(
        sample is not None and _distance(sample, color) <= tolerance for sample in samples
    )
    return matches / len(samples)


def _detect_side(
    image: Image.Image,
    side: str,
    *,
    max_thickness: int,
    color_tolerance: int,
    min_coverage: float,
    contact_fraction_threshold: float,
) -> BorderSide | None:
    outer = _strip_samples(image, side, 0)
    outer_color, outer_coverage = _dominant_color(outer, color_tolerance)
    if outer_coverage < min_coverage:
        return None

    coverages: list[float] = []
    thickness = 0
    for offset in range(max_thickness):
        strip = _strip_samples(image, side, offset)
        color, coverage = _dominant_color(strip, color_tolerance)
        if coverage < min_coverage or _distance(color, outer_color) > color_tolerance:
            break
        thickness += 1
        coverages.append(coverage)

    if thickness == 0:
        return None

    inner = _strip_samples(image, side, thickness)
    trim = min(thickness, max(0, len(inner) // 4))
    if trim and len(inner) > 2 * trim:
        inner = inner[trim:-trim]
    contact_risk = (
        _matching_fraction(inner, outer_color, color_tolerance) >= contact_fraction_threshold
    )

    return BorderSide(
        side=side,
        thickness=thickness,
        color=outer_color,
        confidence=mean(coverages),
        contact_risk=contact_risk,
    )


def detect_border(
    image: Image.Image,
    *,
    max_fraction: float = 0.12,
    color_tolerance: int = 8,
    min_coverage: float = 0.985,
    contact_fraction_threshold: float = 0.05,
) -> BorderDetection:
    if not 0 < max_fraction <= 0.5:
        raise ValueError("max_fraction must be in (0, 0.5]")
    if not 0 <= color_tolerance <= 255:
        raise ValueError("color_tolerance must be between 0 and 255")
    if not 0 < min_coverage <= 1:
        raise ValueError("min_coverage must be in (0, 1]")
    if not 0 <= contact_fraction_threshold <= 1:
        raise ValueError("contact_fraction_threshold must be between 0 and 1")

    rgba = image.convert("RGBA")
    max_thickness = max(1, int(min(rgba.size) * max_fraction))
    shared = {
        "max_thickness": max_thickness,
        "color_tolerance": color_tolerance,
        "min_coverage": min_coverage,
        "contact_fraction_threshold": contact_fraction_threshold,
    }
    return BorderDetection(
        left=_detect_side(rgba, "left", **shared),
        top=_detect_side(rgba, "top", **shared),
        right=_detect_side(rgba, "right", **shared),
        bottom=_detect_side(rgba, "bottom", **shared),
    )


def remove_border(
    image: Image.Image,
    detection: BorderDetection,
    *,
    auto_threshold: float = 0.995,
) -> Image.Image:
    if detection.detected and detection.confidence < auto_threshold:
        raise ValueError("border confidence below automatic removal threshold")
    if detection.contact_risk:
        raise ValueError("border/artwork contact risk requires review")

    left = detection.left.thickness if detection.left else 0
    top = detection.top.thickness if detection.top else 0
    right = detection.right.thickness if detection.right else 0
    bottom = detection.bottom.thickness if detection.bottom else 0
    if left + right >= image.width or top + bottom >= image.height:
        raise ValueError("detected border consumes frame")
    return image.crop((left, top, image.width - right, image.height - bottom))
