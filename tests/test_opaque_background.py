from PIL import Image, ImageDraw

from mtkrita.opaque_background import (
    OpaqueBackgroundStatus,
    apply_opaque_background_removal,
    plan_opaque_background_removal,
)


def _black_canvas() -> Image.Image:
    return Image.new("RGB", (100, 100), (0, 0, 0))


def test_uniform_black_background_is_removed() -> None:
    image = _black_canvas()
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 80, 80), fill=(255, 255, 255))

    plan = plan_opaque_background_removal(image)
    output = apply_opaque_background_removal(image, plan)

    assert plan.status == OpaqueBackgroundStatus.SAFE_REMOVE
    assert plan.boundary_dark_fraction == 1.0
    assert output.mode == "RGBA"
    assert output.getpixel((0, 0))[3] == 0
    assert output.getpixel((50, 50))[3] == 255


def test_enclosed_black_text_like_detail_is_preserved() -> None:
    image = _black_canvas()
    draw = ImageDraw.Draw(image)
    draw.rectangle((15, 15, 85, 85), fill=(255, 255, 255))
    draw.rectangle((40, 40, 60, 60), fill=(0, 0, 0))

    plan = plan_opaque_background_removal(image)
    output = apply_opaque_background_removal(image, plan)

    assert plan.status == OpaqueBackgroundStatus.SAFE_REMOVE
    assert output.getpixel((50, 50))[3] == 255


def test_disconnected_foreground_islands_are_preserved() -> None:
    image = _black_canvas()
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 35, 35), fill=(255, 0, 0))
    draw.rectangle((65, 65, 80, 80), fill=(0, 180, 255))

    plan = plan_opaque_background_removal(image)
    output = apply_opaque_background_removal(image, plan)

    assert plan.status == OpaqueBackgroundStatus.SAFE_REMOVE
    assert output.getpixel((25, 25))[3] == 255
    assert output.getpixel((70, 70))[3] == 255


def test_nonuniform_bright_boundary_routes_review() -> None:
    image = Image.new("RGB", (100, 100), (180, 180, 180))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 80, 80), fill=(255, 0, 0))

    plan = plan_opaque_background_removal(image)

    assert plan.status == OpaqueBackgroundStatus.REVIEW
    assert plan.alpha is None


def test_excessive_removal_routes_review() -> None:
    image = _black_canvas()
    ImageDraw.Draw(image).rectangle((48, 48, 51, 51), fill=(255, 255, 255))

    plan = plan_opaque_background_removal(image, max_removed_ratio=0.90)

    assert plan.status == OpaqueBackgroundStatus.REVIEW
    assert plan.alpha is None


def test_already_transparent_source_is_not_eligible() -> None:
    image = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    image.putpixel((0, 0), (255, 0, 0, 0))

    plan = plan_opaque_background_removal(image)

    assert plan.status == OpaqueBackgroundStatus.NOT_ELIGIBLE
    assert plan.alpha is None


def test_planner_is_deterministic() -> None:
    image = _black_canvas()
    ImageDraw.Draw(image).ellipse((20, 20, 80, 80), fill=(255, 255, 255))

    first = plan_opaque_background_removal(image)
    second = plan_opaque_background_removal(image)

    assert first == second


def test_source_image_is_immutable() -> None:
    image = _black_canvas()
    ImageDraw.Draw(image).rectangle((20, 20, 80, 80), fill=(255, 255, 255))
    before = image.tobytes()

    plan = plan_opaque_background_removal(image)
    _ = apply_opaque_background_removal(image, plan)

    assert image.mode == "RGB"
    assert image.tobytes() == before
