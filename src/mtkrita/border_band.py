from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from PIL import Image

from .border import BorderDetection, BorderSide


class BorderBandCompletionStatus(str, Enum):
    NOT_NEEDED = "NOT_NEEDED"
    SAFE_COMPLETE = "SAFE_COMPLETE"
    REVIEW_INSUFFICIENT_CORROBORATION = "REVIEW_INSUFFICIENT_CORROBORATION"
    REVIEW_ARTWORK_CONTACT = "REVIEW_ARTWORK_CONTACT"
    REVIEW_GEOMETRY_CONFLICT = "REVIEW_GEOMETRY_CONFLICT"
    REVIEW_SEARCH_BOUNDARY = "REVIEW_SEARCH_BOUNDARY"


@dataclass(frozen=True)
class BorderBandLayer:
    side: str
    offset: int
    color: tuple[int, int, int]
    visible_support: float
    color_purity: float
    support_ranges: tuple[tuple[int, int], ...]
    longest_run_fraction: float
    endpoint_low: bool
    endpoint_high: bool


@dataclass(frozen=True)
class CompletedBoundaryContact:
    raw_fraction: float
    raw_ranges: tuple[tuple[int, int], ...]
    explained_corner_ranges: tuple[tuple[int, int], ...]
    fraction: float
    ranges: tuple[tuple[int, int], ...]
    contact_risk: bool
    sample_count: int


@dataclass(frozen=True)
class BorderBandCompletionPlan:
    status: BorderBandCompletionStatus
    trigger_sides: tuple[str, ...]
    proposed_inner_offsets: dict[str, int]
    side_layers: dict[str, tuple[BorderBandLayer, ...]]
    completed_inner_contact: dict[str, CompletedBoundaryContact]
    corroboration_pattern: str | None
    corroborating_sides: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class _LayerCandidate:
    layer: BorderBandLayer
    relative_depth: int


def _distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return max(abs(a[index] - b[index]) for index in range(3))


def _strip(image: Image.Image, side: str, offset: int) -> list[tuple[int, int, int] | None]:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    if side == "top":
        coords = [(x, offset) for x in range(rgba.width)]
    elif side == "bottom":
        y = rgba.height - 1 - offset
        coords = [(x, y) for x in range(rgba.width)]
    elif side == "left":
        coords = [(offset, y) for y in range(rgba.height)]
    elif side == "right":
        x = rgba.width - 1 - offset
        coords = [(x, y) for y in range(rgba.height)]
    else:
        raise ValueError(f"unsupported side: {side}")

    result: list[tuple[int, int, int] | None] = []
    for x, y in coords:
        red, green, blue, alpha = pixels[x, y]
        result.append(None if alpha <= 8 else (red, green, blue))
    return result


