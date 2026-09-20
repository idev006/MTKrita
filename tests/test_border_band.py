from PIL import Image, ImageDraw

from mtkrita.border import BorderDetection, BorderSide
from mtkrita.border_band import (
    BorderBandCompletionStatus,
    plan_border_band_completion,
)


_COLOR = (40, 180, 90, 255)


def _side(name: str, *, risk: bool = True, offset: int = 2, thickness: int = 2) -> BorderSide:
    return BorderSide(
        side=name,
        thickness=thickness,
        color=_COLOR[:3],
        confidence=1.0,
        contact_risk=risk,
        offset=offset,
        contact_fraction=0.20 if risk else 0.0,
        contact_ranges=((0, 100),) if risk else (),
    )


def _detection(*names: str) -> BorderDetection:
    sides = {name: _side(name) for name in names}
    return BorderDetection(
        left=sides.get("left"),
        top=sides.get("top"),
        right=sides.get("right"),
        bottom=sides.get("bottom"),
        consensus_mode="single_tone",
    )


def _image() -> Image.Image:
    return Image.new("RGBA", (100, 100), (0, 0, 0, 0))


def _line(image: Image.Image, side: str, offset: int, *, start: int = 0, end: int = 100) -> None:
    draw = ImageDraw.Draw(image)
    if side == "top":
        draw.line((start, offset, end - 1, offset), fill=_COLOR)
    elif side == "bottom":
        y = image.height - 1 - offset
        draw.line((start, y, end - 1, y), fill=_COLOR)
    elif side == "left":
        draw.line((offset, start, offset, end - 1), fill=_COLOR)
    elif side == "right":
        x = image.width - 1 - offset
        draw.line((x, start, x, end - 1), fill=_COLOR)
    else:
        raise AssertionError(side)


def test_adjacent_side_decorative_layer_can_be_planned_safely() -> None:
    image = _image()
    _line(image, "top", 4)
    _line(image, "left", 4)

    plan = plan_border_band_completion(image, _detection("top", "left"))

    assert plan.status == BorderBandCompletionStatus.SAFE_COMPLETE
    assert plan.corroboration_pattern == "adjacent_side_layer"
    assert plan.corroborating_sides == ("left", "top")
    assert plan.proposed_inner_offsets == {"left": 5, "top": 5}
    assert all(not item.contact_risk for item in plan.completed_inner_contact.values())


def test_single_side_long_strip_is_not_enough() -> None:
    image = _image()
    _line(image, "top", 4)

    plan = plan_border_band_completion(image, _detection("top"))

    assert plan.status == BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION
    assert "top" in plan.side_layers
    assert plan.proposed_inner_offsets == {}


def test_opposite_side_only_similarity_is_not_enough() -> None:
    image = _image()
    _line(image, "top", 4)
    _line(image, "bottom", 4)

    plan = plan_border_band_completion(image, _detection("top", "bottom"))

    assert plan.status == BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION
    assert plan.corroboration_pattern is None


def test_four_side_coherent_ring_can_be_planned_safely() -> None:
    image = _image()
    for name in ("top", "right", "bottom", "left"):
        _line(image, name, 4)

    plan = plan_border_band_completion(
        image,
        _detection("left", "top", "right", "bottom"),
    )

    assert plan.status == BorderBandCompletionStatus.SAFE_COMPLETE
    assert plan.corroboration_pattern == "four_side_ring"
    assert plan.corroborating_sides == ("bottom", "left", "right", "top")


def test_four_side_depth_conflict_fails_closed() -> None:
    image = _image()
    for offset in range(4, 8):
        _line(image, "top", offset)
    for name in ("right", "bottom", "left"):
        _line(image, name, 4)

    plan = plan_border_band_completion(
        image,
        _detection("left", "top", "right", "bottom"),
    )

    assert plan.status == BorderBandCompletionStatus.REVIEW_GEOMETRY_CONFLICT
    assert plan.proposed_inner_offsets == {}


def test_completion_reaching_search_boundary_fails_closed() -> None:
    image = _image()
    for offset in range(4, 12):
        _line(image, "top", offset)
        _line(image, "left", offset)

    plan = plan_border_band_completion(image, _detection("top", "left"))

    assert plan.status == BorderBandCompletionStatus.REVIEW_SEARCH_BOUNDARY
    assert plan.proposed_inner_offsets == {"left": 12, "top": 12}


def test_completed_inner_boundary_contact_fails_closed() -> None:
    image = _image()
    _line(image, "top", 4)
    _line(image, "left", 4)
    _line(image, "top", 5, start=40, end=50)
    _line(image, "left", 5, start=40, end=50)

    plan = plan_border_band_completion(image, _detection("top", "left"))

    assert plan.status == BorderBandCompletionStatus.REVIEW_ARTWORK_CONTACT
    assert plan.completed_inner_contact["top"].contact_risk is True
    assert plan.completed_inner_contact["left"].contact_risk is True


def test_remote_same_color_artwork_is_not_absorbed_without_corner_corroboration() -> None:
    image = _image()
    _line(image, "top", 4, start=35, end=65)
    _line(image, "left", 4, start=35, end=65)

    plan = plan_border_band_completion(image, _detection("top", "left"))

    assert plan.status == BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION
    assert plan.proposed_inner_offsets == {}


def test_no_residual_contact_needs_no_class_b_plan() -> None:
    image = _image()
    detection = BorderDetection(
        left=_side("left", risk=False),
        top=_side("top", risk=False),
        right=None,
        bottom=None,
        consensus_mode="single_tone",
    )

    plan = plan_border_band_completion(image, detection)

    assert plan.status == BorderBandCompletionStatus.NOT_NEEDED


def test_ambiguous_border_consensus_does_not_gain_class_b_authority() -> None:
    image = _image()
    detection = BorderDetection(
        left=None,
        top=None,
        right=None,
        bottom=None,
        consensus_mode="none",
        review_reason="four-side multi-tone thickness geometry is incoherent",
    )

    plan = plan_border_band_completion(image, detection)

    assert plan.status == BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION
    assert plan.proposed_inner_offsets == {}


def test_class_b_planner_is_deterministic() -> None:
    image = _image()
    _line(image, "top", 4)
    _line(image, "left", 4)
    detection = _detection("top", "left")

    first = plan_border_band_completion(image, detection)
    second = plan_border_band_completion(image, detection)

    assert first == second
