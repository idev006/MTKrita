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
    offset: int = 0
    contact_fraction: float = 0.0
    contact_ranges: tuple[tuple[int, int], ...] = ()
    visible_support: float = 1.0
    color_purity: float = 1.0


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


@dataclass(frozen=True)
class _InsetCandidate:
    side: str
    offset: int
    color: tuple[int, int, int]
    coverage: float
    visible_fraction: float
    color_purity: float


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


def _side_depth(image: Image.Image, side: str) -> int:
    return image.height if side in {"top", "bottom"} else image.width


def _visible_fraction(samples: list[tuple[int, int, int] | None]) -> float:
    if not samples:
        return 0.0
    return sum(sample is not None for sample in samples) / len(samples)


def _visible_color_purity(coverage: float, visible_fraction: float) -> float:
    if visible_fraction <= 0:
        return 0.0
    return min(1.0, coverage / visible_fraction)


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


def _matching_ranges(
    samples: list[tuple[int, int, int] | None],
    color: tuple[int, int, int],
    tolerance: int,
    *,
    origin: int = 0,
) -> tuple[tuple[int, int], ...]:
    indexes = [
        origin + index
        for index, sample in enumerate(samples)
        if sample is not None and _distance(sample, color) <= tolerance
    ]
    if not indexes:
        return ()

    ranges: list[tuple[int, int]] = []
    start = indexes[0]
    previous = indexes[0]
    for index in indexes[1:]:
        if index == previous + 1:
            previous = index
            continue
        ranges.append((start, previous + 1))
        start = index
        previous = index
    ranges.append((start, previous + 1))
    return tuple(ranges)


def _contact_evidence(
    samples: list[tuple[int, int, int] | None],
    color: tuple[int, int, int],
    tolerance: int,
    *,
    trim: int,
) -> tuple[float, tuple[tuple[int, int], ...]]:
    if trim and len(samples) > 2 * trim:
        region = samples[trim:-trim]
        origin = trim
    else:
        region = samples
        origin = 0
    return (
        _matching_fraction(region, color, tolerance),
        _matching_ranges(region, color, tolerance, origin=origin),
    )


def _detect_edge_side(
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
    contact_fraction, contact_ranges = _contact_evidence(
        inner,
        outer_color,
        color_tolerance,
        trim=trim,
    )
    visible_support = _visible_fraction(outer)
    color_purity = _visible_color_purity(outer_coverage, visible_support)

    return BorderSide(
        side=side,
        thickness=thickness,
        color=outer_color,
        confidence=mean(coverages),
        contact_risk=contact_fraction >= contact_fraction_threshold,
        offset=0,
        contact_fraction=contact_fraction,
        contact_ranges=contact_ranges,
        visible_support=visible_support,
        color_purity=color_purity,
    )


def _find_inset_candidate(
    image: Image.Image,
    side: str,
    *,
    max_search: int,
    search_tolerance: int,
    min_visible_fraction: float,
    min_candidate_coverage: float,
) -> _InsetCandidate | None:
    candidates: list[_InsetCandidate] = []
    for offset in range(1, max_search):
        strip = _strip_samples(image, side, offset)
        visible = _visible_fraction(strip)
        color, coverage = _dominant_color(strip, search_tolerance)
        purity = _visible_color_purity(coverage, visible)
        if visible < min_visible_fraction or coverage < min_candidate_coverage:
            continue
        candidates.append(
            _InsetCandidate(
                side=side,
                offset=offset,
                color=color,
                coverage=coverage,
                visible_fraction=visible,
                color_purity=purity,
            )
        )
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (
            item.color_purity,
            item.coverage,
            item.visible_fraction,
            -item.offset,
        ),
    )


def _consensus_candidates(
    candidates: dict[str, _InsetCandidate],
    *,
    consensus_tolerance: int,
) -> dict[str, _InsetCandidate]:
    if len(candidates) < 3:
        return {}

    ranked: list[tuple[int, float, dict[str, _InsetCandidate]]] = []
    for seed in candidates.values():
        matched = {
            side: candidate
            for side, candidate in candidates.items()
            if _distance(seed.color, candidate.color) <= consensus_tolerance
        }
        ranked.append(
            (
                len(matched),
                sum(candidate.color_purity for candidate in matched.values()),
                matched,
            )
        )
    side_count, _, best = max(ranked, key=lambda item: (item[0], item[1]))
    return best if side_count >= 3 else {}


