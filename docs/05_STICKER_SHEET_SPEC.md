# Sticker Sheet Specification

## Default Production Sheet

```yaml
sheet:
  rows: 2
  columns: 5
  frames_per_sheet: 10
  nominal_frame_width: 512
  nominal_frame_height: 512
  margin_px: 20
  padding_px: 20
  separator:
    enabled: true
    thickness_px: 3
    color_detection: auto
```

## Important Rule
`512×512` is a **working frame size**, not automatically the final LINE upload size. Final output dimensions are controlled by an export profile.

## Extraction Strategies

### Configured Geometry
Use known rows, columns, margins and frame dimensions.

### Border / Separator Detection
Use visual borders/separators when the sheet has been resized or geometry differs from nominal values.

### Hybrid
Use configured geometry as a prior and image detection to refine actual boundaries.

Hybrid extraction is the target implementation.

## Required Frame Metadata
Every extracted frame must retain:
- index
- row
- column
- x/y
- width/height
- extraction method
- extraction confidence

## Border Handling
Sheet borders are not sticker content. They may be removed only when confidence is high. If artwork touches the border or detection is ambiguous, mark the frame `REVIEW` rather than destructively erasing content.
