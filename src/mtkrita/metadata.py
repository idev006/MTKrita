from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import hypot, sqrt

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class MetadataZone:
    x_fraction: float = 0.25
    y_fraction: float = 0.25
    anchor_x_fraction: float = 0.60
    anchor_y_fraction: float = 0.60
    local_x_fraction: float = 0.90
    local_y_fraction: float = 0.90


@dataclass(frozen=True)
class MetadataDetection:
    bbox: tuple[int, int, int, int] | None
    confidence: float
    mask: Image.Image | None
    reason: str
    candidate_count: int = 0
    anchored_candidate_count: int = 0
    area_ratio: float | None = None
    fill_ratio: float | None = None
    compactness: float | None = None
    anchor_distance: float | None = None
    dominance_margin: float | None = None
    analysis_exclusion_applied: bool = False
    analysis_excluded_pixel_count: int = 0
    analysis_excluded_candidate_pixel_count: int = 0
    analysis_exclusion_sha256: str | None = None
    analysis_shape_overlap_pixel_count: int = 0
    fragmented_by_exclusion: bool = False
    fragment_association_applied: bool = False
    fragment_association_resolved: bool = False
    associated_fragment_count: int = 0
    ignored_remote_fragment_count: int = 0
    requires_joint_cleanup: bool = False
    enclosed_visible_hole_pixel_count: int = 0
    segmentation_basis: str = "rgb_background_distance"
    alpha_visibility_threshold: int = 8
    coordinate_space: str = "pre_cleanup_frame"


@dataclass(frozen=True)
class _MetadataCandidate:
    confidence: float
    mask: np.ndarray
    bbox: tuple[int, int, int, int]
    area_ratio: float
    fill_ratio: float
    compactness: float
    anchor_distance: float
    anchored: bool
    fragment_count: int = 1
    ignored_remote_fragment_count: int = 0
    requires_joint_cleanup: bool = False
    association_resolved: bool = False
    analysis_shape_overlap_pixel_count: int = 0


def _validate_zone(zone: MetadataZone) -> None:
    if not 0 < zone.x_fraction <= 0.5 or not 0 < zone.y_fraction <= 0.5:
        raise ValueError("metadata zone fractions must be in (0, 0.5]")
    for value in (
        zone.anchor_x_fraction,
        zone.anchor_y_fraction,
        zone.local_x_fraction,
        zone.local_y_fraction,
    ):
        if not 0 < value <= 1:
            raise ValueError("metadata anchor/local fractions must be in (0, 1]")
    if zone.anchor_x_fraction > zone.local_x_fraction or zone.anchor_y_fraction > zone.local_y_fraction:
        raise ValueError("metadata local envelope must contain the anchor envelope")


def _background_rgb(rgba: np.ndarray) -> np.ndarray:
    rgb = rgba[:, :, :3].astype(np.int16)
    alpha = rgba[:, :, 3]
    edge_rgb = np.concatenate((rgb[-1, :, :], rgb[:, -1, :]), axis=0)
    edge_alpha = np.concatenate((alpha[-1, :], alpha[:, -1]), axis=0)
    visible = edge_rgb[edge_alpha > 8]
    if visible.size == 0:
        return np.zeros(3, dtype=np.int16)
    return np.median(visible, axis=0)


def _meaningful_transparency(
    alpha: np.ndarray,
    *,
    transparent_alpha_threshold: int = 254,
    meaningful_ratio_threshold: float = 0.0001,
) -> bool:
    if alpha.size == 0:
        return False
    transparent_count = int(np.count_nonzero(alpha <= transparent_alpha_threshold))
    return (
        transparent_count / alpha.size >= meaningful_ratio_threshold
        and int(alpha.min()) <= transparent_alpha_threshold
    )