def _offset_group_nearest_peak(offsets: list[int], peak: int) -> list[int]:
    if not offsets:
        return []
    groups: list[list[int]] = []
    current = [offsets[0]]
    for offset in offsets[1:]:
        if offset - current[-1] <= 2:
            current.append(offset)
        else:
            groups.append(current)
            current = [offset]
    groups.append(current)
    return min(groups, key=lambda group: min(abs(value - peak) for value in group))


def _build_inset_side(
    image: Image.Image,
    candidate: _InsetCandidate,
    *,
    max_search: int,
    search_tolerance: int,
    contact_fraction_threshold: float,
    consensus_side_count: int,
) -> BorderSide | None:
    matching_offsets: list[int] = []
    for offset in range(max_search):
        strip = _strip_samples(image, candidate.side, offset)
        if _visible_fraction(strip) < 0.60:
            continue
        if _matching_fraction(strip, candidate.color, search_tolerance) >= 0.45:
            matching_offsets.append(offset)

    group = _offset_group_nearest_peak(matching_offsets, candidate.offset)
    if not group:
        return None
    start = min(group)
    end = max(group)
    thickness = (end - start) + 1

    inner_offset = end + 1
    inner = (
        _strip_samples(image, candidate.side, inner_offset)
        if inner_offset < _side_depth(image, candidate.side)
        else []
    )
    corner_trim = start + thickness
    trim = min(corner_trim, max(0, len(inner) // 4))
    contact_tolerance = max(32, search_tolerance)
    contact_fraction, contact_ranges = _contact_evidence(
        inner,
        candidate.color,
        contact_tolerance,
        trim=trim,
    )

    support_score = min(1.0, candidate.visible_fraction / 0.85)
    consensus_bonus = 0.15 if consensus_side_count == 4 else 0.05
    structural_confidence = (
        (0.75 * candidate.color_purity) + (0.25 * support_score) + consensus_bonus
    )
    confidence = min(1.0, structural_confidence)

    return BorderSide(
        side=candidate.side,
        thickness=thickness,
        color=candidate.color,
        confidence=confidence,
        contact_risk=contact_fraction >= contact_fraction_threshold,
        offset=start,
        contact_fraction=contact_fraction,
        contact_ranges=contact_ranges,
        visible_support=candidate.visible_fraction,
        color_purity=candidate.color_purity,
    )


def _detect_inset_sides(
    image: Image.Image,
    *,
    max_search: int,
    color_tolerance: int,
    contact_fraction_threshold: float,
) -> dict[str, BorderSide]:
    search_tolerance = max(24, color_tolerance * 3)
    candidates = {
        side: candidate
        for side in ("left", "top", "right", "bottom")
        if (
            candidate := _find_inset_candidate(
                image,
                side,
                max_search=max_search,
                search_tolerance=search_tolerance,
                min_visible_fraction=0.75,
                min_candidate_coverage=0.70,
            )
        )
        is not None
    }
    consensus = _consensus_candidates(candidates, consensus_tolerance=48)
    if not consensus:
        return {}

    side_count = len(consensus)
    detected: dict[str, BorderSide] = {}
    for side, candidate in consensus.items():
        result = _build_inset_side(
            image,
            candidate,
            max_search=max_search,
            search_tolerance=search_tolerance,
            contact_fraction_threshold=contact_fraction_threshold,
            consensus_side_count=side_count,
        )
        if result is not None:
            detected[side] = result
    return detected


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
    edge = {
        side: _detect_edge_side(rgba, side, **shared)
        for side in ("left", "top", "right", "bottom")
    }
    if any(edge.values()):
        return BorderDetection(
            left=edge["left"],
            top=edge["top"],
            right=edge["right"],
            bottom=edge["bottom"],
        )

    inset = _detect_inset_sides(
        rgba,
        max_search=max_thickness,
        color_tolerance=color_tolerance,
        contact_fraction_threshold=contact_fraction_threshold,
    )
    return BorderDetection(
        left=inset.get("left"),
        top=inset.get("top"),
        right=inset.get("right"),
        bottom=inset.get("bottom"),
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

    left = detection.left.offset + detection.left.thickness if detection.left else 0
    top = detection.top.offset + detection.top.thickness if detection.top else 0
    right = detection.right.offset + detection.right.thickness if detection.right else 0
    bottom = detection.bottom.offset + detection.bottom.thickness if detection.bottom else 0
    if left + right >= image.width or top + bottom >= image.height:
        raise ValueError("detected border consumes frame")
    return image.crop((left, top, image.width - right, image.height - bottom))
