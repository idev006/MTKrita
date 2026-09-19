from PIL import Image, ImageDraw

from mtkrita.metadata import MetadataZone, detect_corner_metadata, remove_detected_metadata


def test_detects_and_removes_top_left_badge_without_touching_artwork_elsewhere() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 34, 34), fill=(180, 220, 120, 255))
    draw.rectangle((90, 50, 150, 120), fill=(230, 120, 40, 255))

    detection = detect_corner_metadata(image)
    assert detection.bbox is not None
    assert detection.confidence >= 0.72
    assert detection.anchored_candidate_count == 1
    assert detection.anchor_distance is not None
    assert detection.dominance_margin == 1.0

    result = remove_detected_metadata(image, detection)
    assert result.getpixel((20, 20))[3] == 0
    assert result.getpixel((120, 80))[3] == 255


def test_artwork_outside_metadata_zone_is_not_detected() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 40, 150, 120), fill=(255, 0, 0, 255))

    detection = detect_corner_metadata(image)
    assert detection.bbox is None


def test_nonanchored_component_inside_zone_does_not_compete_with_badge() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((6, 6, 24, 24), fill=(180, 220, 120, 255))
    draw.rectangle((36, 22, 48, 36), fill=(180, 220, 120, 255))

    detection = detect_corner_metadata(image)

    assert detection.bbox is not None
    assert detection.candidate_count == 2
    assert detection.anchored_candidate_count == 1
    assert detection.dominance_margin == 1.0


def test_ambiguous_multiple_anchored_components_are_not_auto_selected() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 5, 16, 17), fill=(180, 220, 120, 255))
    draw.ellipse((18, 5, 30, 17), fill=(180, 220, 120, 255))

    detection = detect_corner_metadata(image)
    assert detection.mask is None
    assert detection.anchored_candidate_count == 2
    assert detection.dominance_margin is not None
    assert "ambiguous" in detection.reason


def test_artwork_only_inside_broad_zone_but_outside_anchor_is_not_deleted() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((34, 18, 48, 34), fill=(200, 80, 80, 255))

    detection = detect_corner_metadata(image)

    assert detection.mask is None
    assert detection.bbox is None
    assert detection.candidate_count == 1
    assert detection.anchored_candidate_count == 0
    assert "anchored" in detection.reason


def test_badge_absent_frame_has_no_removal_plan() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))

    detection = detect_corner_metadata(image)

    assert detection.bbox is None
    assert detection.mask is None
    assert detection.candidate_count == 0


def test_custom_anchor_envelope_is_validated_and_applied() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    ImageDraw.Draw(image).ellipse((20, 8, 36, 24), fill=(180, 220, 120, 255))

    strict = detect_corner_metadata(
        image,
        zone=MetadataZone(anchor_x_fraction=0.35, anchor_y_fraction=0.60),
    )
    relaxed = detect_corner_metadata(image)

    assert strict.mask is None
    assert relaxed.mask is not None
