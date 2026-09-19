from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when MTKrita configuration is syntactically valid TOML but invalid for MTKrita."""


@dataclass(frozen=True)
class ExportProfile:
    id: str
    profile_version: int
    verified_date: str
    output_format: str
    color_mode: str
    max_width: int
    max_height: int
    require_even_dimensions: bool
    transparent_background: bool
    min_dpi_guidance: int
    recommended_content_margin_px: int
    max_file_size_bytes: int
    max_zip_size_bytes: int
    allowed_counts: tuple[int, ...]
    main_image: tuple[int, int]
    tab_image: tuple[int, int]


def load_toml(path: str | Path) -> dict[str, Any]:
    config_path = Path(path).expanduser().resolve(strict=True)
    with config_path.open("rb") as handle:
        return tomllib.load(handle)


def _require(mapping: dict[str, Any], key: str, expected_type: type) -> Any:
    if key not in mapping:
        raise ConfigError(f"missing required key: {key}")
    value = mapping[key]
    if not isinstance(value, expected_type):
        raise ConfigError(f"invalid type for {key}: expected {expected_type.__name__}")
    return value


def _dimension(table: dict[str, Any], name: str) -> tuple[int, int]:
    nested = _require(table, name, dict)
    width = _require(nested, "width", int)
    height = _require(nested, "height", int)
    if width <= 0 or height <= 0:
        raise ConfigError(f"{name} dimensions must be positive")
    return width, height


def load_export_profile(path: str | Path) -> ExportProfile:
    data = load_toml(path)
    profile = _require(data, "profile", dict)

    known = {
        "id",
        "profile_version",
        "verified_date",
        "output_format",
        "color_mode",
        "max_width",
        "max_height",
        "require_even_dimensions",
        "transparent_background",
        "min_dpi_guidance",
        "recommended_content_margin_px",
        "max_file_size_bytes",
        "max_zip_size_bytes",
        "allowed_counts",
        "main_image",
        "tab_image",
    }
    unknown = set(profile) - known
    if unknown:
        raise ConfigError(f"unknown profile keys: {', '.join(sorted(unknown))}")

    max_width = _require(profile, "max_width", int)
    max_height = _require(profile, "max_height", int)
    if max_width <= 0 or max_height <= 0:
        raise ConfigError("profile maximum dimensions must be positive")

    allowed_counts_raw = _require(profile, "allowed_counts", list)
    if not allowed_counts_raw or not all(isinstance(v, int) and v > 0 for v in allowed_counts_raw):
        raise ConfigError("allowed_counts must be a non-empty list of positive integers")

    return ExportProfile(
        id=_require(profile, "id", str),
        profile_version=_require(profile, "profile_version", int),
        verified_date=_require(profile, "verified_date", str),
        output_format=_require(profile, "output_format", str),
        color_mode=_require(profile, "color_mode", str),
        max_width=max_width,
        max_height=max_height,
        require_even_dimensions=_require(profile, "require_even_dimensions", bool),
        transparent_background=_require(profile, "transparent_background", bool),
        min_dpi_guidance=_require(profile, "min_dpi_guidance", int),
        recommended_content_margin_px=_require(profile, "recommended_content_margin_px", int),
        max_file_size_bytes=_require(profile, "max_file_size_bytes", int),
        max_zip_size_bytes=_require(profile, "max_zip_size_bytes", int),
        allowed_counts=tuple(allowed_counts_raw),
        main_image=_dimension(profile, "main_image"),
        tab_image=_dimension(profile, "tab_image"),
    )
