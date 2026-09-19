from pathlib import Path

from PIL import Image

from mtkrita.inspector import inspect_image, sha256_file


def test_inspect_rgba_reports_meaningful_alpha(tmp_path: Path) -> None:
    source = tmp_path / "alpha.png"
    image = Image.new("RGBA", (4, 4), (255, 0, 0, 255))
    image.putpixel((0, 0), (255, 0, 0, 0))
    image.save(source)

    before = sha256_file(source)
    result = inspect_image(source)
    after = sha256_file(source)

    assert result.format == "PNG"
    assert result.width == 4
    assert result.height == 4
    assert result.has_alpha is True
    assert result.alpha_min == 0
    assert result.alpha_max == 255
    assert result.transparent_pixel_ratio == 1 / 16
    assert before == after == result.sha256


def test_inspect_rgb_has_no_alpha(tmp_path: Path) -> None:
    source = tmp_path / "opaque.png"
    Image.new("RGB", (3, 2), (255, 255, 255)).save(source)

    result = inspect_image(source)

    assert result.has_alpha is False
    assert result.alpha_min is None
    assert result.alpha_max is None
    assert result.transparent_pixel_ratio is None
