# Data Models and Configuration

## Project Config Example

```yaml
project:
  name: sample_set
  version: 1

input:
  mode: auto

sheet:
  rows: 2
  columns: 5
  nominal_frame:
    width: 512
    height: 512
  margin: 20
  padding: 20

processing:
  alpha_threshold: 8
  noise_component_area: 8
  auto_recenter: true
  auto_scale_down: true
  auto_scale_up: false

qa:
  safe_edge_px: 12
  review_on_edge_contact: true

export:
  profile: line_static
  filename_pattern: "{index:02d}.png"
```

## Job Model

```json
{
  "job_id": "uuid",
  "created_at": "ISO-8601",
  "input_file": "sheet01.png",
  "input_hash": "sha256",
  "engine_version": "0.1.0",
  "config_hash": "sha256",
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
  "processing_mode": "transparent",
  "content_bbox": [54, 18, 421, 470],
  "status": "PASS",
  "findings": [],
  "actions": [],
  "output_file": "01.png"
}
```

## Reproducibility Metadata
Always retain source hash, config hash, engine version, dependency versions and processing decisions.
