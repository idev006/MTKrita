from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PIL import Image

from .border import BorderDetection, BorderSide


class DepthTopologyStatus(str, Enum):
    NOT_NEEDED = "NOT_NEEDED"
    SAFE_COMPLETE = "SAFE_COMPLETE"
    REVIEW_INSUFFICIENT_CORROBORATION = "REVIEW_INSUFFICIENT_CORROBORATION"
    REVIEW_ARTWORK_CONTACT = "REVIEW_ARTWORK_CONTACT"
    REVIEW_GEOMETRY_CONFLICT = "REVIEW_GEOMETRY_CONFLICT"
    REVIEW_SEARCH_BOUNDARY = "REVIEW_SEARCH_BOUNDARY"


@dataclass(frozen=True)
class ToneCluster:
    color: tuple[int, int, int]
    pixel_count: int
    fraction_of_visible: float


@dataclass(frozen=True)
class DepthLayerEvidence:
    side: str
    relative_depth: int
    offset: int
    visible_support: float
    visible_ranges: tuple[tuple[int, int], ...]
    longest_run_fraction: float
    endpoint_low: bool
    endpoint_high: bool
    tone_clusters: tuple[ToneCluster, ...]
    significant_cluster_count: int
    dominant_cluster_fraction: float


@dataclass(frozen=True)
class DepthBoundaryContact:
    raw_fraction: float
    raw_ranges: tuple[tuple[int, int], ...]
    explained_corner_ranges: tuple[tuple[int, int], ...]
    residual_fraction: float
    residual_ranges: tuple[tuple[int, int], ...]
    contact_risk: bool


@dataclass(frozen=True)
class BorderBandDepthPlan:
    status: DepthTopologyStatus
    trigger_sides: tuple[str, ...]
    deepest_proven_depth: dict[str, int]
    proposed_inner_offsets: dict[str, int]
    depth_evidence: dict[str, tuple[DepthLayerEvidence, ...]]
    proven_pairs: dict[int, tuple[tuple[str, str], ...]]
    completed_inner_contact: dict[str, DepthBoundaryContact]
    reasons: tuple[str, ...]


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

    output: list[tuple[int, int, int] | None] = []
    for x, y in coords:
        red, green, blue, alpha = pixels[x, y]
        output.append(None if alpha <= 8 else (red, green, blue))
    return output


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


def _visible_ranges(samples: list[tuple[int, int, int] | None]) -> tuple[tuple[int, int], ...]:
    return _ranges([index for index, sample in enumerate(samples) if sample is not None])


