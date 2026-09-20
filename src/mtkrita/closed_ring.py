from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256

import numpy as np
from PIL import Image

from .border import BorderDetection, BorderSide


class ClosedRingStatus(str, Enum):
    NO_RING = "NO_RING"
    SAFE_RING = "SAFE_RING"
    RING_WITH_CONTACT = "RING_WITH_CONTACT"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class RingTone:
    color: tuple[int, int, int]
    fraction: float


@dataclass(frozen=True)
class RingSideEvidence:
    side: str
    offset: int
    thickness: int
    line_support_min: float
    line_support_mean: float
    palette: tuple[RingTone, ...]
    palette_coverage: float
    raw_contact_fraction: float
    raw_contact_ranges: tuple[tuple[int, int], ...]
    explained_corner_ranges: tuple[tuple[int, int], ...]
    contact_fraction: float
    contact_ranges: tuple[tuple[int, int], ...]
    contact_risk: bool


@dataclass(frozen=True)
class ClosedRingPlan:
    status: ClosedRingStatus
    sides: dict[str, RingSideEvidence]
    mask: Image.Image | None
    mask_sha256: str | None
    ring_pixel_count: int
    ring_area_ratio: float
    thickness_spread: int | None
    reasons: tuple[str, ...]


def _distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return max(abs(a[index] - b[index]) for index in range(3))


def _side_line(array: np.ndarray, side: str, offset: int) -> np.ndarray:
    if side == "top":
        return array[offset, :, :]
    if side == "bottom":
        return array[-1 - offset, :, :]
    if side == "left":
        return array[:, offset, :]
    if side == "right":
        return array[:, -1 - offset, :]
    raise ValueError(f"unsupported side: {side}")


def _ranges(indexes: list[int]) -> tuple[tuple[int, int], ...]:
    if not indexes:
        return ()
    output: list[tuple[int, int]] = []
    start = previous = indexes[0]
    for index in indexes[1:]:
        if index == previous + 1:
            previous = index
            continue
        output.append((start, previous + 1))
        start = previous = index
    output.append((start, previous + 1))
    return tuple(output)


def _support_runs(values: list[float], threshold: float) -> tuple[tuple[int, int], ...]:
    output: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate([*values, 0.0]):
        if value >= threshold and start is None:
            start = index
        if value < threshold and start is not None:
            output.append((start, index))
            start = None
    return tuple(output)


def _overlaps_seed(run: tuple[int, int], side: BorderSide) -> bool:
    seed_start = side.offset
    seed_end = side.offset + side.thickness
    return run[0] < seed_end and run[1] > seed_start


