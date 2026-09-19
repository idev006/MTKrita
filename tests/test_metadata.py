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
    assert detection.analysis_exclusion_applied is False
    assert detection.fragmented_by_exclusion is False

    result = remove_detected_metadata(image, detection)
    assert result.getpixel((20, 20))[3] == 0
    assert result.getpixel((120, 80))[3] == 255


def test_artwork_outside_metadata_zone_is_not_detected() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    ImageDraw.Draw(image).rectangle((80, 40, 150, 120), fill=(255, 0, 0, 255))
    assert detect_corner_metadata(image).bbox is None


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
    ImageDraw.Draw(image).rectangle((34, 18, 48, 34), fill=(200, 80, 80, 255))

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


def test_local_envelope_must_contain_anchor_envelope() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 255))
    try:
        detect_corner_metadata(
            image,
            zone=MetadataZone(anchor_x_fraction=0.8, local_x_fraction=0.7),
        )
    except ValueError as exc:
        assert "local envelope" in str(exc)
    else:
        raise AssertionError("expected invalid metadata local-envelope rejection")


def test_analysis_exclusion_outside_candidate_does_not_change_badge_selection() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 34, 34), fill=(180, 220, 120, 255))
    exclusion = Image.new("L", image.size, 0)
    ImageDraw.Draw(exclusion).rectangle((45, 0, 49, 39), fill=255)

    detection = detect_corner_metadata(image, analysis_exclusion_mask=exclusion)
    assert detection.mask is not None
    assert detection.analysis_exclusion_applied is True
    assert detection.analysis_excluded_pixel_count > 0
    assert detection.analysis_excluded_candidate_pixel_count == 0
    assert detection.requires_joint_cleanup is False
    assert detection.analysis_shape_overlap_pixel_count == 0


def test_split_badge_fragments_are_associated_only_for_joint_cleanup() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    ImageDraw.Draw(image).ellipse((8, 8, 34, 34), fill=(180, 220, 120, 255))
    exclusion = Image.new("L", image.size, 0)
    ImageDraw.Draw(exclusion).rectangle((20, 0, 21, 39), fill=255)

    detection = detect_corner_metadata(image, analysis_exclusion_mask=exclusion)
    assert detection.mask is not None
    assert detection.analysis_excluded_candidate_pixel_count > 0
    assert detection.analysis_shape_overlap_pixel_count > 0
    assert detection.confidence >= 0.72
    assert detection.fragmented_by_exclusion is True
    assert detection.fragment_association_applied is True
    assert detection.fragment_association_resolved is True
    assert detection.associated_fragment_count == 2
    assert detection.ignored_remote_fragment_count == 0
    assert detection.requires_joint_cleanup is True
    assert detection.analysis_exclusion_sha256 is not None

    try:
        remove_detected_metadata(image, detection)
    except ValueError as exc:
        assert "requires joint cleanup" in str(exc)
    else:
        raise AssertionError("expected joint-only metadata removal refusal")


def test_remote_artwork_connected_only_through_excluded_band_is_preserved() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    color = (180, 220, 120, 255)
    draw.ellipse((8, 8, 34, 34), fill=color)
    draw.line((34, 20, 46, 20), fill=color, width=3)
    draw.rectangle((44, 14, 49, 26), fill=color)
    exclusion = Image.new("L", image.size, 0)
    ImageDraw.Draw(exclusion).rectangle((20, 0, 21, 39), fill=255)
    ImageDraw.Draw(exclusion).rectangle((35, 0, 42, 39), fill=255)

    detection = detect_corner_metadata(image, analysis_exclusion_mask=exclusion)

    assert detection.mask is not None
    assert detection.requires_joint_cleanup is True
    assert detection.fragment_association_resolved is True
    assert detection.ignored_remote_fragment_count >= 1
    assert detection.mask.getpixel((47, 20)) == 0
    assert "remote fragments preserved" in detection.reason


def test_selected_component_with_nonexcluded_path_beyond_local_envelope_routes_review() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    color = (180, 220, 120, 255)
    draw.ellipse((8, 8, 34, 34), fill=color)
    draw.line((12, 24, 12, 39), fill=color, width=3)
    exclusion = Image.new("L", image.size, 0)
    ImageDraw.Draw(exclusion).rectangle((20, 0, 21, 39), fill=255)

    detection = detect_corner_metadata(image, analysis_exclusion_mask=exclusion)

    assert detection.mask is None
    assert detection.fragment_association_applied is True
    assert detection.fragment_association_resolved is False
    assert "unresolved" in detection.reason


def test_analysis_exclusion_size_mismatch_is_rejected() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    exclusion = Image.new("L", (40, 40), 0)
    try:
        detect_corner_metadata(image, analysis_exclusion_mask=exclusion)
    except ValueError as exc:
        assert "size does not match" in str(exc)
    else:
        raise AssertionError("expected exclusion-mask size validation failure")


def test_enclosed_visible_dark_detail_is_included_in_metadata_mask() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 34, 34), fill=(180, 220, 120, 255))
    draw.rectangle((19, 14, 21, 28), fill=(0, 0, 0, 255))

    detection = detect_corner_metadata(image)
    assert detection.mask is not None
    assert detection.enclosed_visible_hole_pixel_count > 0
    assert detection.mask.getpixel((20, 20)) == 255

    cleaned = remove_detected_metadata(image, detection)
    assert cleaned.getpixel((20, 20))[3] == 0


def test_open_dark_notch_is_not_filled_as_metadata_interior() -> None:
    image = Image.new("RGBA", (200, 160), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 34, 34), fill=(180, 220, 120, 255))
    draw.line((20, 20, 20, 7), fill=(0, 0, 0, 255), width=3)

    detection = detect_corner_metadata(image)
    assert detection.mask is not None
    assert detection.mask.getpixel((20, 20)) == 0
