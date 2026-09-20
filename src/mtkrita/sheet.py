from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from PIL import Image


class ExtractionMethod(StrEnum):
    CONFIGURED_EXACT = "configured_exact"
    CONFIGURED_SCALED = "configured_scaled"
    CONFIGURED_REFINED = "configured_refined"


@dataclass(frozen=True)
class GridSpec:
    rows: int = 2
    columns: int = 5
    margin_x: int = 0
    margin_y: int = 0
    gap_x: int = 0
    gap_y: int = 0


@dataclass(frozen=True)
class ExtractedFrame:
    index: int
    row: int
    column: int
    box: tuple[int, int, int, int]
    image: Image.Image


@dataclass(frozen=True)
class GridSplitResult:
    frames: tuple[ExtractedFrame, ...]
    method: ExtractionMethod
    confidence: float
    max_width_variation_px: int
    max_height_variation_px: int
    predicted_x_edges: tuple[int, ...] = ()
    refined_x_edges: tuple[int, ...] = ()
    predicted_y_edges: tuple[int, ...] = ()
    refined_y_edges: tuple[int, ...] = ()
    x_separator_offsets: tuple[int, ...] = ()
    y_separator_offsets: tuple[int, ...] = ()
    separator_min_support: float | None = None


def _validate_geometry(image: Image.Image, spec: GridSpec) -> tuple[int, int]:
    if spec.rows <= 0 or spec.columns <= 0:
        raise ValueError("rows and columns must be positive")
    if min(spec.margin_x, spec.margin_y, spec.gap_x, spec.gap_y) < 0:
        raise ValueError("grid margins/gaps must be non-negative")

    usable_width = image.width - (2 * spec.margin_x) - ((spec.columns - 1) * spec.gap_x)
    usable_height = image.height - (2 * spec.margin_y) - ((spec.rows - 1) * spec.gap_y)
    if usable_width <= 0 or usable_height <= 0:
        raise ValueError("grid margins/gaps exceed image size")
    return usable_width, usable_height


def _proportional_edges(
    usable: int,
    count: int,
    margin: int,
    gap: int,
) -> list[int]:
    return [
        margin + round((usable * index) / count) + (index * gap)
        for index in range(count + 1)
    ]


def _build_frames(
    image: Image.Image,
    spec: GridSpec,
    x_edges: list[int],
    y_edges: list[int],
) -> tuple[ExtractedFrame, ...]:
    frames: list[ExtractedFrame] = []
    for row in range(spec.rows):
        for column in range(spec.columns):
            left = x_edges[column]
            right = x_edges[column + 1] - (spec.gap_x if column < spec.columns - 1 else 0)
            top = y_edges[row]
            bottom = y_edges[row + 1] - (spec.gap_y if row < spec.rows - 1 else 0)
            if right <= left or bottom <= top:
                raise ValueError("grid produced invalid frame geometry")
            box = (left, top, right, bottom)
            frames.append(
                ExtractedFrame(
                    index=(row * spec.columns) + column + 1,
                    row=row,
                    column=column,
                    box=box,
                    image=image.crop(box),
                )
            )
    return tuple(frames)


def _cell_variation(edges: list[int], gap: int) -> int:
    sizes = [
        edges[index + 1]
        - edges[index]
        - (gap if index < len(edges) - 2 else 0)
        for index in range(len(edges) - 1)
    ]
    return max(sizes) - min(sizes)


def split_grid(image: Image.Image, spec: GridSpec | None = None) -> list[ExtractedFrame]:
    """Split exact configured geometry without resampling."""
    resolved_spec = spec or GridSpec()
    usable_width, usable_height = _validate_geometry(image, resolved_spec)
    if usable_width % resolved_spec.columns or usable_height % resolved_spec.rows:
        raise ValueError("sheet geometry does not divide evenly; hybrid refinement required")

    frame_width = usable_width // resolved_spec.columns
    frame_height = usable_height // resolved_spec.rows
    x_edges = [
        resolved_spec.margin_x
        + column * (frame_width + resolved_spec.gap_x)
        for column in range(resolved_spec.columns)
    ]
    x_edges.append(image.width - resolved_spec.margin_x)
    y_edges = [
        resolved_spec.margin_y + row * (frame_height + resolved_spec.gap_y)
        for row in range(resolved_spec.rows)
    ]
    y_edges.append(image.height - resolved_spec.margin_y)
    return list(_build_frames(image, resolved_spec, x_edges, y_edges))