def _palette(
    pixels: list[tuple[int, int, int]],
    *,
    quantization: int,
    min_fraction: float,
    max_tones: int,
) -> tuple[RingTone, ...]:
    if not pixels:
        return ()
    buckets: dict[tuple[int, int, int], list[tuple[int, int, int]]] = {}
    for pixel in pixels:
        key = tuple((channel // quantization) * quantization for channel in pixel)
        buckets.setdefault(key, []).append(pixel)

    tones: list[RingTone] = []
    for values in buckets.values():
        fraction = len(values) / len(pixels)
        if fraction < min_fraction:
            continue
        color = tuple(
            round(sum(value[channel] for value in values) / len(values))
            for channel in range(3)
        )
        tones.append(RingTone(color=color, fraction=fraction))
    tones.sort(key=lambda item: (-item.fraction, item.color))
    return tuple(tones[:max_tones])


def _matches_palette(
    pixel: tuple[int, int, int],
    palette: tuple[RingTone, ...],
    tolerance: int,
) -> bool:
    return any(_distance(pixel, tone.color) <= tolerance for tone in palette)


def _side_palette(
    rgba: np.ndarray,
    side: str,
    run: tuple[int, int],
    *,
    quantization: int,
    min_fraction: float,
    max_tones: int,
) -> tuple[tuple[RingTone, ...], float]:
    pixels: list[tuple[int, int, int]] = []
    for offset in range(run[0], run[1]):
        line = _side_line(rgba, side, offset)
        visible = line[line[:, 3] > 8, :3]
        pixels.extend(tuple(map(int, pixel)) for pixel in visible)
    palette = _palette(
        pixels,
        quantization=quantization,
        min_fraction=min_fraction,
        max_tones=max_tones,
    )
    if not pixels or not palette:
        return palette, 0.0
    matched = sum(_matches_palette(pixel, palette, 32) for pixel in pixels)
    return palette, matched / len(pixels)


def _inner_contact(
    rgba: np.ndarray,
    side: str,
    inner_offset: int,
    palette: tuple[RingTone, ...],
    *,
    color_tolerance: int,
) -> tuple[float, tuple[tuple[int, int], ...], int]:
    line = _side_line(rgba, side, inner_offset)
    trim = min(inner_offset, max(0, len(line) // 4))
    if trim and len(line) > 2 * trim:
        region = line[trim:-trim]
        origin = trim
    else:
        region = line
        origin = 0
    indexes = [
        origin + index
        for index, pixel in enumerate(region)
        if pixel[3] > 8
        and _matches_palette(tuple(map(int, pixel[:3])), palette, color_tolerance)
    ]
    contact_ranges = _ranges(indexes)
    count = sum(end - start for start, end in contact_ranges)
    fraction = count / len(region) if len(region) else 0.0
    return fraction, contact_ranges, len(region)


def _endpoint_ranges(
    ranges: tuple[tuple[int, int], ...],
    *,
    side_length: int,
    envelope: int,
    endpoint: str,
) -> tuple[tuple[int, int], ...]:
    if endpoint == "low":
        return tuple(interval for interval in ranges if interval[1] <= envelope)
    boundary = max(0, side_length - envelope)
    return tuple(interval for interval in ranges if interval[0] >= boundary)


def _explain_corner_contact(
    image: Image.Image,
    raw: dict[str, tuple[float, tuple[tuple[int, int], ...], int]],
    *,
    envelope: int,
    contact_fraction_threshold: float,
) -> dict[
    str,
    tuple[
        tuple[tuple[int, int], ...],
        float,
        tuple[tuple[int, int], ...],
        bool,
    ],
]:
    explained: dict[str, set[tuple[int, int]]] = {name: set() for name in raw}
    corners = (
        ("top", "low", "left", "low"),
        ("top", "high", "right", "low"),
        ("bottom", "low", "left", "high"),
        ("bottom", "high", "right", "high"),
    )
    for first_name, first_endpoint, second_name, second_endpoint in corners:
        if first_name not in raw or second_name not in raw:
            continue
        first_length = image.width if first_name in {"top", "bottom"} else image.height
        second_length = image.width if second_name in {"top", "bottom"} else image.height
        first_ranges = _endpoint_ranges(
            raw[first_name][1],
            side_length=first_length,
            envelope=envelope,
            endpoint=first_endpoint,
        )
        second_ranges = _endpoint_ranges(
            raw[second_name][1],
            side_length=second_length,
            envelope=envelope,
            endpoint=second_endpoint,
        )
        if first_ranges and second_ranges:
            explained[first_name].update(first_ranges)
            explained[second_name].update(second_ranges)

    output = {}
    for name, (_, ranges, sample_count) in raw.items():
        explained_ranges = tuple(interval for interval in ranges if interval in explained[name])
        residual_ranges = tuple(interval for interval in ranges if interval not in explained[name])
        residual_count = sum(end - start for start, end in residual_ranges)
        residual_fraction = residual_count / sample_count if sample_count else 0.0
        output[name] = (
            explained_ranges,
            residual_fraction,
            residual_ranges,
            residual_fraction >= contact_fraction_threshold,
        )
    return output


def _side_region(shape: tuple[int, int], side: str, run: tuple[int, int]) -> np.ndarray:
    height, width = shape
    region = np.zeros((height, width), dtype=bool)
    start, end = run
    if side == "top":
        region[start:end, :] = True
    elif side == "bottom":
        region[max(0, height - end) : max(0, height - start), :] = True
    elif side == "left":
        region[:, start:end] = True
    elif side == "right":
        region[:, max(0, width - end) : max(0, width - start)] = True
    return region


def plan_closed_ring(
    image: Image.Image,
    detection: BorderDetection,
    *,
    max_fraction: float = 0.12,
    min_line_support: float = 0.75,
    max_thickness_spread: int = 2,
    palette_quantization: int = 32,
    palette_min_fraction: float = 0.02,
    palette_max_tones: int = 8,
    min_palette_coverage: float = 0.95,
    color_tolerance: int = 32,
    contact_fraction_threshold: float = 0.05,
) -> ClosedRingPlan:
    """Plan a four-side transparent closed ring without mutating the source image."""
    if not 0 < max_fraction <= 0.5:
        raise ValueError("max_fraction must be in (0, 0.5]")
    if not 0 < min_line_support <= 1:
        raise ValueError("min_line_support must be in (0, 1]")
    if max_thickness_spread < 0:
        raise ValueError("max_thickness_spread must be non-negative")

    if detection.requires_review or detection.consensus_mode not in {
        "single_tone",
        "multi_tone_four_side",
    }:
        return ClosedRingPlan(
            ClosedRingStatus.NO_RING,
            {},
            None,
            None,
            0,
            0.0,
            None,
            ("border consensus is not eligible for closed-ring planning",),
        )

    detected = {
        name: side
        for name in ("left", "top", "right", "bottom")
        if (side := getattr(detection, name)) is not None
    }
    if len(detected) != 4:
        return ClosedRingPlan(
            ClosedRingStatus.NO_RING,
            {},
            None,
            None,
            0,
            0.0,
            None,
            ("closed-ring planning requires four authorized sides",),
        )

    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    max_search = max(1, int(min(image.size) * max_fraction))
    runs: dict[str, tuple[int, int]] = {}
    supports: dict[str, tuple[float, float]] = {}
    palettes: dict[str, tuple[RingTone, ...]] = {}
    palette_coverages: dict[str, float] = {}

    for name, side in detected.items():
        line_support = [
            float(np.mean(_side_line(rgba, name, offset)[:, 3] > 8))
            for offset in range(max_search)
        ]
        candidates = tuple(
            run
            for run in _support_runs(line_support, min_line_support)
            if _overlaps_seed(run, side)
        )
        if len(candidates) != 1:
            return ClosedRingPlan(
                ClosedRingStatus.REVIEW,
                {},
                None,
                None,
                0,
                0.0,
                None,
                (f"{name}: seed border does not map to one bounded alpha-support band",),
            )
        run = candidates[0]
        if run[1] >= max_search:
            return ClosedRingPlan(
                ClosedRingStatus.REVIEW,
                {},
                None,
                None,
                0,
                0.0,
                None,
                (f"{name}: alpha-support band reaches search-domain boundary",),
            )
        selected_support = line_support[run[0] : run[1]]
        palette, palette_coverage = _side_palette(
            rgba,
            name,
            run,
            quantization=palette_quantization,
            min_fraction=palette_min_fraction,
            max_tones=palette_max_tones,
        )
        if not palette or palette_coverage < min_palette_coverage:
            return ClosedRingPlan(
                ClosedRingStatus.REVIEW,
                {},
                None,
                None,
                0,
                0.0,
                None,
                (f"{name}: side-local ring palette does not cover the visible band",),
            )
        runs[name] = run
        supports[name] = (min(selected_support), sum(selected_support) / len(selected_support))
        palettes[name] = palette
        palette_coverages[name] = palette_coverage

    thicknesses = [end - start for start, end in runs.values()]
    thickness_spread = max(thicknesses) - min(thicknesses)
    if thickness_spread > max_thickness_spread:
        return ClosedRingPlan(
            ClosedRingStatus.REVIEW,
            {},
            None,
            None,
            0,
            0.0,
            thickness_spread,
            ("four-side alpha-support band thickness is incoherent",),
        )

    raw_contact: dict[str, tuple[float, tuple[tuple[int, int], ...], int]] = {}
    for name, run in runs.items():
        raw_contact[name] = _inner_contact(
            rgba,
            name,
            run[1],
            palettes[name],
            color_tolerance=color_tolerance,
        )
    resolved_contact = _explain_corner_contact(
        image,
        raw_contact,
        envelope=max_search,
        contact_fraction_threshold=contact_fraction_threshold,
    )

    sides: dict[str, RingSideEvidence] = {}
    for name, run in runs.items():
        raw_fraction, raw_ranges, _ = raw_contact[name]
        explained, residual_fraction, residual_ranges, risk = resolved_contact[name]
        sides[name] = RingSideEvidence(
            side=name,
            offset=run[0],
            thickness=run[1] - run[0],
            line_support_min=supports[name][0],
            line_support_mean=supports[name][1],
            palette=palettes[name],
            palette_coverage=palette_coverages[name],
            raw_contact_fraction=raw_fraction,
            raw_contact_ranges=raw_ranges,
            explained_corner_ranges=explained,
            contact_fraction=residual_fraction,
            contact_ranges=residual_ranges,
            contact_risk=risk,
        )

    height, width = rgba.shape[:2]
    ring = np.zeros((height, width), dtype=np.uint8)
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3]
    for name, run in runs.items():
        region = _side_region((height, width), name, run)
        match = np.zeros((height, width), dtype=bool)
        for tone in palettes[name]:
            target = np.asarray(tone.color, dtype=np.int16)
            distance = np.max(np.abs(rgb.astype(np.int16) - target), axis=2)
            match |= distance <= color_tolerance
        ring[region & (alpha > 8) & match] = 255

    ring_pixel_count = int(np.count_nonzero(ring))
    ring_area_ratio = ring_pixel_count / max(1, width * height)
    mask = Image.fromarray(ring)
    digest = sha256(ring.tobytes()).hexdigest()
    status = (
        ClosedRingStatus.RING_WITH_CONTACT
        if any(side.contact_risk for side in sides.values())
        else ClosedRingStatus.SAFE_RING
    )
    return ClosedRingPlan(
        status=status,
        sides=sides,
        mask=mask,
        mask_sha256=digest,
        ring_pixel_count=ring_pixel_count,
        ring_area_ratio=ring_area_ratio,
        thickness_spread=thickness_spread,
        reasons=("four-side alpha-support plateau forms a coherent side-local palette ring",),
    )
