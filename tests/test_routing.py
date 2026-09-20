from PIL import Image, ImageDraw

from mtkrita.metadata import detect_corner_metadata, remove_detected_metadata
from mtkrita.routing import (
    BackgroundRoute,
    decide_background_route,
    decide_source_background_route,
)


def test_rgb_routes_to_background_removal() -> None:
    image = Image.new("RGB", (8, 8), (255, 255, 255))
    decision = decide_source_background_route(image)
    assert decision.route == BackgroundRoute.REMOVE_BACKGROUND
    assert decision.has_alpha_channel is False
    assert decision.meaningful_transparency is False
    assert decision.provenance == "pre_metadata_frame"


def test_fully_opaque_rgba_routes_to_background_removal() -> None:
    image = Image.new("RGBA", (8, 8), (255, 255, 255, 255))
    decision = decide_source_background_route(image)
    assert decision.route == BackgroundRoute.REMOVE_BACKGROUND
    assert decision.has_alpha_channel is True
    assert decision.meaningful_transparency is False


def test_meaningful_source_transparency_skips_background_removal() -> None:
    image = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
    image.putpixel((0, 0), (255, 255, 255, 0))
    decision = decide_source_background_route(image)
    assert decision.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
    assert decision.meaningful_transparency is True
    assert decision.transparent_pixel_ratio == 0.01


def test_single_nearly_opaque_pixel_does_not_count_as_transparent() -> None:
    image = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
    image.putpixel((0, 0), (255, 255, 255, 254))
    decision = decide_source_background_route(image, transparent_alpha_threshold=253)
    assert decision.route == BackgroundRoute.REMOVE_BACKGROUND


def test_metadata_generated_alpha_does_not_change_captured_source_route() -> None:
    source = Image.new("RGB", (200, 160), (0, 0, 0))
    draw = ImageDraw.Draw(source)
    draw.ellipse((8, 8, 34, 34), fill=(180, 220, 120))
    draw.rectangle((90, 50, 150, 120), fill=(230, 120, 40))

    source_decision = decide_source_background_route(source)
    assert source_decision.route == BackgroundRoute.REMOVE_BACKGROUND

    detection = detect_corner_metadata(source)
    assert detection.bbox is not None
    cleaned = remove_detected_metadata(source, detection)
    assert cleaned.getchannel("A").getextrema()[0] == 0

    # Cleanup-created alpha must not replace the already-captured source decision.
    assert source_decision.route == BackgroundRoute.REMOVE_BACKGROUND

    # Demonstrate the failure mode that the orchestrator must avoid.
    post_cleanup_decision = decide_background_route(cleaned)
    assert post_cleanup_decision.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
