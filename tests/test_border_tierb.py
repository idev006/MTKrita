from PIL import Image, ImageDraw

from mtkrita.border import detect_border


def test_tierb_rounded_inset_border_uses_visible_purity_not_transparent_corners() -> None:
    image = Image.new("RGBA", (120, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (6, 6, 113, 93),
        radius=12,
        outline=(185, 235, 135, 255),
        width=3,
    )

    detection = detect_border(image)

    assert detection.detected is True
    assert detection.confidence >= 0.995
    for side in (detection.left, detection.top, detection.right, detection.bottom):
        assert side is not None
        assert 0.75 <= side.visible_support < 1.0
        assert side.color_purity >= 0.995


def test_tierb_high_color_purity_without_enough_visible_support_cannot_authorize_border() -> None:
    image = Image.new("RGBA", (120, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    color = (185, 235, 135, 255)
    draw.line((30, 6, 89, 6), fill=color, width=3)
    draw.line((30, 93, 89, 93), fill=color, width=3)
    draw.line((6, 25, 6, 74), fill=color, width=3)
    draw.line((113, 25, 113, 74), fill=color, width=3)

    detection = detect_border(image)

    assert detection.detected is False