def _tone_clusters(
    samples: list[tuple[int, int, int] | None],
    *,
    quantization: int,
    significant_fraction: float,
) -> tuple[tuple[ToneCluster, ...], int, float]:
    visible = [sample for sample in samples if sample is not None]
    if not visible:
        return (), 0, 0.0

    buckets: dict[tuple[int, int, int], list[tuple[int, int, int]]] = {}
    for sample in visible:
        key = tuple((channel // quantization) * quantization for channel in sample)
        buckets.setdefault(key, []).append(sample)

    clusters: list[ToneCluster] = []
    for pixels in buckets.values():
        color = tuple(
            round(sum(pixel[channel] for pixel in pixels) / len(pixels))
            for channel in range(3)
        )
        clusters.append(
            ToneCluster(
                color=color,
                pixel_count=len(pixels),
                fraction_of_visible=len(pixels) / len(visible),
            )
        )
    clusters.sort(key=lambda item: (-item.pixel_count, item.color))
    significant = sum(cluster.fraction_of_visible >= significant_fraction for cluster in clusters)
    dominant = clusters[0].fraction_of_visible if clusters else 0.0
    return tuple(clusters), significant, dominant


def _layer_evidence(
    image: Image.Image,
    side: str,
    offset: int,
    relative_depth: int,
    *,
    endpoint_envelope: int,
    min_visible_support: float,
    min_longest_run_fraction: float,
    tone_quantization: int,
    tone_significant_fraction: float,
    max_significant_clusters: int,
    min_dominant_cluster_fraction: float,
) -> DepthLayerEvidence | None:
    samples = _strip(image, side, offset)
    if not samples:
        return None
    visible_count = sum(sample is not None for sample in samples)
    visible_support = visible_count / len(samples)
    if visible_support < min_visible_support:
        return None

    visible_ranges = _visible_ranges(samples)
    if not visible_ranges:
        return None
    longest_run_fraction = max(end - start for start, end in visible_ranges) / len(samples)
    if longest_run_fraction < min_longest_run_fraction:
        return None

    clusters, significant_count, dominant_fraction = _tone_clusters(
        samples,
        quantization=tone_quantization,
        significant_fraction=tone_significant_fraction,
    )
    if significant_count > max_significant_clusters:
        return None
    if dominant_fraction < min_dominant_cluster_fraction:
        return None

    endpoint_low = any(start < endpoint_envelope for start, _ in visible_ranges)
    endpoint_high = any(end > len(samples) - endpoint_envelope for _, end in visible_ranges)
    return DepthLayerEvidence(
        side=side,
        relative_depth=relative_depth,
        offset=offset,
        visible_support=visible_support,
        visible_ranges=visible_ranges,
        longest_run_fraction=longest_run_fraction,
        endpoint_low=endpoint_low,
        endpoint_high=endpoint_high,
        tone_clusters=clusters,
        significant_cluster_count=significant_count,
        dominant_cluster_fraction=dominant_fraction,
    )


def _corner_endpoint(side: str, other: str) -> str | None:
    return {
        ("top", "left"): "low",
        ("left", "top"): "low",
        ("top", "right"): "high",
        ("right", "top"): "low",
        ("bottom", "left"): "low",
        ("left", "bottom"): "high",
        ("bottom", "right"): "high",
        ("right", "bottom"): "high",
    }.get((side, other))


def _endpoint_present(layer: DepthLayerEvidence, endpoint: str) -> bool:
    return layer.endpoint_low if endpoint == "low" else layer.endpoint_high


def _adjacent_pair_proven(
    first: DepthLayerEvidence,
    second: DepthLayerEvidence,
) -> bool:
    first_endpoint = _corner_endpoint(first.side, second.side)
    second_endpoint = _corner_endpoint(second.side, first.side)
    if first_endpoint is None or second_endpoint is None:
        return False
    return _endpoint_present(first, first_endpoint) and _endpoint_present(second, second_endpoint)


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


def _cluster_match(
    sample: tuple[int, int, int] | None,
    clusters: tuple[ToneCluster, ...],
    tolerance: int,
) -> bool:
    if sample is None:
        return False
    return any(_distance(sample, cluster.color) <= tolerance for cluster in clusters)


def _boundary_contact(
    image: Image.Image,
    side: str,
    offset: int,
    clusters: tuple[ToneCluster, ...],
    *,
    color_tolerance: int,
    contact_fraction_threshold: float,
) -> DepthBoundaryContact:
    samples = _strip(image, side, offset)
    trim = min(offset, max(0, len(samples) // 4))
    if trim and len(samples) > 2 * trim:
        region = samples[trim:-trim]
        origin = trim
    else:
        region = samples
        origin = 0
    indexes = [
        origin + index
        for index, sample in enumerate(region)
        if _cluster_match(sample, clusters, color_tolerance)
    ]
    raw_ranges = _ranges(indexes)
    match_count = sum(end - start for start, end in raw_ranges)
    raw_fraction = match_count / len(region) if region else 0.0
    return DepthBoundaryContact(
        raw_fraction=raw_fraction,
        raw_ranges=raw_ranges,
        explained_corner_ranges=(),
        residual_fraction=raw_fraction,
        residual_ranges=raw_ranges,
        contact_risk=raw_fraction >= contact_fraction_threshold,
    )


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


def _resolve_corner_contact(
    image: Image.Image,
    contacts: dict[str, DepthBoundaryContact],
    *,
    envelope: int,
    contact_fraction_threshold: float,
) -> dict[str, DepthBoundaryContact]:
    explained: dict[str, set[tuple[int, int]]] = {name: set() for name in contacts}
    corners = (
        ("top", "low", "left", "low"),
        ("top", "high", "right", "low"),
        ("bottom", "low", "left", "high"),
        ("bottom", "high", "right", "high"),
    )
    for first_name, first_endpoint, second_name, second_endpoint in corners:
        first = contacts.get(first_name)
        second = contacts.get(second_name)
        if first is None or second is None:
            continue
        first_length = image.width if first_name in {"top", "bottom"} else image.height
        second_length = image.width if second_name in {"top", "bottom"} else image.height
        first_ranges = _endpoint_ranges(
            first.raw_ranges,
            side_length=first_length,
            envelope=envelope,
            endpoint=first_endpoint,
        )
        second_ranges = _endpoint_ranges(
            second.raw_ranges,
            side_length=second_length,
            envelope=envelope,
            endpoint=second_endpoint,
        )
        if first_ranges and second_ranges:
            explained[first_name].update(first_ranges)
            explained[second_name].update(second_ranges)

    resolved: dict[str, DepthBoundaryContact] = {}
    for name, contact in contacts.items():
        explained_ranges = tuple(
            interval for interval in contact.raw_ranges if interval in explained[name]
        )
        residual_ranges = tuple(
            interval for interval in contact.raw_ranges if interval not in explained[name]
        )
        side_length = image.width if name in {"top", "bottom"} else image.height
        trim = min(
            max(0, side_length // 4),
            max(0, (side_length - sum(end - start for start, end in contact.raw_ranges)) // 2),
        )
        sample_count = max(1, side_length - (2 * trim))
        residual_count = sum(end - start for start, end in residual_ranges)
        residual_fraction = residual_count / sample_count
        resolved[name] = DepthBoundaryContact(
            raw_fraction=contact.raw_fraction,
            raw_ranges=contact.raw_ranges,
            explained_corner_ranges=explained_ranges,
            residual_fraction=residual_fraction,
            residual_ranges=residual_ranges,
            contact_risk=residual_fraction >= contact_fraction_threshold,
        )
    return resolved


def _empty_plan(
    status: DepthTopologyStatus,
    reason: str,
    *,
    trigger_sides: tuple[str, ...] = (),
    depth_evidence: dict[str, tuple[DepthLayerEvidence, ...]] | None = None,
) -> BorderBandDepthPlan:
    return BorderBandDepthPlan(
        status=status,
        trigger_sides=trigger_sides,
        deepest_proven_depth={},
        proposed_inner_offsets={},
        depth_evidence=depth_evidence or {},
        proven_pairs={},
        completed_inner_contact={},
        reasons=(reason,),
    )


def plan_border_band_depth_topology(
    image: Image.Image,
    detection: BorderDetection,
    *,
    max_fraction: float = 0.12,
    min_visible_support: float = 0.60,
    min_longest_run_fraction: float = 0.20,
    tone_quantization: int = 32,
    tone_significant_fraction: float = 0.05,
    max_significant_clusters: int = 4,
    min_dominant_cluster_fraction: float = 0.30,
    boundary_color_tolerance: int = 32,
    contact_fraction_threshold: float = 0.05,
) -> BorderBandDepthPlan:
    """Build a non-destructive depth-by-depth decorative border topology plan."""
    if not 0 < max_fraction <= 0.5:
        raise ValueError("max_fraction must be in (0, 0.5]")
    if tone_quantization <= 0 or tone_quantization > 256:
        raise ValueError("tone_quantization must be in [1, 256]")
    if detection.requires_review or detection.consensus_mode not in {
        "single_tone",
        "multi_tone_four_side",
    }:
        return _empty_plan(
            DepthTopologyStatus.REVIEW_INSUFFICIENT_CORROBORATION,
            "border consensus is not eligible for depth-topology completion",
        )

    authorized = _authorized_sides(detection)
    triggers = _trigger_sides(detection)
    trigger_names = tuple(sorted(triggers))
    if not triggers:
        return _empty_plan(
            DepthTopologyStatus.NOT_NEEDED,
            "no residual border contact requires depth-topology analysis",
        )

    max_search = max(1, int(min(image.size) * max_fraction))
    max_depth = max(
        0,
        min(
            max_search - (side.offset + side.thickness)
            for side in authorized.values()
        ),
    )
    if max_depth <= 0:
        return _empty_plan(
            DepthTopologyStatus.REVIEW_SEARCH_BOUNDARY,
            "no bounded inward depth remains inside the border search domain",
            trigger_sides=trigger_names,
        )

    per_side: dict[str, list[DepthLayerEvidence]] = {name: [] for name in authorized}
    proven_depth: dict[str, int] = {name: 0 for name in authorized}
    proven_pairs: dict[int, tuple[tuple[str, str], ...]] = {}
    active_triggers = set(triggers)

    for depth in range(1, max_depth + 1):
        current: dict[str, DepthLayerEvidence] = {}
        for name, side in authorized.items():
            if depth > proven_depth[name] + 1:
                continue
            offset = side.offset + side.thickness + depth - 1
            evidence = _layer_evidence(
                image,
                name,
                offset,
                depth,
                endpoint_envelope=max_search,
                min_visible_support=min_visible_support,
                min_longest_run_fraction=min_longest_run_fraction,
                tone_quantization=tone_quantization,
                tone_significant_fraction=tone_significant_fraction,
                max_significant_clusters=max_significant_clusters,
                min_dominant_cluster_fraction=min_dominant_cluster_fraction,
            )
            if evidence is not None:
                current[name] = evidence

        pairs: list[tuple[str, str]] = []
        names = tuple(current)
        for index, first_name in enumerate(names):
            for second_name in names[index + 1 :]:
                if first_name not in active_triggers and second_name not in active_triggers:
                    continue
                if _adjacent_pair_proven(current[first_name], current[second_name]):
                    pairs.append(tuple(sorted((first_name, second_name))))

        if len(current) == 4 and all(proven_depth[name] == depth - 1 for name in current):
            ring_sides = set(current)
            accepted_sides = ring_sides
            pairs = sorted(set(pairs))
        else:
            accepted_sides = {name for pair in pairs for name in pair}

        if not accepted_sides:
            break

        proven_pairs[depth] = tuple(sorted(set(pairs)))
        for name in accepted_sides:
            per_side[name].append(current[name])
            proven_depth[name] = depth
        active_triggers.update(accepted_sides)

    deepest = {name: depth for name, depth in proven_depth.items() if depth > 0}
    depth_evidence = {
        name: tuple(evidence)
        for name, evidence in per_side.items()
        if evidence
    }
    if not deepest or not any(name in deepest for name in triggers):
        return _empty_plan(
            DepthTopologyStatus.REVIEW_INSUFFICIENT_CORROBORATION,
            "no consecutive adjacent/four-side depth proof was established",
            trigger_sides=trigger_names,
            depth_evidence=depth_evidence,
        )

    proposed = {
        name: authorized[name].offset + authorized[name].thickness + depth
        for name, depth in deepest.items()
    }
    if any(offset >= max_search for offset in proposed.values()):
        return BorderBandDepthPlan(
            status=DepthTopologyStatus.REVIEW_SEARCH_BOUNDARY,
            trigger_sides=trigger_names,
            deepest_proven_depth=deepest,
            proposed_inner_offsets=proposed,
            depth_evidence=depth_evidence,
            proven_pairs=proven_pairs,
            completed_inner_contact={},
            reasons=("proven depth reaches the bounded search-domain limit",),
        )

    contacts: dict[str, DepthBoundaryContact] = {}
    for name, offset in proposed.items():
        final_layer = depth_evidence[name][-1]
        contacts[name] = _boundary_contact(
            image,
            name,
            offset,
            final_layer.tone_clusters,
            color_tolerance=boundary_color_tolerance,
            contact_fraction_threshold=contact_fraction_threshold,
        )
    contacts = _resolve_corner_contact(
        image,
        contacts,
        envelope=max_search,
        contact_fraction_threshold=contact_fraction_threshold,
    )

    if any(contact.contact_risk for contact in contacts.values()):
        return BorderBandDepthPlan(
            status=DepthTopologyStatus.REVIEW_ARTWORK_CONTACT,
            trigger_sides=trigger_names,
            deepest_proven_depth=deepest,
            proposed_inner_offsets=proposed,
            depth_evidence=depth_evidence,
            proven_pairs=proven_pairs,
            completed_inner_contact=contacts,
            reasons=("completed depth topology retains unexplained inner-boundary contact",),
        )

    return BorderBandDepthPlan(
        status=DepthTopologyStatus.SAFE_COMPLETE,
        trigger_sides=trigger_names,
        deepest_proven_depth=deepest,
        proposed_inner_offsets=proposed,
        depth_evidence=depth_evidence,
        proven_pairs=proven_pairs,
        completed_inner_contact=contacts,
        reasons=("consecutive cross-side depth topology is proven and completed boundary is clean",),
    )
