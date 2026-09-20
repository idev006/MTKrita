from PIL import Image, ImageDraw

from mtkrita.border import BorderDetection, BorderSide
from mtkrita.border_band import BorderBandCompletionStatus, plan_border_band_completion


_COLOR = (40, 180, 90, 255)


def _side(name: str, *, risk: bool, offset: int = 2, thickness: int = 2) -> BorderSide:
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


def _detection(
    *,
    left: BorderSide | None = None,
    top: BorderSide | None = None,
    right: BorderSide | None = None,
    bottom: BorderSide | None = None,
) -> BorderDetection:
    return BorderDetection(
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        consensus_mode="single_tone",
    )


def test_non_risky_perpendicular_side_can_corroborate_trigger_side() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _line(image, "top", 4)
    _line(image, "left", 4)
    detection = _detection(
        top=_side("top", risk=True),
        left=_side("left", risk=False),
    )

    plan = plan_border_band_completion(image, detection)

    assert plan.status == BorderBandCompletionStatus.SAFE_COMPLETE
    assert plan.trigger_sides == ("top",)
    assert plan.corroboration_pattern == "adjacent_side_layer"
    assert plan.corroborating_sides == ("left", "top")
    assert plan.proposed_inner_offsets == {"left": 5, "top": 5}


def test_non_risky_opposite_side_cannot_corroborate_trigger_side() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _line(image, "top", 4)
    _line(image, "bottom", 4)
    detection = _detection(
        top=_side("top", risk=True),
        bottom=_side("bottom", risk=False),
    )

    plan = plan_border_band_completion(image, detection)

    assert plan.status == BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION
    assert plan.trigger_sides == ("top",)
    assert plan.proposed_inner_offsets == {}


def test_non_risky_side_without_contiguous_layer_cannot_corroborate() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _line(image, "top", 4)
    detection = _detection(
        top=_side("top", risk=True),
        left=_side("left", risk=False),
    )

    plan = plan_border_band_completion(image, detection)

    assert plan.status == BorderBandCompletionStatus.REVIEW_INSUFFICIENT_CORROBORATION
    assert "top" in plan.side_layers
    assert "left" not in plan.side_layers


def test_no_trigger_sides_remains_not_needed_even_when_layers_exist() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _line(image, "top", 4)
    _line(image, "left", 4)
    detection = _detection(
        top=_side("top", risk=False),
        left=_side("left", risk=False),
    )

    plan = plan_border_band_completion(image, detection)

    assert plan.status == BorderBandCompletionStatus.NOT_NEEDED
    assert plan.trigger_sides == ()
    assert plan.side_layers == {}


def test_corroborating_non_risky_side_with_unsafe_completed_boundary_reviews() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _line(image, "top", 4)
    _line(image, "left", 4)
    _line(image, "left", 5, start=40, end=55)
    detection = _detection(
        top=_side("top", risk=True),
        left=_side("left", risk=False),
    )

    plan = plan_border_band_completion(image, detection)

    assert plan.status == BorderBandCompletionStatus.REVIEW_ARTWORK_CONTACT
    assert plan.completed_inner_contact["left"].contact_risk is True
    assert plan.completed_inner_contact["left"].ranges


def test_completed_boundary_reciprocal_corner_contact_is_explained() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _line(image, "top", 4)
    _line(image, "left", 4)
    # Contact survives the completed-boundary trim but remains inside the 12 px corner envelope.
    _line(image, "top", 5, start=6, end=10)
    _line(image, "left", 5, start=6, end=10)
    detection = _detection(
        top=_side("top", risk=True),
        left=_side("left", risk=True),
    )

    plan = plan_border_band_completion(image, detection)

    assert plan.status == BorderBandCompletionStatus.SAFE_COMPLETE
    top = plan.completed_inner_contact["top"]
    left = plan.completed_inner_contact["left"]
    assert top.raw_ranges
    assert left.raw_ranges
    assert top.explained_corner_ranges == top.raw_ranges
    assert left.explained_corner_ranges == left.raw_ranges
    assert top.ranges == ()
    assert left.ranges == ()
    assert top.contact_risk is False
    assert left.contact_risk is False


def test_v11_planner_is_deterministic_with_non_risky_corroborator() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _line(image, "top", 4)
    _line(image, "left", 4)
    detection = _detection(
        top=_side("top", risk=True),
        left=_side("left", risk=False),
    )

    first = plan_border_band_completion(image, detection)
    second = plan_border_band_completion(image, detection)

    assert first == second
