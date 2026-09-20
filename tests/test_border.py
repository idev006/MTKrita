from PIL import Image, ImageDraw

from mtkrita.border import detect_border, remove_border


def _framed(size: tuple[int, int], color: tuple[int, int, int, int], width: int) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for offset in range(width):
        draw.rectangle(
            (offset, offset, size[0] - 1 - offset, size[1] - 1 - offset),
            outline=color,
        )
    return image


def _inset_framed(
    size: tuple[int, int] = (100, 80),
    *,
    inset: int = 6,
    width: int = 3,
) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    colors = (
        (160, 220, 100, 255),
        (175, 235, 115, 255),
        (150, 210, 90, 255),
    )
    for offset in range(width):
        draw.rectangle(
            (
                inset + offset,
                inset + offset,
                size[0] - 1 - inset - offset,
                size[1] - 1 - inset - offset,
            ),
            outline=colors[offset % len(colors)],
        )
    return image


def _multitone_inset_frame(
    size: tuple[int, int] = (120, 100),
    *,
    inset: int = 6,
    width: int = 3,
    omit: str | None = None,
) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    colors = {
        "left": (80, 210, 120, 255),
        "top": (185, 235, 135, 255),
        "right": (55, 130, 205, 255),
        "bottom": (80, 95, 170, 255),
    }
    for offset in range(width):
        left = inset + offset
        top = inset + offset
        right = size[0] - 1 - inset - offset
        bottom = size[1] - 1 - inset - offset
        if omit != "top":
            draw.line((left, top, right, top), fill=colors["top"])
        if omit != "bottom":
            draw.line((left, bottom, right, bottom), fill=colors["bottom"])
        if omit != "left":
            draw.line((left, top, left, bottom), fill=colors["left"])
        if omit != "right":
            draw.line((right, top, right, bottom), fill=colors["right"])
    return image


def test_detects_different_border_colors_and_widths() -> None:
    green = _framed((80, 60), (180, 220, 80, 255), 3)
    black = _framed((80, 60), (12, 12, 12, 255), 7)
    green_result = detect_border(green)
    black_result = detect_border(black)
    assert green_result.left is not None and green_result.left.thickness == 3
    assert green_result.top is not None and green_result.top.thickness == 3
    assert black_result.left is not None and black_result.left.thickness == 7
    assert black_result.bottom is not None and black_result.bottom.thickness == 7


def test_high_confidence_border_can_be_removed() -> None:
    image = _framed((64, 64), (20, 120, 230, 255), 4)
    detection = detect_border(image)
    assert detection.contact_risk is False
    result = remove_border(image, detection)
    assert result.size == (56, 56)


def test_interrupted_edge_is_not_auto_detected_as_border() -> None:
    image = _framed((100, 80), (0, 0, 0, 255), 5)
    ImageDraw.Draw(image).rectangle((0, 30, 8, 50), fill=(255, 0, 0, 255))
    detection = detect_border(image)
    assert detection.left is None


def test_transparent_outer_edge_is_not_mistaken_for_black_border() -> None:
    image = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((10, 10, 29, 29), fill=(0, 0, 0, 255))
    detection = detect_border(image)
    assert detection.detected is False


def test_same_color_artwork_away_from_border_is_safe() -> None:
    color = (20, 120, 230, 255)
    image = _framed((80, 60), color, 4)
    ImageDraw.Draw(image).rectangle((20, 20, 35, 35), fill=color)
    detection = detect_border(image)
    assert detection.contact_risk is False
    result = remove_border(image, detection)
    assert result.size == (72, 52)


def test_same_color_artwork_touching_inner_border_requires_review() -> None:
    color = (20, 120, 230, 255)
    image = _framed((80, 60), color, 4)
    ImageDraw.Draw(image).rectangle((4, 20, 15, 35), fill=color)
    detection = detect_border(image)
    assert detection.left is not None
    assert detection.left.contact_risk is True
    assert detection.left.contact_fraction > 0
    assert detection.left.contact_ranges == ((20, 36),)
    assert detection.contact_risk is True

    try:
        remove_border(image, detection)
    except ValueError as exc:
        assert "contact risk" in str(exc)
    else:
        raise AssertionError("expected conservative border removal refusal")


def test_inset_border_after_transparent_padding_is_detected_and_removed() -> None:
    image = _inset_framed()
    detection = detect_border(image)

    assert detection.detected is True
    assert detection.consensus_mode == "single_tone"
    assert detection.contact_risk is False
    assert detection.confidence >= 0.995
    for side in (detection.left, detection.top, detection.right, detection.bottom):
        assert side is not None
        assert side.offset == 6
        assert side.thickness == 3
        assert side.contact_fraction == 0.0
        assert side.contact_ranges == ()

    result = remove_border(image, detection)
    assert result.size == (82, 62)


def test_single_near_edge_artwork_strip_cannot_authorize_inset_crop() -> None:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    ImageDraw.Draw(image).line((5, 10, 5, 69), fill=(20, 120, 230, 255), width=3)

    detection = detect_border(image)

    assert detection.detected is False


def test_inset_border_same_color_inner_contact_requires_review() -> None:
    image = _inset_framed()
    draw = ImageDraw.Draw(image)
    draw.rectangle((9, 24, 22, 55), fill=(160, 220, 100, 255))

    detection = detect_border(image)

    assert detection.left is not None
    assert detection.left.offset == 6
    assert detection.left.contact_risk is True
    assert detection.left.contact_fraction > 0
    assert detection.left.contact_ranges == ((24, 56),)
    assert detection.contact_risk is True

    try:
        remove_border(image, detection)
    except ValueError as exc:
        assert "contact risk" in str(exc)
    else:
        raise AssertionError("expected inset border contact-risk refusal")


def test_inset_corner_geometry_is_not_reported_as_contact_range() -> None:
    image = _inset_framed()
    detection = detect_border(image)

    assert detection.left is not None
    assert detection.top is not None
    assert detection.left.contact_ranges == ()
    assert detection.top.contact_ranges == ()


def test_four_side_multitone_inset_border_uses_conservative_fallback() -> None:
    image = _multitone_inset_frame()

    detection = detect_border(image)

    assert detection.detected is True
    assert detection.consensus_mode == "multi_tone_four_side"
    assert detection.confidence >= 0.995
    assert all(
        side is not None
        for side in (detection.left, detection.top, detection.right, detection.bottom)
    )


def test_three_side_multitone_geometry_cannot_authorize_fallback() -> None:
    image = _multitone_inset_frame(omit="bottom")

    detection = detect_border(image)

    assert detection.detected is False
    assert detection.consensus_mode == "none"


def test_multitone_fallback_rejects_insufficient_side_support() -> None:
    image = _multitone_inset_frame()
    draw = ImageDraw.Draw(image)
    draw.rectangle((5, 20, 10, 80), fill=(0, 0, 0, 0))

    detection = detect_border(image)

    assert detection.detected is False
    assert detection.consensus_mode == "none"


def test_multitone_fallback_preserves_contact_risk_gate() -> None:
    image = _multitone_inset_frame()
    draw = ImageDraw.Draw(image)
    draw.rectangle((9, 30, 20, 55), fill=(80, 210, 120, 255))

    detection = detect_border(image)

    assert detection.consensus_mode == "multi_tone_four_side"
    assert detection.left is not None
    assert detection.left.contact_risk is True
    assert detection.contact_risk is True


def test_multitone_fallback_evidence_is_deterministic() -> None:
    image = _multitone_inset_frame()

    first = detect_border(image)
    second = detect_border(image)

    assert first.consensus_mode == "multi_tone_four_side"
    assert first == second
