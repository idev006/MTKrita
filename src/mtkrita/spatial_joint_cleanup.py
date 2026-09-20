from __future__ import annotations

from hashlib import sha256

import numpy as np
from PIL import Image

from .closed_ring import ClosedRingPlan, ClosedRingStatus, RingSideEvidence
from .joint_cleanup import JointCleanupPlan, JointCleanupStatus
from .metadata import MetadataDetection


def _range_length(value: tuple[int, int]) -> int:
    return max(0, value[1] - value[0])


def _overlap_length(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def _metadata_adjacent_to_side(
    side: RingSideEvidence,
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
    side: RingSideEvidence,
    bbox: tuple[int, int, int, int],
    adjacency: int,
) -> tuple[int, int]:
    x0, y0, x1, y1 = bbox
    if side.side in {"top", "bottom"}:
        return (max(0, x0 - adjacency), x1 + adjacency)
    return (max(0, y0 - adjacency), y1 + adjacency)


def _contact_accounting(
    ring: ClosedRingPlan,
    metadata_bbox: tuple[int, int, int, int],
    size: tuple[int, int],
    adjacency: int,
) -> tuple[int, int, tuple[str, ...]]:
    explained = 0
    unexplained = 0
    reasons: list[str] = []
    for side in ring.sides.values():
        if not side.contact_risk:
            continue
        if not side.contact_ranges:
            reasons.append(f"{side.side}: ring contact risk has no localized ranges")
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


def plan_spatial_ring_metadata_cleanup(
    image: Image.Image,
    ring: ClosedRingPlan,
    metadata: MetadataDetection,
    *,
    metadata_auto_threshold: float = 0.72,
    contact_adjacency: int = 4,
    max_removed_ratio: float = 0.30,
) -> JointCleanupPlan:
    """Plan one exact-mask transparent cleanup for a verified closed ring plus metadata."""
    if contact_adjacency < 0:
        raise ValueError("contact_adjacency must be non-negative")
    if not 0 < max_removed_ratio <= 1:
        raise ValueError("max_removed_ratio must be in (0, 1]")
    if ring.status not in {ClosedRingStatus.SAFE_RING, ClosedRingStatus.RING_WITH_CONTACT}:
        return _review_plan("closed-ring plan is not eligible for spatial joint cleanup")
    if ring.mask is None or ring.mask_sha256 is None:
        return _review_plan("closed-ring mask or hash is absent")
    if ring.mask.size != image.size:
        return _review_plan("closed-ring mask size does not match frame")

    ring_confidence = min((side.palette_coverage for side in ring.sides.values()), default=0.0)
    confidence = min(ring_confidence, metadata.confidence)

    if metadata.mask is None or metadata.bbox is None:
        return _review_plan("metadata cleanup mask is absent or ambiguous", confidence=confidence)
    if metadata.mask.size != image.size:
        return _review_plan("metadata mask size does not match frame", confidence=confidence)
    if metadata.confidence < metadata_auto_threshold:
        return _review_plan("metadata confidence below automatic threshold", confidence=confidence)
    if metadata.anchored_candidate_count != 1:
        return _review_plan("metadata candidate is not uniquely anchored", confidence=confidence)
    if metadata.fragmented_by_exclusion and not metadata.fragment_association_resolved:
        return _review_plan(
            "metadata mask completeness unresolved after ring exclusion",
            confidence=confidence,
        )
    if metadata.analysis_exclusion_sha256 != ring.mask_sha256:
        return _review_plan(
            "metadata analysis exclusion does not match accepted ring mask",
            confidence=confidence,
        )

    explained, unexplained, localization_reasons = _contact_accounting(
        ring,
        metadata.bbox,
        image.size,
        contact_adjacency,
    )
    if localization_reasons:
        return _review_plan(*localization_reasons, confidence=confidence)

    total_contact = explained + unexplained
    if ring.status == ClosedRingStatus.RING_WITH_CONTACT and total_contact <= 0:
        return _review_plan("ring contact has no measurable localized evidence", confidence=confidence)

    explained_fraction = explained / total_contact if total_contact else 1.0
    unexplained_fraction = unexplained / total_contact if total_contact else 0.0
    if unexplained > 0:
        return JointCleanupPlan(
            status=JointCleanupStatus.REVIEW,
            combined_mask=None,
            border_mask=ring.mask.copy(),
            metadata_mask=metadata.mask.copy(),
            explained_contact_fraction=explained_fraction,
            unexplained_contact_fraction=unexplained_fraction,
            planned_removed_pixel_count=0,
            planned_removed_ratio=0.0,
            confidence=confidence,
            mask_sha256=None,
            reasons=("ring contact exists outside approved metadata adjacency",),
        )

    ring_array = np.asarray(ring.mask.convert("L"), dtype=np.uint8)
    metadata_array = np.asarray(metadata.mask.convert("L"), dtype=np.uint8)
    combined = np.maximum(ring_array, metadata_array)
    removed_count = int(np.count_nonzero(combined))
    removed_ratio = removed_count / max(1, image.width * image.height)
    if removed_ratio > max_removed_ratio:
        return JointCleanupPlan(
            status=JointCleanupStatus.REVIEW,
            combined_mask=None,
            border_mask=ring.mask.copy(),
            metadata_mask=metadata.mask.copy(),
            explained_contact_fraction=explained_fraction,
            unexplained_contact_fraction=0.0,
            planned_removed_pixel_count=removed_count,
            planned_removed_ratio=removed_ratio,
            confidence=confidence,
            mask_sha256=None,
            reasons=("planned spatial ring cleanup exceeds maximum removal ratio",),
        )

    combined_mask = Image.fromarray(combined)
    digest = sha256(combined.tobytes()).hexdigest()
    return JointCleanupPlan(
        status=JointCleanupStatus.SAFE_PLAN,
        combined_mask=combined_mask,
        border_mask=ring.mask.copy(),
        metadata_mask=metadata.mask.copy(),
        explained_contact_fraction=explained_fraction,
        unexplained_contact_fraction=0.0,
        planned_removed_pixel_count=removed_count,
        planned_removed_ratio=removed_ratio,
        confidence=confidence,
        mask_sha256=digest,
        reasons=("all residual ring contact is explained by exact-mask metadata adjacency",),
    )
