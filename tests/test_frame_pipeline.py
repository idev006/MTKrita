from PIL import Image, ImageDraw

from mtkrita.frame_pipeline import FramePipelineConfig, process_frame
from mtkrita.models import FrameStatus, ProcessingMode
from mtkrita.routing import BackgroundRoute


def test_transparent_frame_runs_headless_to_autofixed_result() -> None:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((30, 20, 69, 59), fill=(255, 0, 0, 255))

    output = process_frame(
        image,
        index=1,
        row=0,
        column=0,
        config=FramePipelineConfig(remove_border=False, remove_metadata=False),
    )

    assert output.transparency.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
    assert output.result.processing_mode == ProcessingMode.TRANSPARENT
    assert output.result.status == FrameStatus.AUTO_FIXED
    assert output.result.content_bbox is not None
    assert "SMART_FIT" in output.result.actions


def test_opaque_frame_remains_opaque_route_after_metadata_cleanup() -> None:
    image = Image.new("RGB", (200, 160), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 34, 34), fill=(180, 220, 120))
    draw.rectangle((90, 50, 150, 120), fill=(230, 120, 40))

    output = process_frame(
        image,
        index=2,
        row=0,
        column=1,
        config=FramePipelineConfig(remove_border=False),
    )

    assert output.transparency.route == BackgroundRoute.REMOVE_BACKGROUND
    assert output.transparency.provenance == "pre_metadata_frame"
    assert output.result.processing_mode == ProcessingMode.OPAQUE
    assert output.result.status == FrameStatus.REVIEW
    assert "REMOVE_FRAME_METADATA" in output.result.actions
    assert any(finding.code == "BACKGROUND.REMOVAL_REQUIRED" for finding in output.result.findings)
    assert output.image.convert("RGBA").getchannel("A").getextrema()[0] == 0


def test_ambiguous_metadata_routes_review_without_destructive_cleanup() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((6, 6, 22, 22), fill=(180, 220, 120, 255))
    draw.ellipse((28, 6, 44, 22), fill=(180, 220, 120, 255))
    draw.rectangle((90, 50, 150, 120), fill=(230, 120, 40, 255))

    output = process_frame(
        image,
        index=3,
        row=0,
        column=2,
        config=FramePipelineConfig(remove_border=False),
    )

    assert output.result.status == FrameStatus.REVIEW
    assert "REMOVE_FRAME_METADATA" not in output.result.actions
    assert any(finding.code == "METADATA.AMBIGUOUS" for finding in output.result.findings)
