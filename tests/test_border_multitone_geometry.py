from PIL import Image, ImageDraw

from mtkrita.border import detect_border


def _incoherent_multitone_frame() -> Image.Image:
    size = (120, 100)
    inset = 6
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    colors = {
        "left": (80, 210, 120, 255),
        "top": (185, 235, 135, 255),
        "right": (55, 130, 205, 255),
        "bottom": (80, 95, 170, 255),
    }

    for offset in range(5):
        draw.line(
            (inset + offset, inset + offset, size[0] - 1 - inset - offset, inset + offset),
            fill=colors["top"],
        )
        x = size[0] - 1 - inset - offset
        draw.line((x, inset + offset, x, size[1] - 1 - inset - offset), fill=colors["right"])

    draw.line((inset, inset, inset, size[1] - 1 - inset), fill=colors["left"])
    draw.line(
        (inset, size[1] - 1 - inset, size[0] - 1 - inset, size[1] - 1 - inset),
        fill=colors["bottom"],
    )
    return image


def _offset_asymmetric_coherent_multitone_frame() -> Image.Image:
    size = (140, 110)
    offsets = {"left": 4, "top": 7, "right": 9, "bottom": 5}
    width = 3
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    colors = {
        "left": (80, 210, 120, 255),
        "top": (185, 235, 135, 255),
        "right": (55, 130, 205, 255),
        "bottom": (80, 95, 170, 255),
    }

    for delta in range(width):
        draw.line(
            (
                offsets["left"] + delta,
                offsets["top"],
                offsets["left"] + delta,
                size[1] - 1 - offsets["bottom"],
            ),
            fill=colors["left"],
        )
        x = size[0] - 1 - offsets["right"] - delta
        draw.line(
            (x, offsets["top"], x, size[1] - 1 - offsets["bottom"]),
            fill=colors["right"],
        )
        draw.line(
            (
                offsets["left"],
                offsets["top"] + delta,
                size[0] - 1 - offsets["right"],
                offsets["top"] + delta,
            ),
            fill=colors["top"],
        )
        y = size[1] - 1 - offsets["bottom"] - delta
        draw.line(
            (offsets["left"], y, size[0] - 1 - offsets["right"], y),
            fill=colors["bottom"],
        )
    return image


def test_multitone_fallback_rejects_incoherent_constructed_thickness() -> None:
    detection = detect_border(_incoherent_multitone_frame())

    assert detection.detected is False
    assert detection.consensus_mode == "none"


def test_multitone_fallback_allows_asymmetric_offsets_when_thickness_is_coherent() -> None:
    detection = detect_border(_offset_asymmetric_coherent_multitone_frame())

    assert detection.detected is True
    assert detection.consensus_mode == "multi_tone_four_side"
    sides = (detection.left, detection.top, detection.right, detection.bottom)
    assert all(side is not None and side.thickness == 3 for side in sides)
    assert tuple(side.offset for side in sides if side is not None) == (4, 7, 9, 5)
