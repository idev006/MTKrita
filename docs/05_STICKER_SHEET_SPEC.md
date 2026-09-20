# Sticker Sheet Specification

## Status
SSOT — Sticker Sheet Geometry Baseline v1.2

## Default Production Sheet

```toml
[sheet]
rows = 2
columns = 5
frames_per_sheet = 10
margin_x = 20
margin_y = 20
gap_x = 0
gap_y = 0

[sheet.nominal_frame]
width = 512
height = 512

[sheet.separator]
enabled = true
thickness_px = 3
color_detection = "auto"
```

## Important Rule
`512×512` is a **working frame size**, not automatically the final LINE upload size. Final output dimensions are controlled by an export profile.

## Extraction Strategies

### 1. Configured Exact Geometry
Use known rows, columns, margins and gaps when usable geometry divides exactly.

Evidence:
- method = `configured_exact`
- confidence = `1.0`

### 2. Configured Scaled Geometry
For a known grid that has been uniformly resized and no longer divides exactly, proportional boundaries may be rounded deterministically when per-cell size variation stays within the configured safety tolerance.

Evidence must include:
- method = `configured_scaled`
- extraction confidence
- maximum cell-width variation
- maximum cell-height variation

This strategy must refuse geometry whose variation exceeds the approved tolerance.

### 3. Visual Border / Separator Refinement
Use detected visual separators/borders when configured/scaled geometry is insufficient or ambiguous.

This is an advanced fallback, not permission to guess. Low-confidence visual geometry routes to `REVIEW`.

### 4. Hybrid
Use configured geometry as a prior and visual evidence to refine boundaries where needed.

For M2, exact geometry plus controlled scaled-geometry fallback satisfies the deterministic baseline for known 5×2 layouts. Visual/hybrid refinement remains an extension path and becomes mandatory before the relevant gate only if approved corpus cases cannot be handled safely by the deterministic strategies.

## Required Frame Metadata
Every extracted frame must retain:
- index
- row
- column
- extraction rectangle / x-y-width-height
- extraction method
- extraction confidence
- relevant geometry measurements

## Border Handling
Sheet/frame borders are not sticker content. They may be removed only when confidence is high and contact-risk analysis does not indicate possible artwork loss.

A valid border may begin at the frame edge **or** after a bounded transparent/empty outer inset created by source scaling, rounded corners or sheet spacing. Border detection may search inward only inside an approved near-edge band and must retain the detected inset offset as evidence.

Inset-border auto-removal requires stronger topology evidence than a single visible strip. At minimum, a fallback inset detector must use multi-side geometric/color consensus (or an equivalent conservative topology test) before it may classify a near-edge structure as a frame border. A single artwork strip must never be sufficient authority for destructive crop.

If artwork or frame metadata touches the border, same/near-border-color content continues into the inner boundary, or detection is otherwise ambiguous, the frame must be marked `REVIEW` rather than destructively cropped. Detection of a border does not by itself authorize removal.

## Configuration Rule
Human-maintained sheet configuration is TOML. YAML examples are not authoritative configuration for MTKrita.

References: `09_DATA_MODELS_AND_CONFIG.md`, `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `45_TOML_CONFIGURATION_SPEC.md`, ADR-016.
