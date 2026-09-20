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
        extraction_rect=(0, 0, 100, 80),
        extraction_method="configured_exact",
        extraction_confidence=1.0,
        config=FramePipelineConfig(remove_border=False, remove_metadata=False),
    )

    assert output.transparency.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
    assert output.result.processing_mode == ProcessingMode.TRANSPARENT
    assert output.result.status == FrameStatus.AUTO_FIXED
    assert output.result.content_bbox is not None
    assert output.result.extraction_method == "configured_exact"
    assert output.result.extraction_confidence == 1.0
    assert output.result.evidence["route_provenance"] == "pre_metadata_frame"
    assert output.result.evidence["background_route"] == "skip_remove_background"
    assert "SMART_FIT" in output.result.actions


def test_opaque_frame_preserves_metadata_as_plan_for_m3_without_alpha_mutation() -> None:
    image = Image.new("RGB", (200, 160), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 34, 34), fill=(180, 220, 120))
    draw.rectangle((90, 50, 150, 120), fill=(230, 120, 40))

    output = process_frame(
        image,
        index=2,
        row=0,
        column=1,
        extraction_method="configured_scaled",
        extraction_confidence=0.97,
        config=FramePipelineConfig(remove_border=False),
    )

    assert output.transparency.route == BackgroundRoute.REMOVE_BACKGROUND
    assert output.transparency.provenance == "pre_metadata_frame"
    assert output.result.processing_mode == ProcessingMode.OPAQUE
    assert output.result.status == FrameStatus.REVIEW
    assert output.result.evidence["background_route"] == "remove_background"
    assert output.result.evidence["metadata_bbox"] is not None
    assert output.result.evidence["metadata_anchored_candidate_count"] == 1
    assert output.result.evidence["metadata_dominance_margin"] == 1.0
    assert output.result.extraction_method == "configured_scaled"
    assert "PLAN_FRAME_METADATA" in output.result.actions
    assert "REMOVE_FRAME_METADATA" not in output.result.actions
    assert any(finding.code == "BACKGROUND.REMOVAL_REQUIRED" for finding in output.result.findings)
    assert output.image.convert("RGBA").getchannel("A").getextrema() == (255, 255)


def test_ambiguous_metadata_routes_review_without_destructive_cleanup() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 5, 16, 17), fill=(180, 220, 120, 255))
    draw.ellipse((18, 5, 30, 17), fill=(180, 220, 120, 255))
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
    assert output.result.evidence["metadata_anchored_candidate_count"] == 2
    assert output.result.evidence["metadata_dominance_margin"] is not None
    assert "ambiguous" in str(output.result.evidence["metadata_reason"]).lower()
    assert any(finding.code == "METADATA.AMBIGUOUS" for finding in output.result.findings)


def test_frame_result_serialization_retains_evidence() -> None:
    image = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((10, 10, 29, 29), fill=(255, 255, 255, 255))
    output = process_frame(
        image,
        index=4,
        row=0,
        column=3,
        config=FramePipelineConfig(remove_border=False, remove_metadata=False),
    )
    payload = output.result.to_dict()
    assert payload["index"] == 4
    assert payload["evidence"]["route_provenance"] == "pre_metadata_frame"
    assert "providers" in payload
    assert "output_sha256" in payload


def test_border_contact_risk_routes_to_review_without_crop() -> None:
    border_color = (20, 120, 230, 255)
    image = Image.new("RGBA", (80, 60), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for offset in range(4):
        draw.rectangle((offset, offset, 79 - offset, 59 - offset), outline=border_color)
    draw.rectangle((4, 20, 15, 35), fill=border_color)

    output = process_frame(
        image,
        index=5,
        row=0,
        column=4,
        config=FramePipelineConfig(remove_metadata=False),
    )

    assert output.result.status == FrameStatus.REVIEW
    assert output.result.evidence["border_contact_risk"] is True
    sides = output.result.evidence["border_sides"]
    assert isinstance(sides, dict)
    assert sides["left"]["contact_fraction"] > 0
    assert sides["left"]["contact_ranges"] == ((20, 36),)
    assert "REMOVE_BORDER" not in output.result.actions
    assert output.image.size == image.size
    assert any(finding.code == "BORDER.CONTACT_RISK" for finding in output.result.findings)


def test_inset_border_evidence_records_per_side_offset_and_thickness() -> None:
    image = Image.new("RGBA", (96, 80), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    color = (160, 220, 100, 255)
    for offset in range(6, 9):
        draw.rectangle((offset, offset, 95 - offset, 79 - offset), outline=color)
    draw.rectangle((28, 22, 67, 57), fill=(240, 100, 80, 255))

    output = process_frame(
        image,
        index=6,
        row=1,
        column=0,
        config=FramePipelineConfig(remove_metadata=False),
    )

    sides = output.result.evidence["border_sides"]
    assert isinstance(sides, dict)
    assert sides["left"]["offset"] == 6
    assert sides["left"]["thickness"] == 3
    assert sides["left"]["contact_fraction"] == 0.0
    assert sides["left"]["contact_ranges"] == ()
    assert sides["top"]["offset"] == 6
    assert output.result.evidence["border_contact_risk"] is False
    assert output.result.evidence["border_consensus_mode"] == "single_tone"
    assert "REMOVE_BORDER" in output.result.actions


def test_safe_transparent_border_badge_overlap_uses_joint_cleanup() -> None:
    image = Image.new("RGBA", (96, 80), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    border_color = (160, 220, 100, 255)
    for offset in range(6, 9):
        draw.rectangle((offset, offset, 95 - offset, 79 - offset), outline=border_color)
    # Entire non-border badge topology remains inside the configured anchor envelope.
    draw.ellipse((1, 1, 14, 14), fill=border_color)
    draw.rectangle((32, 24, 63, 55), fill=(240, 100, 80, 255))

    output = process_frame(
        image,
        index=7,
        row=1,
        column=1,
    )

    assert output.transparency.route == BackgroundRoute.SKIP_REMOVE_BACKGROUND
    assert output.result.evidence["border_contact_risk"] is True
    assert output.result.evidence["metadata_requires_joint_cleanup"] is True
    assert output.result.evidence["metadata_fragment_association_resolved"] is True
    assert output.result.evidence["joint_cleanup_status"] == "SAFE_PLAN"
    assert output.result.evidence["joint_cleanup_unexplained_contact_fraction"] == 0.0
    assert "JOINT_BORDER_METADATA_CLEANUP" in output.result.actions
    assert not any(finding.code == "BORDER.CONTACT_RISK" for finding in output.result.findings)
    assert output.result.status == FrameStatus.AUTO_FIXED


def test_opaque_border_badge_overlap_never_mutates_or_bypasses_m3() -> None:
    image = Image.new("RGBA", (96, 80), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    border_color = (160, 220, 100, 255)
    for offset in range(6, 9):
        draw.rectangle((offset, offset, 95 - offset, 79 - offset), outline=border_color)
    draw.ellipse((1, 1, 14, 14), fill=border_color)
    draw.rectangle((32, 24, 63, 55), fill=(240, 100, 80, 255))

    output = process_frame(
        image,
        index=8,
        row=1,
        column=2,
    )

    assert output.transparency.route == BackgroundRoute.REMOVE_BACKGROUND
    assert output.result.status == FrameStatus.REVIEW
    assert "JOINT_BORDER_METADATA_CLEANUP" not in output.result.actions
    assert "REMOVE_FRAME_METADATA" not in output.result.actions
    assert output.image.getchannel("A").getextrema() == (255, 255)
    assert output.result.evidence["background_route"] == "remove_background"
