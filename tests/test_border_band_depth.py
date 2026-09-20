from PIL import Image, ImageDraw

from mtkrita.border import BorderDetection, BorderSide
from mtkrita.border_band_depth import DepthTopologyStatus, plan_border_band_depth_topology


_TONE_A = (40, 180, 90, 255)
_TONE_B = (90, 210, 130, 255)


def _side(name: str, *, risk: bool = True) -> BorderSide:
    return BorderSide(
        side=name,
        thickness=2,
        color=_TONE_A[:3],
        confidence=1.0,
        contact_risk=risk,
        offset=2,
        contact_fraction=0.20 if risk else 0.0,
        contact_ranges=((0, 100),) if risk else (),
    )


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


def _line(
    image: Image.Image,
    side: str,
    offset: int,
    color: tuple[int, int, int, int],
    *,
    start: int = 0,
    end: int = 100,
) -> None:
    draw = ImageDraw.Draw(image)
    if side == "top":
        draw.line((start, offset, end - 1, offset), fill=color)
    elif side == "bottom":
        y = image.height - 1 - offset
        draw.line((start, y, end - 1, y), fill=color)
    elif side == "left":
        draw.line((offset, start, offset, end - 1), fill=color)
    elif side == "right":
        x = image.width - 1 - offset
        draw.line((x, start, x, end - 1), fill=color)
    else:
        raise AssertionError(side)


def _two_tone_line(image: Image.Image, side: str, offset: int) -> None:
    _line(image, side, offset, _TONE_A, start=0, end=50)
    _line(image, side, offset, _TONE_B, start=50, end=100)


def test_two_depth_adjacent_multitone_structure_is_proven() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for offset in (4, 5):
        _two_tone_line(image, "top", offset)
        _two_tone_line(image, "left", offset)
    detection = _detection(top=_side("top"), left=_side("left", risk=False))

    plan = plan_border_band_depth_topology(image, detection)

    assert plan.status == DepthTopologyStatus.SAFE_COMPLETE
    assert plan.deepest_proven_depth == {"left": 2, "top": 2}
    assert plan.proposed_inner_offsets == {"left": 6, "top": 6}
    assert set(plan.proven_pairs) == {1, 2}


def test_depth_gap_is_never_skipped() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _two_tone_line(image, "top", 4)
    _two_tone_line(image, "left", 4)
    _two_tone_line(image, "top", 6)
    _two_tone_line(image, "left", 6)
    detection = _detection(top=_side("top"), left=_side("left", risk=False))

    plan = plan_border_band_depth_topology(image, detection)

    assert plan.status == DepthTopologyStatus.SAFE_COMPLETE
    assert plan.deepest_proven_depth == {"left": 1, "top": 1}
    assert plan.proposed_inner_offsets == {"left": 5, "top": 5}
    assert 2 not in plan.proven_pairs


def test_one_side_deeper_strip_cannot_advance_without_adjacent_proof() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _two_tone_line(image, "top", 4)
    _two_tone_line(image, "left", 4)
    _two_tone_line(image, "top", 5)
    detection = _detection(top=_side("top"), left=_side("left", risk=False))

    plan = plan_border_band_depth_topology(image, detection)

    assert plan.deepest_proven_depth == {"left": 1, "top": 1}
    assert plan.status == DepthTopologyStatus.REVIEW_ARTWORK_CONTACT
    assert plan.completed_inner_contact["top"].contact_risk is True


def test_four_side_two_depth_ring_is_proven() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for offset in (4, 5):
        for side in ("top", "right", "bottom", "left"):
            _two_tone_line(image, side, offset)
    detection = _detection(
        left=_side("left"),
        top=_side("top"),
        right=_side("right"),
        bottom=_side("bottom"),
    )

    plan = plan_border_band_depth_topology(image, detection)

    assert plan.status == DepthTopologyStatus.SAFE_COMPLETE
    assert plan.deepest_proven_depth == {
        "left": 2,
        "top": 2,
        "right": 2,
        "bottom": 2,
    }


def test_asymmetric_adjacent_depth_chains_remain_per_side() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for side in ("top", "left", "right"):
        _two_tone_line(image, side, 4)
    for side in ("top", "left"):
        _two_tone_line(image, side, 5)
    detection = _detection(
        left=_side("left", risk=False),
        top=_side("top"),
        right=_side("right", risk=False),
    )

    plan = plan_border_band_depth_topology(image, detection)

    assert plan.status == DepthTopologyStatus.SAFE_COMPLETE
    assert plan.deepest_proven_depth == {"left": 2, "top": 2, "right": 1}
    assert plan.proposed_inner_offsets == {"left": 6, "top": 6, "right": 5}


def test_chaotic_palette_is_not_accepted_as_depth_layer() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    colors = (
        (255, 0, 0, 255),
        (0, 255, 0, 255),
        (0, 0, 255, 255),
        (255, 255, 0, 255),
        (255, 0, 255, 255),
    )
    for side in ("top", "left"):
        for index, color in enumerate(colors):
            _line(image, side, 4, color, start=index * 20, end=(index + 1) * 20)
    detection = _detection(top=_side("top"), left=_side("left", risk=False))

    plan = plan_border_band_depth_topology(image, detection)

    assert plan.status == DepthTopologyStatus.REVIEW_INSUFFICIENT_CORROBORATION
    assert plan.deepest_proven_depth == {}


def test_final_inner_boundary_artwork_contact_routes_review() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for offset in (4, 5):
        _two_tone_line(image, "top", offset)
        _two_tone_line(image, "left", offset)
    _line(image, "top", 6, _TONE_A, start=35, end=55)
    _line(image, "left", 6, _TONE_A, start=35, end=55)
    detection = _detection(top=_side("top"), left=_side("left", risk=False))

    plan = plan_border_band_depth_topology(image, detection)

    assert plan.status == DepthTopologyStatus.REVIEW_ARTWORK_CONTACT
    assert plan.deepest_proven_depth == {"left": 2, "top": 2}
    assert plan.completed_inner_contact["top"].contact_risk is True
    assert plan.completed_inner_contact["left"].contact_risk is True


def test_depth_topology_planner_is_deterministic() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for offset in (4, 5):
        _two_tone_line(image, "top", offset)
        _two_tone_line(image, "left", offset)
    detection = _detection(top=_side("top"), left=_side("left", risk=False))

    first = plan_border_band_depth_topology(image, detection)
    second = plan_border_band_depth_topology(image, detection)

    assert first == second
