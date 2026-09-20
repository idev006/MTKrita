import numpy as np
from PIL import Image

from mtkrita.sheet import ExtractionMethod, GridSpec, split_grid_refined


def _sheet_with_gutters(
    *,
    width: int = 103,
    height: int = 41,
    x_gutters: tuple[tuple[int, int], ...] = ((20, 21), (40, 41), (59, 60), (81, 82)),
    y_gutters: tuple[tuple[int, int], ...] = ((19, 20),),
) -> Image.Image:
    array = np.zeros((height, width, 4), dtype=np.uint8)
    array[:, :, :] = (20, 40, 60, 255)
    for start, end in x_gutters:
        array[:, start : end + 1, 3] = 0
    for start, end in y_gutters:
        array[start : end + 1, :, 3] = 0

    # Coordinate-derived RGB lets us prove crops preserve exact source pixels.
    ys, xs = np.indices((height, width))
    array[:, :, 0] = xs % 251
    array[:, :, 1] = ys % 251
    array[:, :, 2] = (xs + ys) % 251
    return Image.fromarray(array)


def test_refined_grid_moves_shifted_separator_and_removes_neighbor_contamination() -> None:
    sheet = _sheet_with_gutters()

    result = split_grid_refined(sheet, GridSpec(rows=2, columns=5))

    assert result.method == ExtractionMethod.CONFIGURED_REFINED
    assert result.predicted_x_edges == (0, 21, 41, 62, 82, 103)
    assert result.refined_x_edges == (0, 21, 41, 60, 82, 103)
    assert result.x_separator_offsets == (0, 0, -2, 0)
    assert result.predicted_y_edges == (0, 20, 41)
    assert result.refined_y_edges == (0, 20, 41)
    assert result.y_separator_offsets == (0,)

    third = result.frames[2]
    assert third.box == (41, 0, 60, 20)
    assert third.box[2] == 60


def test_refinement_keeps_prediction_when_prediction_is_inside_gutter() -> None:
    sheet = _sheet_with_gutters(
        x_gutters=((20, 22), (40, 42), (61, 63), (81, 83)),
        y_gutters=((19, 21),),
    )

    result = split_grid_refined(sheet, GridSpec(rows=2, columns=5))

    assert result.refined_x_edges == result.predicted_x_edges
    assert result.refined_y_edges == result.predicted_y_edges
    assert result.x_separator_offsets == (0, 0, 0, 0)
    assert result.y_separator_offsets == (0,)


def test_refinement_rejects_ambiguous_equal_distance_gutters() -> None:
    sheet = _sheet_with_gutters(
        x_gutters=((17, 18), (24, 25), (40, 41), (61, 62), (81, 82)),
    )

    try:
        split_grid_refined(sheet, GridSpec(rows=2, columns=5), min_dominance_px=2)
    except ValueError as exc:
        assert "ambiguous" in str(exc)
    else:
        raise AssertionError("expected ambiguous separator evidence to be rejected")


def test_refinement_rejects_sheet_without_transparent_separator_evidence() -> None:
    sheet = Image.new("RGBA", (103, 41), (30, 30, 30, 255))

    try:
        split_grid_refined(sheet, GridSpec(rows=2, columns=5))
    except ValueError as exc:
        assert "separator evidence is absent" in str(exc)
    else:
        raise AssertionError("expected absent separator evidence to be rejected")


def test_refinement_is_deterministic_and_uses_source_pixels_without_resampling() -> None:
    sheet = _sheet_with_gutters()

    first = split_grid_refined(sheet, GridSpec(rows=2, columns=5))
    second = split_grid_refined(sheet, GridSpec(rows=2, columns=5))

    assert tuple(frame.box for frame in first.frames) == tuple(frame.box for frame in second.frames)
    assert first.refined_x_edges == second.refined_x_edges
    assert first.refined_y_edges == second.refined_y_edges
    assert first.x_separator_offsets == second.x_separator_offsets
    assert first.y_separator_offsets == second.y_separator_offsets

    source = np.asarray(sheet)
    for frame in first.frames:
        left, top, right, bottom = frame.box
        expected = source[top:bottom, left:right, :]
        actual = np.asarray(frame.image)
        assert np.array_equal(actual, expected)
