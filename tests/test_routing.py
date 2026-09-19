from PIL import Image

from mtkrita.routing import BackgroundRoute, decide_background_route


def test_rgb_routes_to_background_removal() -> None:
    image = Image.new("RGB", (8, 8), (255, 255, 255))
    decision = decide_background_route(image)
    assert decision.route == BackgroundRoute.REMOVE_BACKGROUND
    assert decision.has_alpha_channel is False
    assert decision.meaningful_transparency is False


def test_fully_opaque_rgba_routes_to_background_removal() -> None:
    image = Image.new("RGBA", (8, 8), (255, 255, 255, 255))
    decision = decide_background_route(image)
    assert decision.route == BackgroundRoute.REMOVE_BACKGROUND
    assert decision.has_alpha_channel is True
    assert decision.meaningful_transparency is False


def test_meaningful_transparency_skips_background_removal() -> None:
    image = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
    image.putpixel((0, 0), (255, 255, 255, 0))
    decision = decide_background_route(image)
    assert decision.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
    assert decision.meaningful_transparency is True
    assert decision.transparent_pixel_ratio == 0.01


def test_single_nearly_opaque_pixel_does_not_count_as_transparent() -> None:
    image = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
    image.putpixel((0, 0), (255, 255, 255, 254))
    decision = decide_background_route(image, transparent_alpha_threshold=253)
    assert decision.route == BackgroundRoute.REMOVE_BACKGROUND
