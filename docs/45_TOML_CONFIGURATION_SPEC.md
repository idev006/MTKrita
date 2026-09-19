# MTKrita TOML Configuration Specification

## Status
SSOT — Configuration Format v1.0

## Purpose
กำหนด TOML เป็น canonical human-maintained configuration format ของ MTKrita เพื่อให้ config อ่านง่าย version-control ได้ และโหลดด้วย Python 3.11+ standard library โดยไม่ผูกกับ dependency ภายนอก

## Canonical Rule
- Human-maintained config/profile files: **TOML**
- Machine-generated runtime evidence/manifests: JSON allowed/preferred
- Python loader: `tomllib`
- Effective config must be validated before job execution
- Effective config hash must be recorded in job evidence

## File Classes
Recommended shipped files:

```text
configs/
  defaults.toml
  line_static.toml
  providers.toml        # optional deployment/provider mapping
```

Project-specific config may be supplied as another TOML file and layered over defaults/profile configuration.

## Example Export Profile

```toml
[profile]
id = "line_static"
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
allowed_counts = [8, 16, 24, 32, 40]

[profile.main_image]
width = 240
height = 240

[profile.tab_image]
width = 96
height = 74
```

## Example Provider Selection

```toml
[providers]
layout = "opencv"
border = "opencv"
metadata = "opencv"
background_classifier = "opencv"
background_removal = "opencv_floodfill"
content = "opencv"
transform = "pillow"
export = "pillow"
```

## Effective Configuration Precedence
From lowest to highest priority:
1. application defaults
2. selected profile
3. project config
4. explicit CLI/GUI overrides

Every override must be represented in the final effective config/evidence.

## Validation
Configuration loading has two distinct phases:

```text
TOML bytes
   ↓ tomllib
plain Python mapping
   ↓ MTKrita validation
Typed/Frozen EffectiveConfig
   ↓
Pipeline execution
```

The parser only proves TOML syntax. MTKrita validation must additionally check:
- required sections/keys
- supported enum/provider ids
- numeric ranges
- dimensions/counts
- incompatible options
- provider capability compatibility
- version compatibility

## Unknown Keys
Critical configuration sections should reject unknown keys by default, or emit a blocking validation finding. Silent typos are prohibited for behavior-affecting configuration.

## Secrets
MVP configuration is not intended to contain secrets. Future credentials/tokens must not be committed to project TOML files and require a separate secrets mechanism.

## Reproducibility
A job manifest must retain at least:
- source config references
- effective configuration hash
- application version
- provider ids/versions
- explicit runtime overrides

When practical, write a snapshot such as `job/config/effective.toml` into the job evidence area.

## Migration Policy
If config schema changes:
- increment relevant profile/config schema version
- document migration
- preserve backward compatibility when reasonable
- fail clearly rather than silently reinterpret old keys

References: `09_DATA_MODELS_AND_CONFIG.md`, `44_PROVIDER_INTERFACE_ARCHITECTURE.md`, ADR-016.