def split_grid_scaled(
    image: Image.Image,
    spec: GridSpec | None = None,
    *,
    max_cell_variation_px: int = 1,
) -> GridSplitResult:
    """Split uniformly resized configured geometry using proportional boundaries."""
    resolved_spec = spec or GridSpec()
    if max_cell_variation_px < 0:
        raise ValueError("max_cell_variation_px must be non-negative")
    usable_width, usable_height = _validate_geometry(image, resolved_spec)

    if usable_width % resolved_spec.columns == 0 and usable_height % resolved_spec.rows == 0:
        frames = tuple(split_grid(image, resolved_spec))
        return GridSplitResult(
            frames=frames,
            method=ExtractionMethod.CONFIGURED_EXACT,
            confidence=1.0,
            max_width_variation_px=0,
            max_height_variation_px=0,
        )

    x_edges = _proportional_edges(
        usable_width,
        resolved_spec.columns,
        resolved_spec.margin_x,
        resolved_spec.gap_x,
    )
    y_edges = _proportional_edges(
        usable_height,
        resolved_spec.rows,
        resolved_spec.margin_y,
        resolved_spec.gap_y,
    )
    width_variation = _cell_variation(x_edges, resolved_spec.gap_x)
    height_variation = _cell_variation(y_edges, resolved_spec.gap_y)
    if width_variation > max_cell_variation_px or height_variation > max_cell_variation_px:
        raise ValueError("scaled grid variation exceeds configured safety limit")

    frames = _build_frames(image, resolved_spec, x_edges, y_edges)
    confidence = 0.97 if max(width_variation, height_variation) <= 1 else 0.90
    return GridSplitResult(
        frames=frames,
        method=ExtractionMethod.CONFIGURED_SCALED,
        confidence=confidence,
        max_width_variation_px=width_variation,
        max_height_variation_px=height_variation,
        predicted_x_edges=tuple(x_edges),
        refined_x_edges=tuple(x_edges),
        predicted_y_edges=tuple(y_edges),
        refined_y_edges=tuple(y_edges),
        x_separator_offsets=tuple(0 for _ in x_edges[1:-1]),
        y_separator_offsets=tuple(0 for _ in y_edges[1:-1]),
    )


def _qualifying_runs(
    scores: np.ndarray,
    *,
    lower: int,
    upper: int,
    min_support: float,
    min_run_px: int,
) -> list[tuple[int, int, float]]:
    indexes = [
        index
        for index in range(lower, upper + 1)
        if float(scores[index]) >= min_support
    ]
    if not indexes:
        return []

    runs: list[tuple[int, int, float]] = []
    start = previous = indexes[0]
    for index in indexes[1:]:
        if index == previous + 1:
            previous = index
            continue
        if previous - start + 1 >= min_run_px:
            support = float(np.mean(scores[start : previous + 1]))
            runs.append((start, previous, support))
        start = previous = index
    if previous - start + 1 >= min_run_px:
        support = float(np.mean(scores[start : previous + 1]))
        runs.append((start, previous, support))
    return runs


def _refine_axis_edges(
    predicted_edges: list[int],
    scores: np.ndarray,
    *,
    search_window_px: int,
    min_support: float,
    min_run_px: int,
    min_dominance_px: int,
) -> tuple[list[int], list[int], list[float]]:
    refined = [predicted_edges[0]]
    offsets: list[int] = []
    supports: list[float] = []
    axis_length = len(scores)

    for predicted in predicted_edges[1:-1]:
        lower = max(1, predicted - search_window_px)
        upper = min(axis_length - 2, predicted + search_window_px)
        runs = _qualifying_runs(
            scores,
            lower=lower,
            upper=upper,
            min_support=min_support,
            min_run_px=min_run_px,
        )
        if not runs:
            raise ValueError("visual separator evidence is absent within refinement window")

        ranked: list[tuple[int, float, int, int, int]] = []
        for start, end, support in runs:
            if start <= predicted <= end:
                distance = 0
                chosen = predicted
            elif end < predicted:
                distance = predicted - end
                chosen = end
            else:
                distance = start - predicted
                chosen = start
            ranked.append((distance, -support, chosen, start, end))
        ranked.sort()

        if (
            len(ranked) > 1
            and ranked[0][0] != 0
            and ranked[1][0] - ranked[0][0] < min_dominance_px
        ):
            raise ValueError("visual separator evidence is ambiguous within refinement window")

        _, _, chosen, start, end = ranked[0]
        support = float(np.mean(scores[start : end + 1]))
        refined.append(chosen)
        offsets.append(chosen - predicted)
        supports.append(support)

    refined.append(predicted_edges[-1])
    if any(refined[index] >= refined[index + 1] for index in range(len(refined) - 1)):
        raise ValueError("refined separators are not strictly increasing")
    return refined, offsets, supports


