# Supported Input Archetypes

## Status
SSOT Addendum — Input Coverage Baseline v1.0

## Purpose
กำหนดรูปแบบ input จริงที่ MTKrita ต้องรองรับ เพื่อให้การออกแบบ pipeline, QA และ test corpus ยึดจากงาน production จริง ไม่ใช่เฉพาะ synthetic fixtures

## Archetype A — Opaque Black Sticker Sheet with Colored Frame Border

Representative production characteristics observed from user-provided examples:

- image format: PNG
- pixel size: 1536 × 613
- image mode: RGB (no alpha channel)
- layout: 2 rows × 5 columns = 10 frames per sheet
- frame background: opaque black
- frame separator/border: colored rounded rectangle, light green in the current examples
- border width is visually thin relative to frame size and may vary across future sheets
- each frame may contain character artwork, Thai caption text, white sticker outline, props/decorative elements, and frame sequence badge/number near a corner
- foreground may contain dark/black pixels, therefore global black color-key removal is unsafe

## Mandatory Processing Behavior

### Sheet detection and split
The system shall detect or infer the 2×5 frame layout without assuming a fixed total sheet size. 1536×613 is an observed supported size, not a hard-coded requirement.

### Border removal
Border removal shall occur per-frame after split and support varying colors, varying thicknesses, anti-aliased edges, rounded corners, and slight resizing/compression effects. The system shall not remove pixels solely because they match the border color.

### Background removal
For this archetype, the opaque black background shall be converted to transparency using edge-connected/background-topology evidence, not global black deletion.

Preferred strategy:
1. remove/high-confidence crop the frame border,
2. sample/categorize the outer background,
3. identify edge-connected background regions,
4. create/refine alpha mask,
5. preserve disconnected dark content belonging to sticker artwork,
6. preserve white anti-aliased sticker outlines,
7. route ambiguous cases to REVIEW.

### Dark foreground safety
Black or near-black artwork must be protected when it is not topologically connected to the background region, including hair, Thai text strokes, shadows and accessories.

### Sequence markers
Frame numbering badges are sheet metadata by default, not sticker content. Detection/removal shall be configurable because future sheet templates may differ.

### Quality preservation
- no JPEG intermediate
- preserve anti-aliased edges
- no default upscale
- one final downscale where possible
- alpha edge halos shall be part of QA

## Acceptance Tests Required
The regression suite shall include cases equivalent to opaque RGB sheet, black background, colored rounded frame borders, 2×5 grid, dark hair/text, decorative elements close to frame boundary, frame numbering badge near corner, alternate border colors/widths, and resized sheets whose cell geometry is not perfectly divisible.

## Expected End-to-End Result

```text
Opaque RGB Sheet
    ↓
Detect 2×5 layout
    ↓
Split 10 frames
    ↓
Adaptive border removal
    ↓
Remove/configure sequence badge
    ↓
Edge-connected background segmentation
    ↓
RGBA foreground with preserved dark artwork
    ↓
Content bounds + smart fit
    ↓
LINE profile QA
    ↓
PASS / AUTO_FIXED / REVIEW / FAIL
```

## Design Rule
A successful result is not merely "black background removed". A successful result must preserve all intended sticker artwork, including dark content and anti-aliased edges, while producing a clean transparent background suitable for downstream export.
