from PIL import Image, ImageDraw

from mtkrita.border import BorderDetection, BorderSide
from mtkrita.closed_ring import ClosedRingStatus, plan_closed_ring

_TONE_A = (80, 210, 120, 255)
_TONE_B = (180, 235, 135, 255)


def _side(name: str, *, offset: int = 2, thickness: int = 2) -> BorderSide:
    return BorderSide(
        side=name,
        thickness=thickness,
        color=_TONE_A[:3],
        confidence=1.0,
        contact_risk=True,
        offset=offset,
        contact_fraction=0.20,
        contact_ranges=((10, 20),),
    )


def _detection(*, offset: int = 2, thickness: int = 2) -> BorderDetection:
    return BorderDetection(
        left=_side("left", offset=offset, thickness=thickness),
        top=_side("top", offset=offset, thickness=thickness),
        right=_side("right", offset=offset, thickness=thickness),
        bottom=_side("bottom", offset=offset, thickness=thickness),
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


def _ring(
    image: Image.Image,
    *,
    start: int = 2,
    end: int = 6,
    multitone: bool = False,
) -> None:
    for offset in range(start, end):
        color = _TONE_A if not multitone or offset % 2 == 0 else _TONE_B
        for side in ("top", "right", "bottom", "left"):
            _line(image, side, offset, color)


def test_coherent_four_side_ring_is_safe() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _ring(image)

    plan = plan_closed_ring(image, _detection())

    assert plan.status == ClosedRingStatus.SAFE_RING
    assert plan.mask is not None
    assert plan.mask_sha256 is not None
    assert plan.thickness_spread == 0
    assert all(side.thickness == 4 for side in plan.sides.values())
    assert all(side.contact_risk is False for side in plan.sides.values())


def test_multitone_ring_is_safe_without_global_color_model() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _ring(image, multitone=True)

    plan = plan_closed_ring(image, _detection())

    assert plan.status == ClosedRingStatus.SAFE_RING
    assert all(len(side.palette) >= 2 for side in plan.sides.values())
    assert all(side.palette_coverage >= 0.95 for side in plan.sides.values())


def test_transparent_outer_padding_and_inset_ring_are_supported() -> None:
    image = Image.new("RGBA", (120, 100), (0, 0, 0, 0))
    _ring(image, start=6, end=10, multitone=True)

    plan = plan_closed_ring(image, _detection(offset=6, thickness=2))

    assert plan.status == ClosedRingStatus.SAFE_RING
    assert all(side.offset == 6 for side in plan.sides.values())
    assert all(side.thickness == 4 for side in plan.sides.values())


def test_broken_side_cannot_be_authorized_as_ring() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for offset in range(2, 6):
        for side in ("top", "bottom", "left"):
            _line(image, side, offset, _TONE_A)
        _line(image, "right", offset, _TONE_A, start=0, end=40)

    plan = plan_closed_ring(image, _detection())

    assert plan.status == ClosedRingStatus.REVIEW
    assert plan.mask is None


def test_three_side_detection_is_not_closed_ring_authority() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _ring(image)
    detection = _detection()
    detection = BorderDetection(
        left=detection.left,
        top=detection.top,
        right=detection.right,
        bottom=None,
        consensus_mode="single_tone",
    )

    plan = plan_closed_ring(image, detection)

    assert plan.status == ClosedRingStatus.NO_RING
    assert plan.mask is None


def test_incoherent_side_thickness_routes_review() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for offset in range(2, 6):
        for side in ("top", "right", "left"):
            _line(image, side, offset, _TONE_A)
    for offset in range(2, 10):
        _line(image, "bottom", offset, _TONE_A)

    plan = plan_closed_ring(image, _detection())

    assert plan.status == ClosedRingStatus.REVIEW
    assert plan.thickness_spread is not None
    assert plan.thickness_spread > 2


def test_inner_same_palette_artwork_contact_is_preserved_as_risk() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _ring(image)
    _line(image, "top", 6, _TONE_A, start=35, end=55)

    plan = plan_closed_ring(image, _detection())

    assert plan.status == ClosedRingStatus.RING_WITH_CONTACT
    assert plan.sides["top"].contact_risk is True
    assert plan.sides["top"].contact_ranges


def test_reciprocal_corner_only_contact_is_explained() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _ring(image)
    _line(image, "top", 6, _TONE_A, start=7, end=10)
    _line(image, "left", 6, _TONE_A, start=7, end=10)

    plan = plan_closed_ring(image, _detection())

    assert plan.status == ClosedRingStatus.SAFE_RING
    assert plan.sides["top"].raw_contact_ranges
    assert plan.sides["top"].explained_corner_ranges == plan.sides["top"].raw_contact_ranges
    assert plan.sides["left"].explained_corner_ranges == plan.sides["left"].raw_contact_ranges
    assert plan.sides["top"].contact_ranges == ()
    assert plan.sides["left"].contact_ranges == ()


def test_touching_badge_interior_is_not_swallowed_by_spatial_ring_mask() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _ring(image)
    ImageDraw.Draw(image).ellipse((4, 4, 16, 16), fill=_TONE_A)

    plan = plan_closed_ring(image, _detection())

    assert plan.mask is not None
    assert plan.mask.getpixel((10, 10)) == 0
    assert image.getpixel((10, 10))[3] == 255


def test_closed_ring_planner_is_deterministic_and_non_destructive() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _ring(image, multitone=True)
    source_bytes = image.tobytes()

    first = plan_closed_ring(image, _detection())
    second = plan_closed_ring(image, _detection())

    assert first.status == second.status
    assert first.mask_sha256 == second.mask_sha256
    assert first.sides == second.sides
    assert image.tobytes() == source_bytes
