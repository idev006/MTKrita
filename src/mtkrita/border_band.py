from __future__ import annotations

from dataclasses import dataclass
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
class BorderBandCompletionPlan:
    status: BorderBandCompletionStatus
    proposed_inner_offsets: dict[str, int]
    side_layers: dict[str, tuple[BorderBandLayer, ...]]
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
) -> tuple[tuple[int, int], ...]:
    indexes = [
        index
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


def _side_length(image: Image.Image, side: str) -> int:
    return image.width if side in {"top", "bottom"} else image.height


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


def _candidate_sides(detection: BorderDetection) -> dict[str, BorderSide]:
    return {
        name: side
        for name in ("left", "top", "right", "bottom")
        if (side := getattr(detection, name)) is not None and side.contact_risk
    }


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
) -> BorderBandCompletionPlan:
    """Analyze decorative band continuation without mutating image or border authority."""
    if not 0 < max_fraction <= 0.5:
        raise ValueError("max_fraction must be in (0, 0.5]")
    if detection.requires_review or detection.consensus_mode not in {
        "single_tone",
        "multi_tone_four_side",
    }:
        return BorderBandCompletionPlan(
            status=BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION,
            proposed_inner_offsets={},
            side_layers={},
            corroboration_pattern=None,
            corroborating_sides=(),
            reasons=("border consensus is not eligible for Class-B completion",),
        )

    risky = _candidate_sides(detection)
    if not risky:
        return BorderBandCompletionPlan(
            status=BorderBandCompletionStatus.NOT_NEEDED,
            proposed_inner_offsets={},
            side_layers={},
            corroboration_pattern=None,
            corroborating_sides=(),
            reasons=("no residual border contact requires Class-B analysis",),
        )

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
        for name, side in risky.items()
    }
    side_layers = {
        name: tuple(candidate.layer for candidate in candidates)
        for name, candidates in collected.items()
        if candidates
    }

    if not side_layers:
        return BorderBandCompletionPlan(
            status=BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION,
            proposed_inner_offsets={},
            side_layers={},
            corroboration_pattern=None,
            corroborating_sides=(),
            reasons=("no bounded side-parallel decorative continuation was proven",),
        )

    names = tuple(side_layers)
    corroborating: set[str] = set()
    for index, first_name in enumerate(names):
        first_candidates = collected[first_name]
        for second_name in names[index + 1 :]:
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

    four_side = len(side_layers) == 4
    if four_side:
        deepest = [max(candidate.relative_depth for candidate in collected[name]) for name in names]
        four_side = max(deepest) - min(deepest) <= max_depth_spread

    if four_side:
        pattern = "four_side_ring"
        corroborating = set(names)
    elif len(corroborating) >= 2:
        pattern = "adjacent_side_layer"
    else:
        return BorderBandCompletionPlan(
            status=BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION,
            proposed_inner_offsets={},
            side_layers=side_layers,
            corroboration_pattern=None,
            corroborating_sides=(),
            reasons=("long side continuation lacks adjacent-side structural corroboration",),
        )

    proposed = {
        name: max(layer.offset for layer in layers) + 1
        for name, layers in side_layers.items()
        if name in corroborating
    }
    if any(offset > max_search for offset in proposed.values()):
        return BorderBandCompletionPlan(
            status=BorderBandCompletionStatus.REVIEW_SEARCH_BOUNDARY,
            proposed_inner_offsets=proposed,
            side_layers=side_layers,
            corroboration_pattern=pattern,
            corroborating_sides=tuple(sorted(corroborating)),
            reasons=("proposed completion exceeds the existing bounded search domain",),
        )

    return BorderBandCompletionPlan(
        status=BorderBandCompletionStatus.SAFE_COMPLETE,
        proposed_inner_offsets=proposed,
        side_layers=side_layers,
        corroboration_pattern=pattern,
        corroborating_sides=tuple(sorted(corroborating)),
        reasons=(
            "planner-only structural completion candidate; downstream completed-boundary "
            "contact validation is still required before cleanup authority",
        ),
    )
