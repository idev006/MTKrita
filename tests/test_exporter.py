from pathlib import Path

from PIL import Image

from mtkrita.exporter import bind_export_artifact, export_png_atomic
from mtkrita.models import FrameResult


def test_atomic_export_writes_png_and_hash(tmp_path: Path) -> None:
    image = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    image.putpixel((10, 10), (255, 255, 255, 255))
    target = tmp_path / "01.png"

    artifact = export_png_atomic(image, target)

    assert target.exists()
    assert artifact.path == target
    assert len(artifact.sha256) == 64
    assert artifact.byte_size == target.stat().st_size
    assert not list(tmp_path.glob(".*.tmp"))


def test_atomic_export_refuses_existing_target_by_default(tmp_path: Path) -> None:
    target = tmp_path / "01.png"
    target.write_bytes(b"existing")
    image = Image.new("RGBA", (10, 10), (0, 0, 0, 0))

    try:
        export_png_atomic(image, target)
    except FileExistsError:
        pass
    else:
        raise AssertionError("expected overwrite refusal")

    assert target.read_bytes() == b"existing"


def test_export_artifact_binds_to_frame_result(tmp_path: Path) -> None:
    image = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    image.putpixel((5, 5), (255, 0, 0, 255))
    artifact = export_png_atomic(image, tmp_path / "02.png")
    frame = FrameResult(index=2, row=0, column=1)

    bind_export_artifact(frame, artifact)

    assert frame.output_file == str(artifact.path)
    assert frame.output_sha256 == artifact.sha256
