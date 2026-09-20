from PIL import Image

from mtkrita.border import BorderDetection, BorderSide
from mtkrita.contact_topology import resolve_reciprocal_corner_contact


def _side(
    name: str,
    ranges: tuple[tuple[int, int], ...],
    *,
    side_length: int,
    offset: int = 6,
    thickness: int = 3,
) -> BorderSide:
    trim = offset + thickness
    sample_count = side_length - (2 * trim)
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


def _detection(
    *,
    left: BorderSide | None = None,
    top: BorderSide | None = None,
    right: BorderSide | None = None,
    bottom: BorderSide | None = None,
) -> BorderDetection:
    return BorderDetection(
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        consensus_mode="single_tone",
    )


def test_reciprocal_corner_contact_is_explained_but_raw_evidence_is_preserved() -> None:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    detection = _detection(
        top=_side("top", ((2, 8),), side_length=100),
        left=_side("left", ((3, 9),), side_length=80),
    )

    result = resolve_reciprocal_corner_contact(image, detection)

    assert result.sides["top"].raw_contact_ranges == ((2, 8),)
    assert result.sides["top"].explained_corner_ranges == ((2, 8),)
    assert result.sides["left"].explained_corner_ranges == ((3, 9),)
    assert result.detection.top is not None
    assert result.detection.left is not None
    assert result.detection.top.contact_ranges == ()
    assert result.detection.left.contact_ranges == ()
    assert result.detection.top.contact_fraction == 0.0
    assert result.detection.left.contact_fraction == 0.0
    assert result.detection.contact_risk is False


def test_reciprocal_corner_plus_central_artwork_keeps_central_contact_residual() -> None:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    detection = _detection(
        top=_side("top", ((2, 8), (40, 50)), side_length=100),
        left=_side("left", ((3, 9),), side_length=80),
    )

    result = resolve_reciprocal_corner_contact(image, detection)

    assert result.detection.top is not None
    assert result.sides["top"].explained_corner_ranges == ((2, 8),)
    assert result.detection.top.contact_ranges == ((40, 50),)
    assert result.detection.top.contact_risk is True
    assert result.detection.contact_risk is True


def test_one_sided_endpoint_contact_remains_unexplained() -> None:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    detection = _detection(
        top=_side("top", ((2, 8),), side_length=100),
        left=_side("left", ((20, 26),), side_length=80),
    )

    result = resolve_reciprocal_corner_contact(image, detection)

    assert result.detection.top is not None
    assert result.sides["top"].explained_corner_ranges == ()
    assert result.detection.top.contact_ranges == ((2, 8),)
    assert result.detection.top.contact_risk is True


def test_interval_crossing_corner_envelope_is_not_partially_explained() -> None:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    detection = _detection(
        top=_side("top", ((8, 15),), side_length=100),
        left=_side("left", ((3, 9),), side_length=80),
    )

    result = resolve_reciprocal_corner_contact(image, detection)

    assert result.detection.top is not None
    assert result.detection.left is not None
    assert result.sides["top"].explained_corner_ranges == ()
    assert result.sides["left"].explained_corner_ranges == ()
    assert result.detection.top.contact_ranges == ((8, 15),)
    assert result.detection.left.contact_ranges == ((3, 9),)


def test_single_long_parallel_contact_remains_unexplained() -> None:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    detection = _detection(
        top=_side("top", ((0, 40),), side_length=100),
        left=_side("left", ((3, 9),), side_length=80),
    )

    result = resolve_reciprocal_corner_contact(image, detection)

    assert result.detection.top is not None
    assert result.sides["top"].explained_corner_ranges == ()
    assert result.detection.top.contact_ranges == ((0, 40),)
    assert result.detection.top.contact_risk is True


def test_edge_consensus_is_unchanged_by_phase_one_topology() -> None:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    top = _side("top", ((2, 8),), side_length=100, offset=0, thickness=3)
    left = _side("left", ((3, 9),), side_length=80, offset=0, thickness=3)
    detection = BorderDetection(
        left=left,
        top=top,
        right=None,
        bottom=None,
        consensus_mode="edge",
    )

    result = resolve_reciprocal_corner_contact(image, detection)

    assert result.detection == detection
    assert result.sides["top"].explained_corner_ranges == ()
    assert result.sides["left"].explained_corner_ranges == ()


def test_topology_resolution_is_deterministic() -> None:
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    detection = _detection(
        top=_side("top", ((2, 8), (40, 50)), side_length=100),
        left=_side("left", ((3, 9),), side_length=80),
    )

    first = resolve_reciprocal_corner_contact(image, detection)
    second = resolve_reciprocal_corner_contact(image, detection)

    assert first == second
