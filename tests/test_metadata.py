from PIL import Image, ImageDraw

from mtkrita.metadata import detect_corner_metadata, remove_detected_metadata


def test_detects_and_removes_top_left_badge_without_touching_artwork_elsewhere() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 34, 34), fill=(180, 220, 120, 255))
    draw.rectangle((90, 50, 150, 120), fill=(230, 120, 40, 255))

    detection = detect_corner_metadata(image)
    assert detection.bbox is not None
    assert detection.confidence >= 0.72

    result = remove_detected_metadata(image, detection)
    assert result.getpixel((20, 20))[3] == 0
    assert result.getpixel((120, 80))[3] == 255


def test_artwork_outside_metadata_zone_is_not_detected() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 40, 150, 120), fill=(255, 0, 0, 255))

    detection = detect_corner_metadata(image)
    assert detection.bbox is None


def test_ambiguous_multiple_corner_components_are_not_auto_selected() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((6, 6, 22, 22), fill=(180, 220, 120, 255))
    draw.ellipse((28, 6, 44, 22), fill=(180, 220, 120, 255))

    detection = detect_corner_metadata(image)
    assert detection.mask is None
    assert "ambiguous" in detection.reason
