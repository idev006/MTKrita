from PIL import Image

from mtkrita.line_profile import validate_static_sticker


def test_line_profile_accepts_visible_transparent_canvas_within_limits() -> None:
    image = Image.new("RGBA", (320, 300), (0, 0, 0, 0))
    image.putpixel((160, 150), (255, 255, 255, 255))
    result = validate_static_sticker(image)
    assert result.valid is True
    assert result.findings == ()


def test_line_profile_rejects_oversize_odd_and_opaque() -> None:
    image = Image.new("RGB", (371, 321), (255, 255, 255))
    result = validate_static_sticker(image)
    assert result.valid is False
    assert "DIMENSIONS_EXCEED_PROFILE" in result.findings
    assert "DIMENSIONS_NOT_EVEN" in result.findings
    assert "NO_TRANSPARENT_PIXELS" in result.findings


def test_line_profile_rejects_fully_transparent_empty_canvas() -> None:
    image = Image.new("RGBA", (320, 300), (0, 0, 0, 0))
    result = validate_static_sticker(image)
    assert result.valid is False
    assert "NO_VISIBLE_CONTENT" in result.findings
