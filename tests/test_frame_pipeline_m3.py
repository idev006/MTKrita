from PIL import Image, ImageDraw

from mtkrita.frame_pipeline import FramePipelineConfig
from mtkrita.frame_pipeline_m3 import process_frame_with_m3
from mtkrita.models import FrameStatus, ProcessingMode


def test_opaque_black_frame_becomes_transparent_and_continues_pipeline() -> None:
    image = Image.new("RGB", (120, 100), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((18, 12, 102, 88), radius=10, fill=(255, 255, 255))
    draw.rectangle((45, 35, 75, 65), fill=(220, 40, 80))
    cfg = FramePipelineConfig(
        target_size=(120, 100),
        margin=0,
        remove_border=False,
        remove_metadata=False,
    )

    output = process_frame_with_m3(image, index=1, row=0, column=0, config=cfg)

    assert output.result.status == FrameStatus.AUTO_FIXED
    assert output.result.processing_mode == ProcessingMode.OPAQUE
    assert "REMOVE_OPAQUE_BACKGROUND" in output.result.actions
    assert output.image.mode == "RGBA"
    assert output.image.getpixel((0, 0))[3] == 0
    assert output.image.getpixel((60, 50))[3] == 255
    assert output.result.evidence["source_background_route"] == "REMOVE_BACKGROUND"
    assert output.result.evidence["m3_background_status"] == "SAFE_REMOVE"


def test_m3_preserves_enclosed_black_detail() -> None:
    image = Image.new("RGB", (120, 100), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 15, 100, 85), fill=(255, 255, 255))
    draw.rectangle((50, 40, 70, 60), fill=(0, 0, 0))
    cfg = FramePipelineConfig(
        target_size=(120, 100),
        margin=0,
        remove_border=False,
        remove_metadata=False,
    )

    output = process_frame_with_m3(image, index=1, row=0, column=0, config=cfg)

    assert output.result.status == FrameStatus.AUTO_FIXED
    assert output.image.getpixel((60, 50))[3] == 255


def test_unsupported_opaque_boundary_routes_review_without_mutation() -> None:
    image = Image.new("RGB", (120, 100), (180, 180, 180))
    ImageDraw.Draw(image).rectangle((25, 20, 95, 80), fill=(255, 0, 0))
    before = image.tobytes()

    output = process_frame_with_m3(image, index=1, row=0, column=0)

    assert output.result.status == FrameStatus.REVIEW
    assert output.result.processing_mode == ProcessingMode.OPAQUE
    assert output.result.findings[0].code == "BACKGROUND.REMOVAL_AMBIGUOUS"
    assert image.tobytes() == before


def test_transparent_input_uses_existing_pipeline_without_m3_action() -> None:
    image = Image.new("RGBA", (120, 100), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((25, 20, 95, 80), fill=(255, 255, 255, 255))
    cfg = FramePipelineConfig(
        target_size=(120, 100),
        margin=0,
        remove_border=False,
        remove_metadata=False,
    )

    output = process_frame_with_m3(image, index=1, row=0, column=0, config=cfg)

    assert "REMOVE_OPAQUE_BACKGROUND" not in output.result.actions
    assert output.result.processing_mode == ProcessingMode.TRANSPARENT
