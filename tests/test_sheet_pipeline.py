import json

from PIL import Image, ImageDraw

from mtkrita.frame_pipeline import FramePipelineConfig
from mtkrita.models import FrameStatus
from mtkrita.sheet_pipeline import process_sheet_file


def _synthetic_opaque_sheet() -> Image.Image:
    image = Image.new("RGB", (500, 200), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    for row in range(2):
        for column in range(5):
            left = column * 100
            top = row * 100
            ring = (160, 220, 100)
            for inset in range(5, 9):
                draw.rectangle(
                    (left + inset, top + inset, left + 99 - inset, top + 99 - inset),
                    outline=ring,
                )
            draw.rounded_rectangle(
                (left + 20, top + 18, left + 80, top + 82),
                radius=8,
                fill=(255, 255, 255),
            )
            draw.rectangle(
                (left + 40, top + 40, left + 60, top + 62),
                fill=(220, 40, 80),
            )
    return image


def test_sheet_pipeline_extracts_and_exports_ten_frames(tmp_path) -> None:
    source = tmp_path / "sheet.png"
    output_dir = tmp_path / "out"
    _synthetic_opaque_sheet().save(source)
    cfg = FramePipelineConfig(
        target_size=(100, 100),
        margin=0,
        remove_border=True,
        remove_metadata=False,
    )

    output = process_sheet_file(source, output_dir, frame_config=cfg)

    assert output.summary.frame_count == 10
    assert output.summary.review_count == 0
    assert output.summary.fail_count == 0
    assert output.summary.auto_fixed_count == 10
    assert all(frame.status == FrameStatus.AUTO_FIXED for frame in output.frames)
    assert all((output_dir / f"{index:02d}.png").is_file() for index in range(1, 11))
    assert (output_dir / "report.json").is_file()

    with Image.open(output_dir / "01.png") as first:
        assert first.mode == "RGBA"
        assert first.getpixel((0, 0))[3] == 0
        assert first.getpixel((50, 50))[3] == 255


def test_sheet_pipeline_supports_start_number(tmp_path) -> None:
    source = tmp_path / "sheet.png"
    output_dir = tmp_path / "out"
    _synthetic_opaque_sheet().save(source)
    cfg = FramePipelineConfig(
        target_size=(100, 100),
        margin=0,
        remove_border=True,
        remove_metadata=False,
    )

    output = process_sheet_file(source, output_dir, frame_config=cfg, start_number=31)

    assert output.frames[0].index == 31
    assert output.frames[-1].index == 40
    assert (output_dir / "31.png").is_file()
    assert (output_dir / "40.png").is_file()


def test_sheet_pipeline_report_contains_per_frame_evidence(tmp_path) -> None:
    source = tmp_path / "sheet.png"
    output_dir = tmp_path / "out"
    _synthetic_opaque_sheet().save(source)
    cfg = FramePipelineConfig(
        target_size=(100, 100),
        margin=0,
        remove_border=True,
        remove_metadata=False,
    )

    output = process_sheet_file(source, output_dir, frame_config=cfg)
    report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))

    assert report["extraction"]["frame_count"] == 10
    assert len(report["frames"]) == 10
    assert report["frames"][0]["status"] == "AUTO_FIXED"
    assert "REMOVE_OPAQUE_BACKGROUND" in report["frames"][0]["actions"]
    assert output.summary.report_file == str(output_dir / "report.json")


def test_sheet_pipeline_refuses_missing_source(tmp_path) -> None:
    try:
        process_sheet_file(tmp_path / "missing.png", tmp_path / "out")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing sheet source must fail")
