from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256

import numpy as np
from PIL import Image

from .border import BorderDetection, BorderSide
from .metadata import MetadataDetection


class JointCleanupStatus(str, Enum):
    SAFE_PLAN = "SAFE_PLAN"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class JointCleanupPlan:
    status: JointCleanupStatus
    combined_mask: Image.Image | None
    border_mask: Image.Image | None
    metadata_mask: Image.Image | None
    explained_contact_fraction: float
    unexplained_contact_fraction: float
    planned_removed_pixel_count: int
    planned_removed_ratio: float
    confidence: float
    mask_sha256: str | None
    reasons: tuple[str, ...]


def _distance_map(rgb: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    target = np.asarray(color, dtype=np.int16)
    return np.max(np.abs(rgb.astype(np.int16) - target), axis=2)


def _side_region(shape: tuple[int, int], side: BorderSide) -> np.ndarray:
    height, width = shape
    region = np.zeros((height, width), dtype=bool)
    start = side.offset
    end = side.offset + side.thickness
    if side.side == "left":
        region[:, start:end] = True
    elif side.side == "right":
        region[:, max(0, width - end) : max(0, width - start)] = True
    elif side.side == "top":
        region[start:end, :] = True
    elif side.side == "bottom":
        region[max(0, height - end) : max(0, height - start), :] = True
    else:
        raise ValueError(f"unsupported border side: {side.side}")
    return region


def build_border_cleanup_mask(
    image: Image.Image,
    detection: BorderDetection,
    *,
    color_tolerance: int = 48,
) -> Image.Image:
    if not 0 <= color_tolerance <= 255:
        raise ValueError("color_tolerance must be between 0 and 255")

    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    height, width = rgba.shape[:2]
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3]
    mask = np.zeros((height, width), dtype=np.uint8)

    for side in (detection.left, detection.top, detection.right, detection.bottom):
        if side is None:
            continue
        region = _side_region((height, width), side)
        near_border_color = _distance_map(rgb, side.color) <= color_tolerance
        selected = region & (alpha > 8) & near_border_color
        mask[selected] = 255

    return Image.fromarray(mask, mode="L")


def _range_length(value: tuple[int, int]) -> int:
    return max(0, value[1] - value[0])


