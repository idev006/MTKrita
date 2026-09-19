from PIL import Image, ImageDraw

from mtkrita.border import BorderDetection, BorderSide
from mtkrita.joint_cleanup import (
    JointCleanupStatus,
    apply_joint_cleanup,
    build_border_cleanup_mask,
    plan_joint_cleanup,
)
from mtkrita.metadata import MetadataDetection


def _side(
    name: str,
    *,
    contact: bool = False,
    ranges: tuple[tuple[int, int], ...] = (),
) -> BorderSide:
    return BorderSide(
        side=name,
        offset=6,
        thickness=3,
        color=(160, 220, 100),
        confidence=1.0,
        contact_risk=contact,
        contact_fraction=0.15 if contact else 0.0,
        contact_ranges=ranges,
    )


def _case() -> tuple[Image.Image, BorderDetection, MetadataDetection]:
    image = Image.new("RGBA", (80, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    border_color = (160, 220, 100, 255)
    for offset in range(6, 9):
        draw.rectangle((offset, offset, 79 - offset, 63 - offset), outline=border_color)
    draw.ellipse((4, 4, 20, 20), fill=border_color)
    draw.rectangle((30, 24, 55, 48), fill=(230, 80, 50, 255))

    metadata_mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(metadata_mask).ellipse((4, 4, 20, 20), fill=255)
    metadata = MetadataDetection(
        bbox=(4, 4, 21, 21),
        confidence=0.92,
        mask=metadata_mask,
        reason="single dominant anchored top-left metadata candidate",
        candidate_count=1,
        anchored_candidate_count=1,
        area_ratio=0.10,
        fill_ratio=0.80,
        compactness=1.0,
        anchor_distance=0.20,
        dominance_margin=1.0,
    )
    border = BorderDetection(
        left=_side("left", contact=True, ranges=((10, 20),)),
        top=_side("top", contact=True, ranges=((10, 20),)),
        right=_side("right"),
        bottom=_side("bottom"),
    )
    return image, border, metadata


def test_safe_joint_plan_is_deterministic_and_applies_once() -> None:
    image, border, metadata = _case()

    first = plan_joint_cleanup(image, border, metadata)
    second = plan_joint_cleanup(image, border, metadata)

    assert first.status == JointCleanupStatus.SAFE_PLAN
    assert first.unexplained_contact_fraction == 0.0
    assert first.explained_contact_fraction == 1.0
    assert first.mask_sha256 is not None
    assert first.mask_sha256 == second.mask_sha256
    assert first.planned_removed_pixel_count > 0
    assert first.planned_removed_ratio < 0.30

    result = apply_joint_cleanup(image, first)
    assert result.getpixel((10, 10))[3] == 0
    assert result.getpixel((40, 32))[3] == 255


def test_unexplained_contact_on_other_side_routes_review() -> None:
    image, border, metadata = _case()
    border = BorderDetection(
        left=border.left,
        top=border.top,
        right=_side("right", contact=True, ranges=((28, 40),)),
        bottom=border.bottom,
    )

    plan = plan_joint_cleanup(image, border, metadata)

    assert plan.status == JointCleanupStatus.REVIEW
    assert plan.unexplained_contact_fraction > 0
    assert "outside approved metadata adjacency" in plan.reasons[0]


def test_missing_contact_localization_routes_review() -> None:
    image, border, metadata = _case()
    border = BorderDetection(
        left=_side("left", contact=True, ranges=()),
        top=border.top,
        right=border.right,
        bottom=border.bottom,
    )

    plan = plan_joint_cleanup(image, border, metadata)

    assert plan.status == JointCleanupStatus.REVIEW
    assert any("no localized ranges" in reason for reason in plan.reasons)


def test_ambiguous_metadata_cannot_authorize_joint_cleanup() -> None:
    image, border, _ = _case()
    ambiguous = MetadataDetection(
        bbox=None,
        confidence=0.90,
        mask=None,
        reason="multiple ambiguous anchored metadata candidates",
        candidate_count=2,
        anchored_candidate_count=2,
        dominance_margin=0.02,
    )

    plan = plan_joint_cleanup(image, border, ambiguous)

    assert plan.status == JointCleanupStatus.REVIEW
    assert "metadata cleanup mask is absent" in plan.reasons[0]


def test_spatial_border_mask_preserves_different_color_artwork_crossing_band() -> None:
    image, border, _ = _case()
    draw = ImageDraw.Draw(image)
    draw.rectangle((6, 30, 8, 36), fill=(255, 0, 0, 255))

    mask = build_border_cleanup_mask(image, border)

    assert mask.getpixel((7, 32)) == 0
    assert image.getpixel((7, 32))[3] == 255


def test_excessive_planned_removal_routes_review() -> None:
    image, border, metadata = _case()

    plan = plan_joint_cleanup(image, border, metadata, max_removed_ratio=0.001)

    assert plan.status == JointCleanupStatus.REVIEW
    assert plan.planned_removed_ratio > 0.001
    assert "exceeds maximum removal ratio" in plan.reasons[0]


def test_review_plan_cannot_be_applied() -> None:
    image, border, metadata = _case()
    border = BorderDetection(
        left=border.left,
        top=border.top,
        right=_side("right", contact=True, ranges=((28, 40),)),
        bottom=border.bottom,
    )
    plan = plan_joint_cleanup(image, border, metadata)

    try:
        apply_joint_cleanup(image, plan)
    except ValueError as exc:
        assert "SAFE_PLAN" in str(exc)
    else:
        raise AssertionError("expected REVIEW plan application refusal")