def split_grid_refined(
    image: Image.Image,
    spec: GridSpec | None = None,
    *,
    max_cell_variation_px: int = 1,
    search_window_px: int = 16,
    min_transparent_fraction: float = 0.98,
    min_run_px: int = 2,
    min_dominance_px: int = 2,
    transparent_alpha_threshold: int = 8,
) -> GridSplitResult:
    """Refine configured proportional separators using bounded transparent gutters.

    This Tier-B refinement never resamples source pixels. It searches only near the
    configured prediction and fails closed when separator evidence is absent or
    ambiguous.
    """
    resolved_spec = spec or GridSpec()
    if resolved_spec.gap_x or resolved_spec.gap_y:
        raise ValueError("visual separator refinement currently requires zero configured gaps")
    if max_cell_variation_px < 0:
        raise ValueError("max_cell_variation_px must be non-negative")
    if search_window_px < 0:
        raise ValueError("search_window_px must be non-negative")
    if not 0 < min_transparent_fraction <= 1:
        raise ValueError("min_transparent_fraction must be in (0, 1]")
    if min_run_px <= 0:
        raise ValueError("min_run_px must be positive")
    if min_dominance_px < 0:
        raise ValueError("min_dominance_px must be non-negative")
    if not 0 <= transparent_alpha_threshold <= 254:
        raise ValueError("transparent_alpha_threshold must be between 0 and 254")

    usable_width, usable_height = _validate_geometry(image, resolved_spec)
    predicted_x = _proportional_edges(
        usable_width,
        resolved_spec.columns,
        resolved_spec.margin_x,
        resolved_spec.gap_x,
    )
    predicted_y = _proportional_edges(
        usable_height,
        resolved_spec.rows,
        resolved_spec.margin_y,
        resolved_spec.gap_y,
    )
    predicted_width_variation = _cell_variation(predicted_x, 0)
    predicted_height_variation = _cell_variation(predicted_y, 0)
    if (
        predicted_width_variation > max_cell_variation_px
        or predicted_height_variation > max_cell_variation_px
    ):
        raise ValueError("scaled grid variation exceeds configured safety limit")

    alpha = np.asarray(image.convert("RGBA").getchannel("A"), dtype=np.uint8)
    x_scores = np.mean(alpha <= transparent_alpha_threshold, axis=0)
    y_scores = np.mean(alpha <= transparent_alpha_threshold, axis=1)

    refined_x, x_offsets, x_supports = _refine_axis_edges(
        predicted_x,
        x_scores,
        search_window_px=search_window_px,
        min_support=min_transparent_fraction,
        min_run_px=min_run_px,
        min_dominance_px=min_dominance_px,
    )
    refined_y, y_offsets, y_supports = _refine_axis_edges(
        predicted_y,
        y_scores,
        search_window_px=search_window_px,
        min_support=min_transparent_fraction,
        min_run_px=min_run_px,
        min_dominance_px=min_dominance_px,
    )

    frames = _build_frames(image, resolved_spec, refined_x, refined_y)
    width_variation = _cell_variation(refined_x, 0)
    height_variation = _cell_variation(refined_y, 0)
    supports = x_supports + y_supports
    min_support = min(supports) if supports else 1.0
    confidence = min(0.995, min_support)

    return GridSplitResult(
        frames=frames,
        method=ExtractionMethod.CONFIGURED_REFINED,
        confidence=confidence,
        max_width_variation_px=width_variation,
        max_height_variation_px=height_variation,
        predicted_x_edges=tuple(predicted_x),
        refined_x_edges=tuple(refined_x),
        predicted_y_edges=tuple(predicted_y),
        refined_y_edges=tuple(refined_y),
        x_separator_offsets=tuple(x_offsets),
        y_separator_offsets=tuple(y_offsets),
        separator_min_support=min_support,
    )