def _overlap_length(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def _metadata_adjacent_to_side(
    side: BorderSide,
    bbox: tuple[int, int, int, int],
    size: tuple[int, int],
    adjacency: int,
) -> bool:
    width, height = size
    x0, y0, x1, y1 = bbox
    inner = side.offset + side.thickness
    if side.side == "top":
        return y0 <= inner + adjacency
    if side.side == "left":
        return x0 <= inner + adjacency
    if side.side == "bottom":
        return y1 >= height - inner - adjacency
    if side.side == "right":
        return x1 >= width - inner - adjacency
    return False


def _allowed_projection(
    side: BorderSide,
    bbox: tuple[int, int, int, int],
    adjacency: int,
) -> tuple[int, int]:
    x0, y0, x1, y1 = bbox
    if side.side in {"top", "bottom"}:
        return (max(0, x0 - adjacency), x1 + adjacency)
    return (max(0, y0 - adjacency), y1 + adjacency)


def _contact_accounting(
    detection: BorderDetection,
    metadata_bbox: tuple[int, int, int, int],
    size: tuple[int, int],
    adjacency: int,
) -> tuple[int, int, tuple[str, ...]]:
    explained = 0
    unexplained = 0
    reasons: list[str] = []

    for side in (detection.left, detection.top, detection.right, detection.bottom):
        if side is None or not side.contact_risk:
            continue
        if not side.contact_ranges:
            reasons.append(f"{side.side}: contact risk has no localized ranges")
            continue

        adjacent = _metadata_adjacent_to_side(side, metadata_bbox, size, adjacency)
        allowed = _allowed_projection(side, metadata_bbox, adjacency)
        for contact_range in side.contact_ranges:
            length = _range_length(contact_range)
            if not adjacent:
                unexplained += length
                continue
            overlap = _overlap_length(contact_range, allowed)
            explained += overlap
            unexplained += length - overlap

    return explained, unexplained, tuple(reasons)


def _review_plan(*reasons: str, confidence: float = 0.0) -> JointCleanupPlan:
    return JointCleanupPlan(
        status=JointCleanupStatus.REVIEW,
        combined_mask=None,
        border_mask=None,
        metadata_mask=None,
        explained_contact_fraction=0.0,
        unexplained_contact_fraction=1.0 if reasons else 0.0,
        planned_removed_pixel_count=0,
        planned_removed_ratio=0.0,
        confidence=confidence,
        mask_sha256=None,
        reasons=tuple(reasons),
    )


def plan_joint_cleanup(
    image: Image.Image,
    border: BorderDetection,
    metadata: MetadataDetection,
    *,
    border_auto_threshold: float = 0.995,
    metadata_auto_threshold: float = 0.72,
    contact_adjacency: int = 4,
    max_removed_ratio: float = 0.30,
    border_color_tolerance: int = 48,
) -> JointCleanupPlan:
    if contact_adjacency < 0:
        raise ValueError("contact_adjacency must be non-negative")
    if not 0 < max_removed_ratio <= 1:
        raise ValueError("max_removed_ratio must be in (0, 1]")
    if not border.detected:
        return _review_plan("border evidence is absent")
    confidence = min(border.confidence, metadata.confidence)
    if border.confidence < border_auto_threshold:
        return _review_plan("border confidence below automatic threshold", confidence=confidence)
    if not border.contact_risk:
        return _review_plan("joint cleanup is unnecessary without border contact", confidence=confidence)
    if metadata.mask is None or metadata.bbox is None:
        return _review_plan("metadata cleanup mask is absent or ambiguous", confidence=confidence)
    if metadata.confidence < metadata_auto_threshold:
        return _review_plan("metadata confidence below automatic threshold", confidence=confidence)
    if metadata.anchored_candidate_count != 1:
        return _review_plan("metadata candidate is not uniquely anchored", confidence=confidence)
    if metadata.fragmented_by_exclusion:
        return _review_plan(
            "metadata mask completeness unresolved after analysis exclusion",
            confidence=confidence,
        )

    explained, unexplained, localization_reasons = _contact_accounting(
        border,
        metadata.bbox,
        image.size,
        contact_adjacency,
    )
    if localization_reasons:
        return _review_plan(*localization_reasons, confidence=confidence)

    total_contact = explained + unexplained
    if total_contact <= 0:
        return _review_plan("contact risk has no measurable localized contact", confidence=confidence)
    explained_fraction = explained / total_contact
    unexplained_fraction = unexplained / total_contact
    if unexplained > 0:
        return JointCleanupPlan(
            status=JointCleanupStatus.REVIEW,
            combined_mask=None,
            border_mask=None,
            metadata_mask=metadata.mask.copy(),
            explained_contact_fraction=explained_fraction,
            unexplained_contact_fraction=unexplained_fraction,
            planned_removed_pixel_count=0,
            planned_removed_ratio=0.0,
            confidence=confidence,
            mask_sha256=None,
            reasons=("border contact exists outside approved metadata adjacency",),
        )

    border_mask = build_border_cleanup_mask(
        image,
        border,
        color_tolerance=border_color_tolerance,
    )
    metadata_mask = metadata.mask.convert("L")
    if metadata_mask.size != image.size:
        return _review_plan("metadata mask size does not match frame", confidence=confidence)

    border_array = np.asarray(border_mask, dtype=np.uint8)
    metadata_array = np.asarray(metadata_mask, dtype=np.uint8)
    combined = np.maximum(border_array, metadata_array)
    removed_count = int(np.count_nonzero(combined))
    removed_ratio = removed_count / max(1, image.width * image.height)
    if removed_ratio > max_removed_ratio:
        return JointCleanupPlan(
            status=JointCleanupStatus.REVIEW,
            combined_mask=None,
            border_mask=border_mask,
            metadata_mask=metadata_mask,
            explained_contact_fraction=explained_fraction,
            unexplained_contact_fraction=0.0,
            planned_removed_pixel_count=removed_count,
            planned_removed_ratio=removed_ratio,
            confidence=confidence,
            mask_sha256=None,
            reasons=("planned cleanup exceeds maximum removal ratio",),
        )

    combined_mask = Image.fromarray(combined, mode="L")
    digest = sha256(combined.tobytes()).hexdigest()
    return JointCleanupPlan(
        status=JointCleanupStatus.SAFE_PLAN,
        combined_mask=combined_mask,
        border_mask=border_mask,
        metadata_mask=metadata_mask,
        explained_contact_fraction=explained_fraction,
        unexplained_contact_fraction=0.0,
        planned_removed_pixel_count=removed_count,
        planned_removed_ratio=removed_ratio,
        confidence=confidence,
        mask_sha256=digest,
        reasons=("all localized border contact is explained by approved metadata adjacency",),
    )


def apply_joint_cleanup(image: Image.Image, plan: JointCleanupPlan) -> Image.Image:
    if plan.status != JointCleanupStatus.SAFE_PLAN or plan.combined_mask is None:
        raise ValueError("joint cleanup requires SAFE_PLAN")
    if plan.combined_mask.size != image.size:
        raise ValueError("joint cleanup mask size does not match frame")

    rgba = image.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8).copy()
    mask = np.asarray(plan.combined_mask, dtype=np.uint8)
    alpha[mask > 0] = 0
    rgba.putalpha(Image.fromarray(alpha, mode="L"))
    return rgba
