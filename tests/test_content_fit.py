from PIL import Image, ImageDraw

from mtkrita.content import analyze_alpha_content
from mtkrita.fit import fit_rgba_to_canvas


def test_alpha_content_bounds_and_edge_contact() -> None:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((10, 12, 59, 51), fill=(255, 0, 0, 255))
    result = analyze_alpha_content(image)
    assert result.bbox == (10, 12, 60, 52)
    assert result.touches_edge is False
    assert result.occupancy_ratio == (50 * 40) / (100 * 80)


def test_alpha_content_detects_edge_contact() -> None:
    image = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((0, 5, 4, 10), fill=(255, 255, 255, 255))
    assert analyze_alpha_content(image).touches_edge is True


def test_smart_fit_does_not_upscale_by_default() -> None:
    image = Image.new("RGBA", (30, 20), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((5, 5, 14, 14), fill=(0, 0, 0, 255))
    result = fit_rgba_to_canvas(image, (100, 80), margin=10)
    assert result.scale == 1.0
    assert result.image.size == (100, 80)
    assert result.source_bbox == (5, 5, 15, 15)


def test_smart_fit_scales_down_to_safe_margin() -> None:
    image = Image.new("RGBA", (200, 200), (255, 0, 0, 255))
    result = fit_rgba_to_canvas(image, (100, 80), margin=10)
    assert result.scale == 0.3
    bounds = analyze_alpha_content(result.image).bbox
    assert bounds is not None
    left, top, right, bottom = bounds
    assert left >= 10 and top >= 10
    assert right <= 90 and bottom <= 70
