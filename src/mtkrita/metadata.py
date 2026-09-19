from __future__ import annotations

from dataclasses import dataclass
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
    fragmented_by_exclusion: bool = False
    fragment_association_applied: bool = False
    fragment_association_resolved: bool = False
    associated_fragment_count: int = 0
    requires_joint_cleanup: bool = False
    enclosed_visible_hole_pixel_count: int = 0
    coordinate_space: str = "pre_cleanup_frame"


@dataclass(frozen=True)
class _MetadataCandidate:
    confidence: float
    label: int
    bbox: tuple[int, int, int, int]
    area_ratio: float
    fill_ratio: float
    compactness: float
    anchor_distance: float
    anchored: bool


def _validate_zone(zone: MetadataZone) -> None:
    if not 0 < zone.x_fraction <= 0.5 or not 0 < zone.y_fraction <= 0.5:
        raise ValueError("metadata zone fractions must be in (0, 0.5]")
    if not 0 < zone.anchor_x_fraction <= 1 or not 0 < zone.anchor_y_fraction <= 1:
        raise ValueError("metadata anchor fractions must be in (0, 1]")


def _background_rgb(rgba: np.ndarray) -> np.ndarray:
    rgb = rgba[:, :, :3].astype(np.int16)
    alpha = rgba[:, :, 3]
    edge_rgb = np.concatenate((rgb[-1, :, :], rgb[:, -1, :]), axis=0)
    edge_alpha = np.concatenate((alpha[-1, :], alpha[:, -1]), axis=0)
    visible = edge_rgb[edge_alpha > 8]
    if visible.size == 0:
        return np.zeros(3, dtype=np.int16)
    return np.median(visible, axis=0)


def _analysis_exclusion(
    image: Image.Image,
    analysis_exclusion_mask: Image.Image | None,
    raw_candidate: np.ndarray,
    zone_width: int,
    zone_height: int,
) -> tuple[np.ndarray, dict[str, object]]:
    candidate_mask = raw_candidate.copy()
    if analysis_exclusion_mask is None:
        return candidate_mask, {
            "analysis_exclusion_applied": False,
            "analysis_excluded_pixel_count": 0,
            "analysis_excluded_candidate_pixel_count": 0,
            "fragmented_by_exclusion": False,
        }
    if analysis_exclusion_mask.size != image.size:
        raise ValueError("analysis exclusion mask size does not match frame")

    exclusion = np.asarray(analysis_exclusion_mask.convert("L"), dtype=np.uint8) > 0
    zone_exclusion = exclusion[:zone_height, :zone_width]
    raw_visible = raw_candidate > 0
    excluded_candidate = int(np.count_nonzero(raw_visible & zone_exclusion))
    candidate_mask[zone_exclusion] = 0
    return candidate_mask, {
        "analysis_exclusion_applied": True,
        "analysis_excluded_pixel_count": int(np.count_nonzero(exclusion)),
        "analysis_excluded_candidate_pixel_count": excluded_candidate,
        "fragmented_by_exclusion": excluded_candidate > 0,
    }


def _complete_enclosed_visible_holes(
    selected_mask: np.ndarray,
    alpha: np.ndarray,
) -> tuple[np.ndarray, int]:
    """Add only visible holes fully enclosed by the approved candidate topology."""
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
        local_completed = mask[y0:y1, x0:x1].copy()
        local_completed |= holes
        mask[y0:y1, x0:x1] = local_completed
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
) -> MetadataDetection:
    """Detect a compact, corner-anchored metadata component conservatively."""
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

    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    height, width = rgba.shape[:2]
    zone_width = max(1, round(width * resolved_zone.x_fraction))
    zone_height = max(1, round(height * resolved_zone.y_fraction))
    anchor_width = max(1.0, zone_width * resolved_zone.anchor_x_fraction)
    anchor_height = max(1.0, zone_height * resolved_zone.anchor_y_fraction)

    rgb = rgba[:, :, :3].astype(np.int16)
    alpha = rgba[:, :, 3]
    background = _background_rgb(rgba)

    zone_rgb = rgb[:zone_height, :zone_width, :]
    zone_alpha = alpha[:zone_height, :zone_width]
    distance = np.max(np.abs(zone_rgb - background), axis=2)
    raw_candidate = ((distance > color_tolerance) & (zone_alpha > 8)).astype(np.uint8) * 255
    candidate_mask, exclusion_evidence = _analysis_exclusion(
        image,
        analysis_exclusion_mask,
        raw_candidate,
        zone_width,
        zone_height,
    )

    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidate_mask, connectivity=8)
    if count <= 1:
        return MetadataDetection(
            None,
            0.0,
            None,
            "no compact metadata component found",
            **exclusion_evidence,
        )

    zone_area = zone_width * zone_height
    candidates: list[_MetadataCandidate] = []
    for label in range(1, count):
        x, y, w, h, area = (int(v) for v in stats[label])
        area_ratio = area / zone_area
        if not min_area_ratio <= area_ratio <= max_area_ratio:
            continue
        if w <= 1 or h <= 1:
            continue

        fill_ratio = area / (w * h)
        compactness = min(w, h) / max(w, h)
        center_x = x + (w / 2)
        center_y = y + (h / 2)
        anchored = center_x <= anchor_width and center_y <= anchor_height
        anchor_distance = hypot(center_x / zone_width, center_y / zone_height) / sqrt(2)
        proximity = 1.0 - min(1.0, anchor_distance)
        containment = 1.0 if (x + w <= zone_width and y + h <= zone_height) else 0.65
        confidence = (
            (0.30 * fill_ratio)
            + (0.30 * proximity)
            + (0.20 * compactness)
            + (0.20 * containment)
        )
        candidates.append(
            _MetadataCandidate(
                confidence=float(confidence),
                label=label,
                bbox=(x, y, x + w, y + h),
                area_ratio=float(area_ratio),
                fill_ratio=float(fill_ratio),
                compactness=float(compactness),
                anchor_distance=float(anchor_distance),
                anchored=anchored,
            )
        )

    if not candidates:
        return MetadataDetection(
            None,
            0.0,
            None,
            "no candidate passed metadata constraints",
            **exclusion_evidence,
        )

    plausible = [
        candidate
        for candidate in candidates
        if candidate.anchored
        and candidate.fill_ratio >= min_fill_ratio
        and candidate.compactness >= min_compactness
    ]
    if not plausible:
        return MetadataDetection(
            None,
            max(candidate.confidence for candidate in candidates),
            None,
            "no anchored metadata candidate passed shape constraints",
            candidate_count=len(candidates),
            anchored_candidate_count=0,
            **exclusion_evidence,
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
            **exclusion_evidence,
        )

    local = labels == best.label
    enclosed_count = 0
    if not bool(exclusion_evidence["fragmented_by_exclusion"]):
        local, enclosed_count = _complete_enclosed_visible_holes(local, zone_alpha)

    full_mask = np.zeros((height, width), dtype=np.uint8)
    full_mask[:zone_height, :zone_width] = local.astype(np.uint8) * 255
    reason = "single dominant anchored top-left metadata candidate"
    if enclosed_count:
        reason += "; enclosed visible interior detail included"
    if bool(exclusion_evidence["fragmented_by_exclusion"]):
        reason += "; analysis exclusion intersects candidate pixels"
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
        enclosed_visible_hole_pixel_count=enclosed_count,
        **exclusion_evidence,
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
