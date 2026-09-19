from PIL import Image, ImageDraw

from mtkrita.frame_pipeline import FramePipelineConfig, process_frame


def test_metadata_segmentation_basis_is_propagated_to_frame_evidence() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 34, 34), fill=(180, 220, 120, 255))
    draw.rectangle((90, 50, 150, 120), fill=(230, 120, 40, 255))

    output = process_frame(
        image,
        index=1,
        row=0,
        column=0,
        config=FramePipelineConfig(remove_border=False),
    )

    assert output.result.evidence["metadata_segmentation_basis"] == "alpha_visible"
    assert output.result.evidence["metadata_alpha_visibility_threshold"] == 8


def test_opaque_metadata_segmentation_basis_is_propagated_to_frame_evidence() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 34, 34), fill=(180, 220, 120, 255))
    draw.rectangle((90, 50, 150, 120), fill=(230, 120, 40, 255))

    output = process_frame(
        image,
        index=2,
        row=0,
        column=1,
        config=FramePipelineConfig(remove_border=False),
    )

    assert output.result.evidence["metadata_segmentation_basis"] == "rgb_background_distance"
    assert output.result.evidence["metadata_alpha_visibility_threshold"] == 8
