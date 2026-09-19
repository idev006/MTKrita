import copy

import pytest

from mtkrita.m2_task_descriptor import M2TaskDescriptorError, parse_m2_frame_descriptor


def _descriptor() -> dict[str, object]:
    return {
        "task_type": "m2.frame",
        "input_name": "frame-001.png",
        "input_sha256": "a" * 64,
        "output_name": "01.png",
        "frame_index": 1,
        "row": 0,
        "column": 0,
        "extraction_rect": [0, 0, 512, 512],
        "extraction_method": "exact-grid",
        "extraction_confidence": 1.0,
        "pipeline_config": {
            "target_width": 370,
            "target_height": 320,
            "margin": 10,
            "remove_border": True,
            "remove_metadata": True,
            "border_auto_threshold": 0.995,
            "metadata_auto_threshold": 0.72,
        },
    }


def test_m2_descriptor_parses_exact_production_schema() -> None:
    parsed = parse_m2_frame_descriptor(_descriptor())

    assert parsed.task_type == "m2.frame"
    assert parsed.input_name == "frame-001.png"
    assert parsed.output_name == "01.png"
    assert parsed.extraction_rect == (0, 0, 512, 512)
    assert parsed.pipeline_config.target_width == 370
    assert parsed.pipeline_config.remove_metadata is True


def test_m2_descriptor_rejects_unknown_or_path_like_fields() -> None:
    descriptor = _descriptor()
    descriptor["source_path"] = "C:/outside/frame.png"
    with pytest.raises(M2TaskDescriptorError, match="fields"):
        parse_m2_frame_descriptor(descriptor)

    descriptor = _descriptor()
    descriptor["input_name"] = "../frame.png"
    with pytest.raises(M2TaskDescriptorError, match="path component"):
        parse_m2_frame_descriptor(descriptor)

    descriptor = _descriptor()
    descriptor["output_name"] = "C:/outside/01.png"
    with pytest.raises(M2TaskDescriptorError, match="path component"):
        parse_m2_frame_descriptor(descriptor)


def test_m2_descriptor_rejects_invalid_hash_geometry_and_output_extension() -> None:
    descriptor = _descriptor()
    descriptor["input_sha256"] = "not-a-hash"
    with pytest.raises(M2TaskDescriptorError, match="SHA-256"):
        parse_m2_frame_descriptor(descriptor)

    descriptor = _descriptor()
    descriptor["extraction_rect"] = [10, 10, 5, 20]
    with pytest.raises(M2TaskDescriptorError, match="geometry"):
        parse_m2_frame_descriptor(descriptor)

    descriptor = _descriptor()
    descriptor["output_name"] = "01.jpg"
    with pytest.raises(M2TaskDescriptorError, match=".png"):
        parse_m2_frame_descriptor(descriptor)


def test_m2_descriptor_rejects_bool_as_integer_and_out_of_range_ratios() -> None:
    descriptor = _descriptor()
    descriptor["frame_index"] = True
    with pytest.raises(M2TaskDescriptorError, match="integer"):
        parse_m2_frame_descriptor(descriptor)

    descriptor = _descriptor()
    descriptor["extraction_confidence"] = 1.1
    with pytest.raises(M2TaskDescriptorError, match="between 0 and 1"):
        parse_m2_frame_descriptor(descriptor)

    descriptor = _descriptor()
    config = copy.deepcopy(descriptor["pipeline_config"])
    assert isinstance(config, dict)
    config["border_auto_threshold"] = -0.1
    descriptor["pipeline_config"] = config
    with pytest.raises(M2TaskDescriptorError, match="between 0 and 1"):
        parse_m2_frame_descriptor(descriptor)


def test_m2_descriptor_rejects_unknown_pipeline_config_and_bad_margin() -> None:
    descriptor = _descriptor()
    config = copy.deepcopy(descriptor["pipeline_config"])
    assert isinstance(config, dict)
    config["mystery"] = 1
    descriptor["pipeline_config"] = config
    with pytest.raises(M2TaskDescriptorError, match="pipeline_config fields"):
        parse_m2_frame_descriptor(descriptor)

    descriptor = _descriptor()
    config = copy.deepcopy(descriptor["pipeline_config"])
    assert isinstance(config, dict)
    config["margin"] = 200
    descriptor["pipeline_config"] = config
    with pytest.raises(M2TaskDescriptorError, match="no usable output canvas"):
        parse_m2_frame_descriptor(descriptor)