def _dominant_visible_color(
    samples: list[tuple[int, int, int] | None],
    tolerance: int,
) -> tuple[tuple[int, int, int], float, float]:
    visible = [sample for sample in samples if sample is not None]
    if not samples or not visible:
        return (0, 0, 0), 0.0, 0.0

    quant = max(1, tolerance + 1)
    buckets: dict[tuple[int, int, int], int] = {}
    for sample in visible:
        key = tuple((channel // quant) * quant for channel in sample)
        buckets[key] = buckets.get(key, 0) + 1
    seed = max(buckets, key=buckets.get)
    matching = [sample for sample in visible if _distance(seed, sample) <= tolerance]
    if not matching:
        return seed, len(visible) / len(samples), 0.0
    color = tuple(
        round(sum(sample[index] for sample in matching) / len(matching))
        for index in range(3)
    )
    visible_support = len(visible) / len(samples)
    purity = len(matching) / len(visible)
    return color, visible_support, purity


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


def _layer_candidate(
    image: Image.Image,
    side: str,
    offset: int,
    *,
    relative_depth: int,
    color_tolerance: int,
    min_visible_support: float,
    min_color_purity: float,
    min_longest_run_fraction: float,
    endpoint_envelope: int,
) -> _LayerCandidate | None:
    samples = _strip(image, side, offset)
    color, visible_support, color_purity = _dominant_visible_color(samples, color_tolerance)
    if visible_support < min_visible_support or color_purity < min_color_purity:
        return None
    ranges = _matching_ranges(samples, color, color_tolerance)
    side_length = len(samples)
    if not ranges or side_length <= 0:
        return None
    longest = max(end - start for start, end in ranges)
    longest_fraction = longest / side_length
    if longest_fraction < min_longest_run_fraction:
        return None
    endpoint_low = any(start < endpoint_envelope for start, _ in ranges)
    endpoint_high = any(end > side_length - endpoint_envelope for _, end in ranges)
    return _LayerCandidate(
        layer=BorderBandLayer(
            side=side,
            offset=offset,
            color=color,
            visible_support=visible_support,
            color_purity=color_purity,
            support_ranges=ranges,
            longest_run_fraction=longest_fraction,
            endpoint_low=endpoint_low,
            endpoint_high=endpoint_high,
        ),
        relative_depth=relative_depth,
    )


def _seed_inner_offset(side: BorderSide) -> int:
    return side.offset + side.thickness


def _collect_candidates(
    image: Image.Image,
    side: BorderSide,
    *,
    max_search: int,
    color_tolerance: int,
    min_visible_support: float,
    min_color_purity: float,
    min_longest_run_fraction: float,
) -> tuple[_LayerCandidate, ...]:
    start = _seed_inner_offset(side)
    endpoint_envelope = max_search
    candidates: list[_LayerCandidate] = []
    for offset in range(start, max_search):
        candidate = _layer_candidate(
            image,
            side.side,
            offset,
            relative_depth=(offset - start) + 1,
            color_tolerance=color_tolerance,
            min_visible_support=min_visible_support,
            min_color_purity=min_color_purity,
            min_longest_run_fraction=min_longest_run_fraction,
            endpoint_envelope=endpoint_envelope,
        )
        if candidate is None:
            break
        candidates.append(candidate)
    return tuple(candidates)


def _corner_endpoint(side: str, other: str) -> str | None:
    mapping = {
        ("top", "left"): "low",
        ("left", "top"): "low",
        ("top", "right"): "high",
        ("right", "top"): "low",
        ("bottom", "left"): "low",
        ("left", "bottom"): "high",
        ("bottom", "right"): "high",
        ("right", "bottom"): "high",
    }
    return mapping.get((side, other))


def _has_endpoint(layer: BorderBandLayer, endpoint: str) -> bool:
    return layer.endpoint_low if endpoint == "low" else layer.endpoint_high


def _adjacent_pair_corroborates(
    first: _LayerCandidate,
    second: _LayerCandidate,
    *,
    depth_spread: int,
) -> bool:
    first_endpoint = _corner_endpoint(first.layer.side, second.layer.side)
    second_endpoint = _corner_endpoint(second.layer.side, first.layer.side)
    if first_endpoint is None or second_endpoint is None:
        return False
    if abs(first.relative_depth - second.relative_depth) > depth_spread:
        return False
    return _has_endpoint(first.layer, first_endpoint) and _has_endpoint(
        second.layer, second_endpoint
    )


def _authorized_sides(detection: BorderDetection) -> dict[str, BorderSide]:
    return {
        name: side
        for name in ("left", "top", "right", "bottom")
        if (side := getattr(detection, name)) is not None
    }


def _trigger_sides(detection: BorderDetection) -> dict[str, BorderSide]:
    return {
        name: side
        for name, side in _authorized_sides(detection).items()
        if side.contact_risk
    }


def _completed_contact(
    image: Image.Image,
    side: str,
    offset: int,
    color: tuple[int, int, int],
    *,
    tolerance: int,
    threshold: float,
) -> CompletedBoundaryContact:
    samples = _strip(image, side, offset)
    trim = min(offset, max(0, len(samples) // 4))
    if trim and len(samples) > 2 * trim:
        region = samples[trim:-trim]
        origin = trim
    else:
        region = samples
        origin = 0
    raw_ranges = _matching_ranges(region, color, tolerance, origin=origin)
    raw_match_count = sum(end - start for start, end in raw_ranges)
    sample_count = len(region)
    raw_fraction = raw_match_count / sample_count if sample_count else 0.0
    return CompletedBoundaryContact(
        raw_fraction=raw_fraction,
        raw_ranges=raw_ranges,
        explained_corner_ranges=(),
        fraction=raw_fraction,
        ranges=raw_ranges,
        contact_risk=raw_fraction >= threshold,
        sample_count=sample_count,
    )


def _endpoint_ranges(
    ranges: tuple[tuple[int, int], ...],
    *,
    side_length: int,
    max_search: int,
    endpoint: str,
) -> tuple[tuple[int, int], ...]:
    if endpoint == "low":
        return tuple(interval for interval in ranges if interval[1] <= max_search)
    boundary = max(0, side_length - max_search)
    return tuple(interval for interval in ranges if interval[0] >= boundary)


def _resolve_completed_corner_contact(
    image: Image.Image,
    completed: dict[str, CompletedBoundaryContact],
    *,
    max_search: int,
    threshold: float,
) -> dict[str, CompletedBoundaryContact]:
    explained: dict[str, set[tuple[int, int]]] = {name: set() for name in completed}
    corners = (
        ("top", "low", "left", "low"),
        ("top", "high", "right", "low"),
        ("bottom", "low", "left", "high"),
        ("bottom", "high", "right", "high"),
    )
    for first_name, first_endpoint, second_name, second_endpoint in corners:
        first = completed.get(first_name)
        second = completed.get(second_name)
        if first is None or second is None:
            continue
        first_length = image.width if first_name in {"top", "bottom"} else image.height
        second_length = image.width if second_name in {"top", "bottom"} else image.height
        first_ranges = _endpoint_ranges(
            first.raw_ranges,
            side_length=first_length,
            max_search=max_search,
            endpoint=first_endpoint,
        )
        second_ranges = _endpoint_ranges(
            second.raw_ranges,
            side_length=second_length,
            max_search=max_search,
            endpoint=second_endpoint,
        )
        if not first_ranges or not second_ranges:
            continue
        explained[first_name].update(first_ranges)
        explained[second_name].update(second_ranges)

    resolved: dict[str, CompletedBoundaryContact] = {}
    for name, contact in completed.items():
        explained_ranges = tuple(
            interval for interval in contact.raw_ranges if interval in explained[name]
        )
        residual_ranges = tuple(
            interval for interval in contact.raw_ranges if interval not in explained[name]
        )
        residual_count = sum(end - start for start, end in residual_ranges)
        fraction = residual_count / contact.sample_count if contact.sample_count else 0.0
        resolved[name] = replace(
            contact,
            explained_corner_ranges=explained_ranges,
            fraction=fraction,
            ranges=residual_ranges,
            contact_risk=fraction >= threshold,
        )
    return resolved


def _empty_plan(
    status: BorderBandCompletionStatus,
    reason: str,
    *,
    trigger_sides: tuple[str, ...] = (),
) -> BorderBandCompletionPlan:
    return BorderBandCompletionPlan(
        status=status,
        trigger_sides=trigger_sides,
        proposed_inner_offsets={},
        side_layers={},
        completed_inner_contact={},
        corroboration_pattern=None,
        corroborating_sides=(),
        reasons=(reason,),
    )


def plan_border_band_completion(
    image: Image.Image,
    detection: BorderDetection,
    *,
    max_fraction: float = 0.12,
    color_tolerance: int = 24,
    min_visible_support: float = 0.60,
    min_color_purity: float = 0.90,
    min_longest_run_fraction: float = 0.20,
    max_depth_spread: int = 2,
    contact_fraction_threshold: float = 0.05,
) -> BorderBandCompletionPlan:
    """Analyze decorative band continuation without mutating image or border authority."""
    if not 0 < max_fraction <= 0.5:
        raise ValueError("max_fraction must be in (0, 0.5]")
    if not 0 <= contact_fraction_threshold <= 1:
        raise ValueError("contact_fraction_threshold must be between 0 and 1")
    if detection.requires_review or detection.consensus_mode not in {
        "single_tone",
        "multi_tone_four_side",
    }:
        return _empty_plan(
            BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION,
            "border consensus is not eligible for Class-B completion",
        )

    triggers = _trigger_sides(detection)
    trigger_names = tuple(sorted(triggers))
    if not triggers:
        return _empty_plan(
            BorderBandCompletionStatus.NOT_NEEDED,
            "no residual border contact requires Class-B analysis",
        )

    authorized = _authorized_sides(detection)
    max_search = max(1, int(min(image.size) * max_fraction))
    collected = {
        name: _collect_candidates(
            image,
            side,
            max_search=max_search,
            color_tolerance=color_tolerance,
            min_visible_support=min_visible_support,
            min_color_purity=min_color_purity,
            min_longest_run_fraction=min_longest_run_fraction,
        )
        for name, side in authorized.items()
    }
    side_layers = {
        name: tuple(candidate.layer for candidate in candidates)
        for name, candidates in collected.items()
        if candidates
    }

    if not side_layers:
        return _empty_plan(
            BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION,
            "no bounded side-parallel decorative continuation was proven",
            trigger_sides=trigger_names,
        )

    names = tuple(side_layers)
    corroborating: set[str] = set()
    for index, first_name in enumerate(names):
        first_candidates = collected[first_name]
        for second_name in names[index + 1 :]:
            if first_name not in triggers and second_name not in triggers:
                continue
            second_candidates = collected[second_name]
            if any(
                _adjacent_pair_corroborates(
                    first,
                    second,
                    depth_spread=max_depth_spread,
                )
                for first in first_candidates
                for second in second_candidates
            ):
                corroborating.update((first_name, second_name))

    if len(side_layers) == 4:
        deepest = [max(candidate.relative_depth for candidate in collected[name]) for name in names]
        if max(deepest) - min(deepest) > max_depth_spread:
            return BorderBandCompletionPlan(
                status=BorderBandCompletionStatus.REVIEW_GEOMETRY_CONFLICT,
                trigger_sides=trigger_names,
                proposed_inner_offsets={},
                side_layers=side_layers,
                completed_inner_contact={},
                corroboration_pattern=None,
                corroborating_sides=(),
                reasons=("four-side proposed band depth is geometrically incoherent",),
            )
        pattern = "four_side_ring"
        corroborating = set(names)
    elif len(corroborating) >= 2:
        pattern = "adjacent_side_layer"
    else:
        return BorderBandCompletionPlan(
            status=BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION,
            trigger_sides=trigger_names,
            proposed_inner_offsets={},
            side_layers=side_layers,
            completed_inner_contact={},
            corroboration_pattern=None,
            corroborating_sides=(),
            reasons=("long side continuation lacks adjacent-side structural corroboration",),
        )

    proposed = {
        name: max(layer.offset for layer in layers) + 1
        for name, layers in side_layers.items()
        if name in corroborating
    }
    if any(offset >= max_search for offset in proposed.values()):
        return BorderBandCompletionPlan(
            status=BorderBandCompletionStatus.REVIEW_SEARCH_BOUNDARY,
            trigger_sides=trigger_names,
            proposed_inner_offsets=proposed,
            side_layers=side_layers,
            completed_inner_contact={},
            corroboration_pattern=pattern,
            corroborating_sides=tuple(sorted(corroborating)),
            reasons=("proposed completion reaches the bounded search-domain limit",),
        )

    completed: dict[str, CompletedBoundaryContact] = {}
    for name, offset in proposed.items():
        last_layer = side_layers[name][-1]
        completed[name] = _completed_contact(
            image,
            name,
            offset,
            last_layer.color,
            tolerance=max(32, color_tolerance),
            threshold=contact_fraction_threshold,
        )
    completed = _resolve_completed_corner_contact(
        image,
        completed,
        max_search=max_search,
        threshold=contact_fraction_threshold,
    )
    if any(contact.contact_risk for contact in completed.values()):
        return BorderBandCompletionPlan(
            status=BorderBandCompletionStatus.REVIEW_ARTWORK_CONTACT,
            trigger_sides=trigger_names,
            proposed_inner_offsets=proposed,
            side_layers=side_layers,
            completed_inner_contact=completed,
            corroboration_pattern=pattern,
            corroborating_sides=tuple(sorted(corroborating)),
            reasons=("completed inner boundary retains unexplained contact",),
        )

    return BorderBandCompletionPlan(
        status=BorderBandCompletionStatus.SAFE_COMPLETE,
        trigger_sides=trigger_names,
        proposed_inner_offsets=proposed,
        side_layers=side_layers,
        completed_inner_contact=completed,
        corroboration_pattern=pattern,
        corroborating_sides=tuple(sorted(corroborating)),
        reasons=("completed band is structurally corroborated and its inner boundary is clean",),
    )
