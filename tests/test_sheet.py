from PIL import Image

from mtkrita.sheet import ExtractionMethod, GridSpec, split_grid, split_grid_scaled


def test_split_grid_5x2_with_margin_and_gaps() -> None:
    spec = GridSpec(rows=2, columns=5, margin_x=10, margin_y=8, gap_x=4, gap_y=6)
    width = (2 * spec.margin_x) + (5 * 20) + (4 * spec.gap_x)
    height = (2 * spec.margin_y) + (2 * 30) + spec.gap_y
    sheet = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    frames = split_grid(sheet, spec)
    assert len(frames) == 10
    assert frames[0].index == 1
    assert frames[-1].index == 10
    assert frames[0].image.size == (20, 30)
    assert frames[0].box == (10, 8, 30, 38)


def test_split_grid_rejects_ambiguous_geometry() -> None:
    sheet = Image.new("RGBA", (103, 41), (0, 0, 0, 0))
    try:
        split_grid(sheet, GridSpec(rows=2, columns=5))
    except ValueError as exc:
        assert "hybrid refinement required" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_scaled_grid_handles_uniformly_resized_non_divisible_sheet() -> None:
    sheet = Image.new("RGBA", (103, 41), (0, 0, 0, 0))
    result = split_grid_scaled(sheet, GridSpec(rows=2, columns=5))

    assert result.method == ExtractionMethod.CONFIGURED_SCALED
    assert result.confidence >= 0.95
    assert len(result.frames) == 10
    assert result.frames[0].index == 1
    assert result.frames[-1].index == 10
    assert result.max_width_variation_px <= 1
    assert result.max_height_variation_px <= 1

    first_row = result.frames[:5]
    assert first_row[0].box[0] == 0
    assert first_row[-1].box[2] == 103
    assert sum(frame.image.width for frame in first_row) == 103


def test_scaled_grid_returns_exact_method_when_divisible() -> None:
    sheet = Image.new("RGBA", (100, 40), (0, 0, 0, 0))
    result = split_grid_scaled(sheet, GridSpec(rows=2, columns=5))
    assert result.method == ExtractionMethod.CONFIGURED_EXACT
    assert result.confidence == 1.0
    assert all(frame.image.size == (20, 20) for frame in result.frames)
