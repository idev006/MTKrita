from PIL import Image, ImageDraw

from mtkrita.border import BorderDetection, BorderSide
from mtkrita.frame_pipeline import FramePipelineConfig, process_frame
from mtkrita.models import FrameStatus


def _side(
    name: str,
    ranges: tuple[tuple[int, int], ...],
    *,
    side_length: int,
) -> BorderSide:
    offset = 6
    thickness = 3
    sample_count = side_length - (2 * (offset + thickness))
    fraction = sum(end - start for start, end in ranges) / sample_count
    return BorderSide(
        side=name,
        thickness=thickness,
        color=(20, 120, 230),
        confidence=1.0,
        contact_risk=fraction >= 0.05,
        offset=offset,
        contact_fraction=fraction,
        contact_ranges=ranges,
    )


def _image() -> Image.Image:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((35, 25, 64, 54), fill=(240, 100, 80, 255))
    return image


def test_frame_pipeline_uses_residual_contact_after_reciprocal_corner_explanation(
    monkeypatch,
) -> None:
    detection = BorderDetection(
        left=_side("left", ((3, 9),), side_length=80),
        top=_side("top", ((2, 8),), side_length=100),
        right=None,
        bottom=None,
        consensus_mode="single_tone",
    )
    monkeypatch.setattr("mtkrita.frame_pipeline.detect_border", lambda image: detection)

    output = process_frame(
        _image(),
        index=1,
        row=0,
        column=0,
        config=FramePipelineConfig(remove_metadata=False),
    )

    assert output.result.status == FrameStatus.AUTO_FIXED
    assert output.result.evidence["border_contact_risk"] is False
    sides = output.result.evidence["border_sides"]
    assert sides["top"]["raw_contact_ranges"] == ((2, 8),)
    assert sides["top"]["explained_corner_ranges"] == ((2, 8),)
    assert sides["top"]["contact_ranges"] == ()
    assert sides["top"]["contact_fraction"] == 0.0
    assert sides["left"]["raw_contact_ranges"] == ((3, 9),)
    assert sides["left"]["explained_corner_ranges"] == ((3, 9),)
    assert sides["left"]["contact_ranges"] == ()
    assert "REMOVE_BORDER" in output.result.actions


def test_frame_pipeline_keeps_central_contact_as_review_after_corner_explanation(
    monkeypatch,
) -> None:
    detection = BorderDetection(
        left=_side("left", ((3, 9),), side_length=80),
        top=_side("top", ((2, 8), (40, 50)), side_length=100),
        right=None,
        bottom=None,
        consensus_mode="single_tone",
    )
    monkeypatch.setattr("mtkrita.frame_pipeline.detect_border", lambda image: detection)
    source = _image()

    output = process_frame(
        source,
        index=2,
        row=0,
        column=1,
        config=FramePipelineConfig(remove_metadata=False),
    )

    assert output.result.status == FrameStatus.REVIEW
    assert output.result.evidence["border_contact_risk"] is True
    sides = output.result.evidence["border_sides"]
    assert sides["top"]["raw_contact_ranges"] == ((2, 8), (40, 50))
    assert sides["top"]["explained_corner_ranges"] == ((2, 8),)
    assert sides["top"]["contact_ranges"] == ((40, 50),)
    assert sides["top"]["contact_fraction"] > 0.05
    assert "REMOVE_BORDER" not in output.result.actions
    assert output.image.size == source.size
    assert any(finding.code == "BORDER.CONTACT_RISK" for finding in output.result.findings)
