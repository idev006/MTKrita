from __future__ import annotations

from dataclasses import dataclass, replace

from PIL import Image

from .border import BorderDetection, BorderSide


@dataclass(frozen=True)
class SideContactTopology:
    raw_contact_fraction: float
    raw_contact_ranges: tuple[tuple[int, int], ...]
    explained_corner_ranges: tuple[tuple[int, int], ...]
    residual_contact_fraction: float
    residual_contact_ranges: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class BorderContactTopology:
    detection: BorderDetection
    sides: dict[str, SideContactTopology]


def _side_length(image: Image.Image, side: str) -> int:
    return image.width if side in {"top", "bottom"} else image.height


def _sample_count(image: Image.Image, side: BorderSide) -> int:
    length = _side_length(image, side.side)
    trim = min(side.offset + side.thickness, max(0, length // 4))
    if trim and length > 2 * trim:
        return length - (2 * trim)
    return length


def _range_length(interval: tuple[int, int]) -> int:
    return max(0, interval[1] - interval[0])


def _endpoint_ranges(
    ranges: tuple[tuple[int, int], ...],
    *,
    side_length: int,
    max_search: int,
    endpoint: str,
) -> tuple[tuple[int, int], ...]:
    if endpoint == "low":
        return tuple(
            interval
            for interval in ranges
            if interval[0] >= 0 and interval[1] <= max_search
        )
    boundary = max(0, side_length - max_search)
    return tuple(
        interval
        for interval in ranges
        if interval[0] >= boundary and interval[1] <= side_length
    )


def _unchanged_side_evidence(side: BorderSide) -> SideContactTopology:
    return SideContactTopology(
        raw_contact_fraction=side.contact_fraction,
        raw_contact_ranges=side.contact_ranges,
        explained_corner_ranges=(),
        residual_contact_fraction=side.contact_fraction,
        residual_contact_ranges=side.contact_ranges,
    )


def resolve_reciprocal_corner_contact(
    image: Image.Image,
    detection: BorderDetection,
    *,
    max_fraction: float = 0.12,
    contact_fraction_threshold: float = 0.05,
) -> BorderContactTopology:
    """Explain only reciprocal inset-corner continuation and preserve residual risk."""
    if not 0 < max_fraction <= 0.5:
        raise ValueError("max_fraction must be in (0, 0.5]")
    if not 0 <= contact_fraction_threshold <= 1:
        raise ValueError("contact_fraction_threshold must be between 0 and 1")

    side_names = ("left", "top", "right", "bottom")
    original = {
        name: side
        for name in side_names
        if (side := getattr(detection, name)) is not None
    }
    evidence = {name: _unchanged_side_evidence(side) for name, side in original.items()}

    if (
        detection.requires_review
        or detection.consensus_mode not in {"single_tone", "multi_tone_four_side"}
        or len(original) < 2
    ):
        return BorderContactTopology(detection=detection, sides=evidence)

    max_search = max(1, int(min(image.size) * max_fraction))
    explained: dict[str, set[tuple[int, int]]] = {name: set() for name in original}
    corners = (
        ("top", "low", "left", "low"),
        ("top", "high", "right", "low"),
        ("bottom", "low", "left", "high"),
        ("bottom", "high", "right", "high"),
    )

    for first_name, first_endpoint, second_name, second_endpoint in corners:
        first = original.get(first_name)
        second = original.get(second_name)
        if first is None or second is None:
            continue
        first_ranges = _endpoint_ranges(
            first.contact_ranges,
            side_length=_side_length(image, first_name),
            max_search=max_search,
            endpoint=first_endpoint,
        )
        second_ranges = _endpoint_ranges(
            second.contact_ranges,
            side_length=_side_length(image, second_name),
            max_search=max_search,
            endpoint=second_endpoint,
        )
        if not first_ranges or not second_ranges:
            continue
        explained[first_name].update(first_ranges)
        explained[second_name].update(second_ranges)

    resolved: dict[str, BorderSide] = {}
    topology: dict[str, SideContactTopology] = {}
    for name, side in original.items():
        explained_ranges = tuple(
            interval for interval in side.contact_ranges if interval in explained[name]
        )
        residual_ranges = tuple(
            interval for interval in side.contact_ranges if interval not in explained[name]
        )
        sample_count = _sample_count(image, side)
        residual_match_count = sum(_range_length(interval) for interval in residual_ranges)
        residual_fraction = residual_match_count / sample_count if sample_count else 0.0
        resolved[name] = replace(
            side,
            contact_risk=residual_fraction >= contact_fraction_threshold,
            contact_fraction=residual_fraction,
            contact_ranges=residual_ranges,
        )
        topology[name] = SideContactTopology(
            raw_contact_fraction=side.contact_fraction,
            raw_contact_ranges=side.contact_ranges,
            explained_corner_ranges=explained_ranges,
            residual_contact_fraction=residual_fraction,
            residual_contact_ranges=residual_ranges,
        )

    resolved_detection = replace(
        detection,
        left=resolved.get("left"),
        top=resolved.get("top"),
        right=resolved.get("right"),
        bottom=resolved.get("bottom"),
    )
    return BorderContactTopology(detection=resolved_detection, sides=topology)
