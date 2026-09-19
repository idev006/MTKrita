# Data Models and Configuration

## Status
SSOT — Configuration Model v1.2

## Canonical Format
MTKrita uses **TOML** for human-maintained configuration and shipped profiles.

Python 3.11+ should read TOML with the standard-library `tomllib`. Configuration data must be validated into typed runtime models before processing begins.

JSON remains appropriate for machine-generated manifests and evidence artifacts.

## Project Config Example

```toml
[project]
name = "sample_set"
version = 1

[input]
mode = "auto"

[sheet]
rows = 2
columns = 5
margin_x = 20
margin_y = 20
gap_x = 0
gap_y = 0

[sheet.nominal_frame]
width = 512
height = 512

[processing]
alpha_threshold = 8
noise_component_area = 8
auto_recenter = true
auto_scale_down = true
auto_scale_up = false

[processing.metadata]
zone = "top_left"
x_fraction = 0.25
y_fraction = 0.25
confidence_threshold = 0.72

[processing.border]
max_fraction = 0.12
color_tolerance = 8
min_coverage = 0.985
auto_threshold = 0.995

[qa]
safe_edge_px = 12
review_on_edge_contact = true

[export]
profile = "line_static"
filename_pattern = "{index:02d}.png"
```

## Configuration Layers
Recommended precedence, lowest to highest:

1. shipped defaults
2. export/profile TOML
3. project TOML
4. explicit CLI/GUI overrides

Overrides must be recorded in job evidence so the effective configuration can be reproduced.

## Validation Rules
- unknown critical keys should fail validation or be explicitly surfaced
- enum-like values are validated against accepted values
- dimensions/counts/thresholds must satisfy declared ranges
- configuration is frozen per job after validation
- effective config receives a stable SHA-256 hash
- provider selection is explicit and traceable

## Provider Selection Example

```toml
[providers]
layout = "opencv"
border = "opencv"
metadata = "opencv"
background = "opencv_floodfill"
transform = "pillow"
export = "pillow"
```

The orchestrator depends on provider interfaces. These names select registered concrete implementations; domain workflow must not branch on third-party library details.

## Job Model

```json
{
  "job_id": "uuid",
  "created_at": "ISO-8601",
  "input_file": "sheet01.png",
  "input_hash": "sha256",
  "engine_version": "0.1.0",
  "config_hash": "sha256",
  "effective_config": "job/config/effective.toml",
  "frames": []
}
```

## Frame Result

```json
{
  "index": 1,
  "row": 0,
  "column": 0,
  "extraction_rect": [20, 20, 512, 512],
  "extraction_method": "configured_scaled",
  "extraction_confidence": 0.97,
  "processing_mode": "transparent",
  "content_bbox": [54, 18, 421, 470],
  "status": "AUTO_FIXED",
  "findings": [],
  "actions": ["SMART_FIT"],
  "providers": {},
  "evidence": {
    "background_route": "skip_remove_background",
    "route_provenance": "pre_metadata_frame",
    "meaningful_transparency": true,
    "transparent_pixel_ratio": 0.41,
    "fit_scale": 0.88
  },
  "output_file": "01.png",
  "output_sha256": "sha256"
}
```

## Mandatory Evidence Rules
Each processed frame must retain enough machine-readable evidence to reconstruct critical decisions without reading UI text or logs.

At minimum where applicable:
- extraction rectangle / method / confidence
- source transparency/background route
- route provenance (`pre_metadata_frame` for ADR-023)
- alpha statistics used for routing
- border/metadata detection confidence and reason
- significant actions / QA findings
- fit scale / offset
- provider identifiers when provider boundaries are active
- final output path reference + SHA-256 once exported

Cleanup-generated alpha must never overwrite or reinterpret the stored source routing evidence.

## Reproducibility Metadata
Always retain source hash, effective config hash, engine version, provider/strategy identifiers, dependency versions and processing decisions.

References: `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `34_DATA_FLOW_AND_ARTIFACT_LIFECYCLE.md`, `44_PROVIDER_INTERFACE_ARCHITECTURE.md`, `45_TOML_CONFIGURATION_SPEC.md`, ADR-015, ADR-016 and ADR-023.
