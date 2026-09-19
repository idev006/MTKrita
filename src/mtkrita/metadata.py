from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class MetadataZone:
    x_fraction: float = 0.20
    y_fraction: float = 0.20


@dataclass(frozen=True)
class MetadataDetection:
    bbox: tuple[int, int, int, int] | None
    confidence: float
    mask: Image.Image | None
    reason: str


def _validate_zone(zone: MetadataZone) -> None:
    if not 0 < zone.x_fraction <= 0.5 or not 0 < zone.y_fraction <= 0.5:
        raise ValueError("metadata zone fractions must be in (0, 0.5]")


def detect_corner_metadata(
    image: Image.Image,
    *,
    zone: MetadataZone = MetadataZone(),
    color_tolerance: int = 24,
    min_area_ratio: float = 0.002,
    max_area_ratio: float = 0.30,
) -> MetadataDetection:
    """Detect a compact top-left metadata component conservatively.

    The detector is intentionally limited to a configurable corner zone. It models
    background color from the opposite outer edges, then finds connected components
    that differ from that background. Ambiguous candidates are rejected rather than
    removed automatically.
    """
    _validate_zone(zone)
    if not 0 <= color_tolerance <= 255:
        raise ValueError("color_tolerance must be between 0 and 255")

    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    height, width = rgba.shape[:2]
    zone_width = max(1, round(width * zone.x_fraction))
    zone_height = max(1, round(height * zone.y_fraction))

    rgb = rgba[:, :, :3].astype(np.int16)
    alpha = rgba[:, :, 3]

    # Estimate background from bottom and right outer strips, which are away from
    # the default top-left number badge zone.
    sample = np.concatenate((rgb[-1, :, :], rgb[:, -1, :]), axis=0)
    background = np.median(sample, axis=0)

    zone_rgb = rgb[:zone_height, :zone_width, :]
    zone_alpha = alpha[:zone_height, :zone_width]
    distance = np.max(np.abs(zone_rgb - background), axis=2)
    candidate = ((distance > color_tolerance) & (zone_alpha > 8)).astype(np.uint8) * 255

    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidate, connectivity=8)
    if count <= 1:
        return MetadataDetection(None, 0.0, None, "no compact metadata component found")

    zone_area = zone_width * zone_height
    candidates: list[tuple[float, int, tuple[int, int, int, int]]] = []
    for label in range(1, count):
        x, y, w, h, area = (int(v) for v in stats[label])
        area_ratio = area / zone_area
        if not min_area_ratio <= area_ratio <= max_area_ratio:
            continue
        if w <= 1 or h <= 1:
            continue

        fill_ratio = area / (w * h)
        proximity = 1.0 - min(1.0, (x + y) / max(1, zone_width + zone_height))
        containment = 1.0 if (x + w < zone_width and y + h < zone_height) else 0.65
        confidence = (0.45 * fill_ratio) + (0.35 * proximity) + (0.20 * containment)
        candidates.append((confidence, label, (x, y, x + w, y + h)))

    if not candidates:
        return MetadataDetection(None, 0.0, None, "no candidate passed metadata constraints")

    candidates.sort(reverse=True, key=lambda item: item[0])
    best_confidence, best_label, bbox = candidates[0]
    if len(candidates) > 1 and candidates[1][0] >= best_confidence - 0.08:
        return MetadataDetection(None, best_confidence, None, "multiple ambiguous metadata candidates")

    full_mask = np.zeros((height, width), dtype=np.uint8)
    local = (labels == best_label).astype(np.uint8) * 255
    full_mask[:zone_height, :zone_width] = local
    return MetadataDetection(
        bbox=bbox,
        confidence=float(best_confidence),
        mask=Image.fromarray(full_mask, mode="L"),
        reason="single compact top-left metadata candidate",
    )


def remove_detected_metadata(
    image: Image.Image,
    detection: MetadataDetection,
    *,
    auto_threshold: float = 0.72,
) -> Image.Image:
    if detection.mask is None or detection.bbox is None:
        raise ValueError("no removable metadata mask")
    if detection.confidence < auto_threshold:
        raise ValueError("metadata confidence below automatic removal threshold")

    rgba = image.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8).copy()
    mask = np.asarray(detection.mask, dtype=np.uint8)
    alpha[mask > 0] = 0
    rgba.putalpha(Image.fromarray(alpha, mode="L"))
    return rgba
