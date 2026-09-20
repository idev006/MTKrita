from PIL import Image, ImageDraw

from mtkrita.frame_pipeline import FramePipelineConfig, process_frame
from mtkrita.models import FrameStatus
from mtkrita.routing import BackgroundRoute

_RING = (160, 220, 100, 255)
_ART = (240, 100, 80, 255)


def _draw_ring(image: Image.Image, *, start: int = 6, end: int = 10) -> None:
    draw = ImageDraw.Draw(image)
    for offset in range(start, end):
        draw.rectangle(
            (offset, offset, image.width - 1 - offset, image.height - 1 - offset),
            outline=_RING,
        )


def test_frame_pipeline_uses_exact_closed_ring_before_seed_crop() -> None:
    image = Image.new("RGBA", (120, 100), (0, 0, 0, 0))
    _draw_ring(image)
    ImageDraw.Draw(image).rectangle((42, 34, 77, 69), fill=_ART)

    output = process_frame(
        image,
        index=1,
        row=0,
        column=0,
        config=FramePipelineConfig(remove_metadata=False),
    )

    assert output.transparency.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
    assert output.result.status == FrameStatus.AUTO_FIXED
    assert output.result.evidence["route_provenance"] == "pre_metadata_frame"
    assert output.result.evidence["closed_ring_status"] == "SAFE_RING"
    assert "REMOVE_CLOSED_RING" in output.result.actions
    assert "REMOVE_BORDER" not in output.result.actions
    assert output.result.evidence["closed_ring_mask_sha256"] is not None


def test_frame_pipeline_joint_ring_badge_cleanup_is_automatic() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _draw_ring(image)
    draw = ImageDraw.Draw(image)
    draw.ellipse((2, 2, 16, 16), fill=_RING)
    draw.rectangle((35, 35, 64, 64), fill=_ART)

    output = process_frame(image, index=2, row=0, column=1)

    assert output.transparency.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
    assert output.result.status == FrameStatus.AUTO_FIXED
    assert output.result.evidence["closed_ring_status"] == "RING_WITH_CONTACT"
    assert output.result.evidence["joint_cleanup_status"] == "SAFE_PLAN"
    assert output.result.evidence["joint_cleanup_unexplained_contact_fraction"] == 0.0
    assert "JOINT_RING_METADATA_CLEANUP" in output.result.actions
    assert "JOINT_BORDER_METADATA_CLEANUP" not in output.result.actions
    assert not any(finding.code == "RING.CONTACT_RISK" for finding in output.result.findings)


def test_frame_pipeline_remote_ring_contact_remains_review() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    _draw_ring(image)
    draw = ImageDraw.Draw(image)
    draw.ellipse((2, 2, 16, 16), fill=_RING)
    draw.rectangle((35, 35, 64, 64), fill=_ART)
    # Same-palette interior contact on the right is remote from the top-left badge.
    x = image.width - 1 - 10
    draw.line((x, 40, x, 60), fill=_RING, width=1)

    output = process_frame(image, index=3, row=0, column=2)

    assert output.result.status == FrameStatus.REVIEW
    assert output.result.evidence["closed_ring_status"] == "RING_WITH_CONTACT"
    assert output.result.evidence["joint_cleanup_status"] == "REVIEW"
    assert "REMOVE_CLOSED_RING" not in output.result.actions
    assert "JOINT_RING_METADATA_CLEANUP" not in output.result.actions
    assert any(finding.code == "RING.CONTACT_RISK" for finding in output.result.findings)


def test_frame_pipeline_opaque_input_does_not_apply_ring_alpha_cleanup() -> None:
    image = Image.new("RGBA", (100, 100), (20, 20, 20, 255))
    _draw_ring(image)
    ImageDraw.Draw(image).rectangle((35, 35, 64, 64), fill=_ART)

    output = process_frame(image, index=4, row=0, column=3)

    assert output.transparency.route == BackgroundRoute.REMOVE_BACKGROUND
    assert output.result.status == FrameStatus.REVIEW
    assert "REMOVE_CLOSED_RING" not in output.result.actions
    assert "JOINT_RING_METADATA_CLEANUP" not in output.result.actions
    assert output.image.convert("RGBA").getchannel("A").getextrema() == (255, 255)
    assert any(finding.code == "BACKGROUND.REMOVAL_REQUIRED" for finding in output.result.findings)
