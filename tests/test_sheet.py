from PIL import Image

from mtkrita.sheet import GridSpec, split_grid


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
    sheet = Image.new("RGBA", (103, 40), (0, 0, 0, 0))
    try:
        split_grid(sheet, GridSpec(rows=2, columns=5))
    except ValueError as exc:
        assert "hybrid refinement required" in str(exc)
    else:
        raise AssertionError("expected ValueError")
