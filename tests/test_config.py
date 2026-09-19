from pathlib import Path

import pytest

from mtkrita.config import ConfigError, load_export_profile


def test_loads_shipped_line_static_profile() -> None:
    profile = load_export_profile(Path("configs/line_static.toml"))

    assert profile.id == "line_static"
    assert profile.max_width == 370
    assert profile.max_height == 320
    assert profile.allowed_counts == (8, 16, 24, 32, 40)
    assert profile.main_image == (240, 240)
    assert profile.tab_image == (96, 74)


def test_rejects_unknown_profile_key(tmp_path: Path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text(
        """
[profile]
id = "bad"
profile_version = 1
verified_date = "2026-09-19"
output_format = "png"
color_mode = "RGBA"
max_width = 370
max_height = 320
require_even_dimensions = true
transparent_background = true
min_dpi_guidance = 72
recommended_content_margin_px = 10
max_file_size_bytes = 1048576
max_zip_size_bytes = 62914560
allowed_counts = [8]
unknown_behavior = true

[profile.main_image]
width = 240
height = 240

[profile.tab_image]
width = 96
height = 74
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="unknown profile keys"):
        load_export_profile(path)
