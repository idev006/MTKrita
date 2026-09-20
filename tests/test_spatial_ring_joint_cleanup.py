from dataclasses import replace

from PIL import Image, ImageDraw

from mtkrita.border import BorderDetection, BorderSide
from mtkrita.closed_ring import ClosedRingStatus, plan_closed_ring
from mtkrita.joint_cleanup import JointCleanupStatus, apply_joint_cleanup
from mtkrita.metadata import detect_corner_metadata
from mtkrita.spatial_joint_cleanup import plan_spatial_ring_metadata_cleanup

_RING = (160, 220, 100, 255)
_ART = (240, 100, 80, 255)


def _side(name: str) -> BorderSide:
    return BorderSide(
        side=name,
        offset=6,
        thickness=2,
        color=_RING[:3],
        confidence=1.0,
        contact_risk=True,
        contact_fraction=0.20,
        contact_ranges=((10, 20),),
    )


def _detection() -> BorderDetection:
    return BorderDetection(
        left=_side("left"),
        top=_side("top"),
        right=_side("right"),
        bottom=_side("bottom"),
        consensus_mode="single_tone",
    )


def _line(image: Image.Image, side: str, offset: int, *, start: int = 0, end: int = 100) -> None:
    draw = ImageDraw.Draw(image)
    if side == "top":
        draw.line((start, offset, end - 1, offset), fill=_RING)
    elif side == "bottom":
        y = image.height - 1 - offset
        draw.line((start, y, end - 1, y), fill=_RING)
    elif side == "left":
        draw.line((offset, start, offset, end - 1), fill=_RING)
    elif side == "right":
        x = image.width - 1 - offset
        draw.line((x, start, x, end - 1), fill=_RING)
    else:
        raise AssertionError(side)


def _case() -> tuple[Image.Image, object, object]:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for offset in range(6, 10):
        for side in ("top", "right", "bottom", "left"):
            _line(image, side, offset)
    draw = ImageDraw.Draw(image)
    draw.ellipse((2, 2, 16, 16), fill=_RING)
    draw.rectangle((35, 35, 64, 64), fill=_ART)

    ring = plan_closed_ring(image, _detection())
    assert ring.status == ClosedRingStatus.RING_WITH_CONTACT
    assert ring.mask is not None
    metadata = detect_corner_metadata(image, analysis_exclusion_mask=ring.mask)
    return image, ring, metadata


def test_exact_ring_badge_contact_can_form_safe_joint_plan() -> None:
    image, ring, metadata = _case()

    plan = plan_spatial_ring_metadata_cleanup(image, ring, metadata)

    assert metadata.mask is not None
    assert metadata.analysis_exclusion_sha256 == ring.mask_sha256
    assert plan.status == JointCleanupStatus.SAFE_PLAN
    assert plan.unexplained_contact_fraction == 0.0
    assert plan.mask_sha256 is not None

    cleaned = apply_joint_cleanup(image, plan)
    assert cleaned.getpixel((6, 50))[3] == 0
    assert cleaned.getpixel((10, 10))[3] == 0
    assert cleaned.getpixel((50, 50))[3] == 255


def test_remote_ring_colored_contact_outside_badge_routes_review() -> None:
    image, _, _ = _case()
    _line(image, "right", 10, start=40, end=60)
    ring = plan_closed_ring(image, _detection())
    assert ring.status == ClosedRingStatus.RING_WITH_CONTACT
    assert ring.mask is not None
    metadata = detect_corner_metadata(image, analysis_exclusion_mask=ring.mask)

    plan = plan_spatial_ring_metadata_cleanup(image, ring, metadata)

    assert plan.status == JointCleanupStatus.REVIEW
    assert plan.unexplained_contact_fraction > 0
    assert "outside approved metadata adjacency" in plan.reasons[0]


def test_mismatched_metadata_exclusion_hash_is_rejected() -> None:
    image, ring, metadata = _case()
    mismatched = replace(metadata, analysis_exclusion_sha256="0" * 64)

    plan = plan_spatial_ring_metadata_cleanup(image, ring, mismatched)

    assert plan.status == JointCleanupStatus.REVIEW
    assert "does not match accepted ring mask" in plan.reasons[0]


def test_missing_metadata_cannot_explain_ring_contact() -> None:
    image, ring, metadata = _case()
    absent = replace(metadata, bbox=None, mask=None, anchored_candidate_count=0)

    plan = plan_spatial_ring_metadata_cleanup(image, ring, absent)

    assert plan.status == JointCleanupStatus.REVIEW
    assert "metadata cleanup mask is absent" in plan.reasons[0]


def test_excessive_combined_removal_ratio_is_rejected() -> None:
    image, ring, metadata = _case()

    plan = plan_spatial_ring_metadata_cleanup(
        image,
        ring,
        metadata,
        max_removed_ratio=0.001,
    )

    assert plan.status == JointCleanupStatus.REVIEW
    assert plan.planned_removed_ratio > 0.001
    assert "exceeds maximum removal ratio" in plan.reasons[0]


def test_spatial_joint_plan_is_deterministic_and_source_is_immutable() -> None:
    image, ring, metadata = _case()
    source_bytes = image.tobytes()

    first = plan_spatial_ring_metadata_cleanup(image, ring, metadata)
    second = plan_spatial_ring_metadata_cleanup(image, ring, metadata)

    assert first.status == JointCleanupStatus.SAFE_PLAN
    assert first.mask_sha256 == second.mask_sha256
    assert first.planned_removed_pixel_count == second.planned_removed_pixel_count
    assert image.tobytes() == source_bytes
