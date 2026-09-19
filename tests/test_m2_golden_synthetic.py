from pathlib import Path

from PIL import Image, ImageDraw

from mtkrita.exporter import bind_export_artifact, export_png_atomic
from mtkrita.frame_pipeline import process_frame
from mtkrita.manifest import create_manifest, write_manifest
from mtkrita.models import FrameStatus, ProcessingMode
from mtkrita.sheet import ExtractionMethod, GridSpec, split_grid_scaled


def _synthetic_transparent_sheet() -> Image.Image:
    frame_size = (80, 60)
    sheet = Image.new("RGBA", (frame_size[0] * 5, frame_size[1] * 2), (0, 0, 0, 0))
    for index in range(10):
        cell = Image.new("RGBA", frame_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(cell)
        for offset in range(3):
            draw.rectangle(
                (offset, offset, frame_size[0] - 1 - offset, frame_size[1] - 1 - offset),
                outline=(180, 220, 80, 255),
            )
        # Compact top-left sheet metadata badge.
        draw.rectangle((7, 7, 13, 13), fill=(220, 180, 80, 255))
        # Sticker artwork safely separated from frame metadata/border.
        draw.rectangle((28, 20, 51, 43), fill=(240, 80 + index, 60, 255))
        x = (index % 5) * frame_size[0]
        y = (index // 5) * frame_size[1]
        sheet.alpha_composite(cell, dest=(x, y))
    return sheet


def test_m2_synthetic_ten_frame_end_to_end(tmp_path: Path) -> None:
    source = tmp_path / "synthetic_sheet.png"
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    sheet = _synthetic_transparent_sheet()
    sheet.save(source, format="PNG")

    manifest = create_manifest(source, config_text="synthetic-m2-golden-v1")
    source_hash_before = manifest.input_hash

    split = split_grid_scaled(sheet, GridSpec(rows=2, columns=5))
    assert split.method == ExtractionMethod.CONFIGURED_EXACT
    assert split.confidence == 1.0
    assert len(split.frames) == 10

    for frame in split.frames:
        processed = process_frame(
            frame.image,
            index=frame.index,
            row=frame.row,
            column=frame.column,
            extraction_rect=frame.box,
            extraction_method=split.method.value,
            extraction_confidence=split.confidence,
        )
        assert processed.result.status == FrameStatus.AUTO_FIXED
        assert processed.result.processing_mode == ProcessingMode.TRANSPARENT
        assert "REMOVE_BORDER" in processed.result.actions
        assert "REMOVE_FRAME_METADATA" in processed.result.actions
        assert processed.result.evidence["route_provenance"] == "pre_metadata_frame"
        assert processed.result.evidence["background_route"] == "skip_remove_background"

        artifact = export_png_atomic(processed.image, output_dir / f"{frame.index:02d}.png")
        bind_export_artifact(processed.result, artifact)
        assert processed.result.output_sha256 == artifact.sha256
        assert len(artifact.sha256) == 64
        manifest.frames.append(processed.result)

    manifest_path = write_manifest(manifest, tmp_path / "job")
    assert manifest_path.exists()
    assert len(manifest.frames) == 10
    assert all(frame.output_file for frame in manifest.frames)
    assert all(frame.output_sha256 for frame in manifest.frames)

    # Re-inspecting the immutable source must produce the same source identity.
    after = create_manifest(source)
    assert after.input_hash == source_hash_before