def _analysis_exclusion(
    image: Image.Image,
    analysis_exclusion_mask: Image.Image | None,
    raw_candidate: np.ndarray,
    zone_width: int,
    zone_height: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    candidate_mask = raw_candidate.copy()
    empty_exclusion = np.zeros((zone_height, zone_width), dtype=bool)
    if analysis_exclusion_mask is None:
        return candidate_mask, empty_exclusion, {
            "analysis_exclusion_applied": False,
            "analysis_excluded_pixel_count": 0,
            "analysis_excluded_candidate_pixel_count": 0,
            "analysis_exclusion_sha256": None,
        }
    if analysis_exclusion_mask.size != image.size:
        raise ValueError("analysis exclusion mask size does not match frame")

    exclusion_image = analysis_exclusion_mask.convert("L")
    exclusion_array = np.asarray(exclusion_image, dtype=np.uint8)
    exclusion = exclusion_array > 0
    zone_exclusion = exclusion[:zone_height, :zone_width]
    raw_visible = raw_candidate > 0
    excluded_candidate = int(np.count_nonzero(raw_visible & zone_exclusion))
    candidate_mask[zone_exclusion] = 0
    return candidate_mask, zone_exclusion, {
        "analysis_exclusion_applied": True,
        "analysis_excluded_pixel_count": int(np.count_nonzero(exclusion)),
        "analysis_excluded_candidate_pixel_count": excluded_candidate,
        "analysis_exclusion_sha256": sha256(exclusion_array.tobytes()).hexdigest(),
    }


def _candidate_from_mask(
    mask: np.ndarray,
    *,
    zone_width: int,
    zone_height: int,
    anchor_width: float,
    anchor_height: float,
    fragment_count: int = 1,
    ignored_remote_fragment_count: int = 0,
    requires_joint_cleanup: bool = False,
    association_resolved: bool = False,
    analysis_overlap: np.ndarray | None = None,
) -> _MetadataCandidate | None:
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    width = x1 - x0
    height = y1 - y0
    if width <= 1 or height <= 1:
        return None

    area = int(xs.size)
    overlap_count = 0
    if analysis_overlap is not None:
        if analysis_overlap.shape != mask.shape:
            raise ValueError("analysis overlap shape does not match candidate mask")
        overlap_count = int(np.count_nonzero(analysis_overlap[y0:y1, x0:x1]))

    area_ratio = area / max(1, zone_width * zone_height)
    analysis_area = min(width * height, area + overlap_count)
    fill_ratio = analysis_area / (width * height)
    compactness = min(width, height) / max(width, height)
    center_x = x0 + (width / 2)
    center_y = y0 + (height / 2)
    anchored = center_x <= anchor_width and center_y <= anchor_height
    anchor_distance = hypot(center_x / zone_width, center_y / zone_height) / sqrt(2)
    proximity = 1.0 - min(1.0, anchor_distance)
    confidence = (0.30 * fill_ratio) + (0.30 * proximity) + (0.20 * compactness) + 0.20
    return _MetadataCandidate(
        confidence=float(confidence),
        mask=mask.astype(bool, copy=True),
        bbox=(x0, y0, x1, y1),
        area_ratio=float(area_ratio),
        fill_ratio=float(fill_ratio),
        compactness=float(compactness),
        anchor_distance=float(anchor_distance),
        anchored=anchored,
        fragment_count=fragment_count,
        ignored_remote_fragment_count=ignored_remote_fragment_count,
        requires_joint_cleanup=requires_joint_cleanup,
        association_resolved=association_resolved,
        analysis_shape_overlap_pixel_count=overlap_count,
    )


def _inside_local_envelope(
    candidate: _MetadataCandidate,
    local_width: float,
    local_height: float,
) -> bool:
    _, _, x1, y1 = candidate.bbox
    return x1 <= local_width and y1 <= local_height


def _group_candidates_by_raw_topology(
    raw_candidate: np.ndarray,
    candidate_mask: np.ndarray,
    zone_exclusion: np.ndarray,
    *,
    zone_width: int,
    zone_height: int,
    anchor_width: float,
    anchor_height: float,
    local_width: float,
    local_height: float,
    association_gap: int = 2,
) -> tuple[list[_MetadataCandidate], bool]:
    raw_count, raw_labels = cv2.connectedComponents(raw_candidate, connectivity=8)
    candidates: list[_MetadataCandidate] = []
    unresolved_association = False

    if np.any(zone_exclusion):
        distance_to_exclusion = cv2.distanceTransform(
            (~zone_exclusion).astype(np.uint8), cv2.DIST_C, 3
        )
    else:
        distance_to_exclusion = np.full(candidate_mask.shape, 999.0, dtype=np.float32)

    for raw_label in range(1, raw_count):
        raw_group = raw_labels == raw_label
        group_mask = raw_group & (candidate_mask > 0)
        if not np.any(group_mask):
            continue

        excluded_from_group = bool(np.any(raw_group & zone_exclusion))
        if not excluded_from_group:
            candidate = _candidate_from_mask(
                group_mask,
                zone_width=zone_width,
                zone_height=zone_height,
                anchor_width=anchor_width,
                anchor_height=anchor_height,
            )
            if candidate is not None:
                candidates.append(candidate)
            continue

        fragment_count, fragment_labels = cv2.connectedComponents(
            group_mask.astype(np.uint8), connectivity=8
        )
        selected_fragments: list[np.ndarray] = []
        independent_fragments: list[_MetadataCandidate] = []
        remote_count = 0

        for fragment_label in range(1, fragment_count):
            fragment = fragment_labels == fragment_label
            fragment_candidate = _candidate_from_mask(
                fragment,
                zone_width=zone_width,
                zone_height=zone_height,
                anchor_width=anchor_width,
                anchor_height=anchor_height,
            )
            if fragment_candidate is None:
                continue

            local = _inside_local_envelope(fragment_candidate, local_width, local_height)
            distance = float(np.min(distance_to_exclusion[fragment]))
            adjacent = distance <= association_gap

            if fragment_candidate.anchored and adjacent:
                if not local:
                    unresolved_association = True
                    continue
                selected_fragments.append(fragment)
                continue

            remote_count += 1
            independent_fragments.append(fragment_candidate)

        if selected_fragments:
            selected_union = np.logical_or.reduce(selected_fragments)
            candidate = _candidate_from_mask(
                selected_union,
                zone_width=zone_width,
                zone_height=zone_height,
                anchor_width=anchor_width,
                anchor_height=anchor_height,
                fragment_count=len(selected_fragments),
                ignored_remote_fragment_count=remote_count,
                requires_joint_cleanup=True,
                association_resolved=True,
                analysis_overlap=raw_group & zone_exclusion,
            )
            if candidate is not None and _inside_local_envelope(
                candidate, local_width, local_height
            ):
                candidates.append(candidate)
            else:
                unresolved_association = True

        candidates.extend(independent_fragments)

    return candidates, unresolved_association


def _complete_enclosed_visible_holes(
    selected_mask: np.ndarray,
    alpha: np.ndarray,
) -> tuple[np.ndarray, int]:
    mask = selected_mask.astype(bool, copy=True)
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return mask, 0

    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    local = mask[y0:y1, x0:x1]
    inverse = (~local).astype(np.uint8)
    count, labels = cv2.connectedComponents(inverse, connectivity=8)
    if count <= 1:
        return mask, 0

    exterior_labels = set(labels[0, :].tolist())
    exterior_labels.update(labels[-1, :].tolist())
    exterior_labels.update(labels[:, 0].tolist())
    exterior_labels.update(labels[:, -1].tolist())

    holes = np.zeros_like(local, dtype=bool)
    for label in range(1, count):
        if label not in exterior_labels:
            holes |= labels == label

    holes &= alpha[y0:y1, x0:x1] > 8
    hole_count = int(np.count_nonzero(holes))
    if hole_count:
        completed = mask[y0:y1, x0:x1].copy()
        completed |= holes
        mask[y0:y1, x0:x1] = completed
    return mask, hole_count


def detect_corner_metadata(
    image: Image.Image,
    *,
    zone: MetadataZone | None = None,
    analysis_exclusion_mask: Image.Image | None = None,
    color_tolerance: int = 24,
    min_area_ratio: float = 0.002,
    max_area_ratio: float = 0.50,
    min_fill_ratio: float = 0.20,
    min_compactness: float = 0.35,
    dominance_margin: float = 0.12,
    alpha_visibility_threshold: int = 8,
) -> MetadataDetection:
    """Detect compact corner metadata with conservative topology evidence."""
    resolved_zone = zone or MetadataZone()
    _validate_zone(resolved_zone)
    if not 0 <= color_tolerance <= 255:
        raise ValueError("color_tolerance must be between 0 and 255")
    if not 0 <= min_fill_ratio <= 1:
        raise ValueError("min_fill_ratio must be between 0 and 1")
    if not 0 <= min_compactness <= 1:
        raise ValueError("min_compactness must be between 0 and 1")
    if not 0 <= dominance_margin <= 1:
        raise ValueError("dominance_margin must be between 0 and 1")
    if not 0 <= alpha_visibility_threshold <= 254:
        raise ValueError("alpha_visibility_threshold must be between 0 and 254")

    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    height, width = rgba.shape[:2]
    zone_width = max(1, round(width * resolved_zone.x_fraction))
    zone_height = max(1, round(height * resolved_zone.y_fraction))
    anchor_width = max(1.0, zone_width * resolved_zone.anchor_x_fraction)
    anchor_height = max(1.0, zone_height * resolved_zone.anchor_y_fraction)
    local_width = max(anchor_width, zone_width * resolved_zone.local_x_fraction)
    local_height = max(anchor_height, zone_height * resolved_zone.local_y_fraction)

    rgb = rgba[:, :, :3].astype(np.int16)
    alpha = rgba[:, :, 3]
    zone_alpha = alpha[:zone_height, :zone_width]

    if _meaningful_transparency(alpha):
        segmentation_basis = "alpha_visible"
        raw_candidate = (zone_alpha > alpha_visibility_threshold).astype(np.uint8) * 255
    else:
        segmentation_basis = "rgb_background_distance"
        background = _background_rgb(rgba)
        zone_rgb = rgb[:zone_height, :zone_width, :]
        distance = np.max(np.abs(zone_rgb - background), axis=2)
        raw_candidate = (
            (distance > color_tolerance) & (zone_alpha > alpha_visibility_threshold)
        ).astype(np.uint8) * 255

    segmentation_evidence = {
        "segmentation_basis": segmentation_basis,
        "alpha_visibility_threshold": alpha_visibility_threshold,
    }
    candidate_mask, zone_exclusion, exclusion_evidence = _analysis_exclusion(
        image,
        analysis_exclusion_mask,
        raw_candidate,
        zone_width,
        zone_height,
    )

    candidates, unresolved_association = _group_candidates_by_raw_topology(
        raw_candidate,
        candidate_mask,
        zone_exclusion,
        zone_width=zone_width,
        zone_height=zone_height,
        anchor_width=anchor_width,
        anchor_height=anchor_height,
        local_width=local_width,
        local_height=local_height,
    )
    if unresolved_association:
        return MetadataDetection(
            None,
            0.0,
            None,
            "analysis exclusion produced an unresolved local-isolation association",
            candidate_count=len(candidates),
            fragment_association_applied=True,
            fragment_association_resolved=False,
            **exclusion_evidence,
            **segmentation_evidence,
        )
    if not candidates:
        return MetadataDetection(
            None,
            0.0,
            None,
            "no compact metadata component found",
            **exclusion_evidence,
            **segmentation_evidence,
        )

    plausible = [
        candidate
        for candidate in candidates
        if candidate.anchored
        and _inside_local_envelope(candidate, local_width, local_height)
        and min_area_ratio <= candidate.area_ratio <= max_area_ratio
        and candidate.fill_ratio >= min_fill_ratio
        and candidate.compactness >= min_compactness
    ]
    if not plausible:
        return MetadataDetection(
            None,
            max(candidate.confidence for candidate in candidates),
            None,
            "no anchored metadata candidate passed local shape constraints",
            candidate_count=len(candidates),
            anchored_candidate_count=0,
            **exclusion_evidence,
            **segmentation_evidence,
        )

    plausible.sort(reverse=True, key=lambda item: item.confidence)
    best = plausible[0]
    margin = 1.0 if len(plausible) == 1 else best.confidence - plausible[1].confidence
    if len(plausible) > 1 and margin < dominance_margin:
        return MetadataDetection(
            None,
            best.confidence,
            None,
            "multiple ambiguous anchored metadata candidates",
            candidate_count=len(candidates),
            anchored_candidate_count=len(plausible),
            area_ratio=best.area_ratio,
            fill_ratio=best.fill_ratio,
            compactness=best.compactness,
            anchor_distance=best.anchor_distance,
            dominance_margin=float(margin),
            analysis_shape_overlap_pixel_count=best.analysis_shape_overlap_pixel_count,
            ignored_remote_fragment_count=best.ignored_remote_fragment_count,
            **exclusion_evidence,
            **segmentation_evidence,
        )

    completed_mask, enclosed_count = _complete_enclosed_visible_holes(best.mask, zone_alpha)
    full_mask = np.zeros((height, width), dtype=np.uint8)
    full_mask[:zone_height, :zone_width] = completed_mask.astype(np.uint8) * 255

    reason = "single dominant anchored top-left metadata candidate"
    if best.requires_joint_cleanup:
        reason += "; post-exclusion local isolation resolved for joint cleanup"
    if best.ignored_remote_fragment_count:
        reason += "; remote fragments preserved outside local destructive ownership"
    if best.analysis_shape_overlap_pixel_count:
        reason += "; approved exclusion overlap used for shape confidence only"
    if enclosed_count:
        reason += "; enclosed visible interior detail included"

    return MetadataDetection(
        bbox=best.bbox,
        confidence=best.confidence,
        mask=Image.fromarray(full_mask),
        reason=reason,
        candidate_count=len(candidates),
        anchored_candidate_count=len(plausible),
        area_ratio=best.area_ratio,
        fill_ratio=best.fill_ratio,
        compactness=best.compactness,
        anchor_distance=best.anchor_distance,
        dominance_margin=float(margin),
        analysis_shape_overlap_pixel_count=best.analysis_shape_overlap_pixel_count,
        fragmented_by_exclusion=best.requires_joint_cleanup and best.fragment_count > 1,
        fragment_association_applied=best.requires_joint_cleanup,
        fragment_association_resolved=best.association_resolved,
        associated_fragment_count=best.fragment_count,
        ignored_remote_fragment_count=best.ignored_remote_fragment_count,
        requires_joint_cleanup=best.requires_joint_cleanup,
        enclosed_visible_hole_pixel_count=enclosed_count,
        **exclusion_evidence,
        **segmentation_evidence,
    )


def remove_detected_metadata(
    image: Image.Image,
    detection: MetadataDetection,
    *,
    auto_threshold: float = 0.72,
) -> Image.Image:
    if detection.mask is None or detection.bbox is None:
        raise ValueError("no removable metadata mask")
    if detection.requires_joint_cleanup:
        raise ValueError("metadata mask requires joint cleanup")
    if detection.fragmented_by_exclusion and not detection.fragment_association_resolved:
        raise ValueError("metadata mask completeness unresolved after analysis exclusion")
    if detection.confidence < auto_threshold:
        raise ValueError("metadata confidence below automatic removal threshold")

    rgba = image.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8).copy()
    mask = np.asarray(detection.mask, dtype=np.uint8)
    alpha[mask > 0] = 0
    rgba.putalpha(Image.fromarray(alpha))
    return rgba
