from PIL import Image, ImageDraw

from mtkrita.border import detect_border, remove_border


def _framed(size: tuple[int, int], color: tuple[int, int, int, int], width: int) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for offset in range(width):
        draw.rectangle((offset, offset, size[0] - 1 - offset, size[1] - 1 - offset), outline=color)
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
