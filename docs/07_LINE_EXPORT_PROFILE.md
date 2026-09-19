# LINE Export Profile

## Status
Baseline verified against official LINE Creators Market static-sticker guideline on 2026-09-19. Official LINE documentation remains authoritative at release time and must be rechecked before declaring a build submission-ready.

## Purpose
LINE-specific constraints are isolated from the core engine so requirements can be updated without rewriting image-processing logic.

## Static Sticker Baseline
Current official requirements include:
- sticker count: 8 / 16 / 24 / 32 / 40
- sticker image: maximum 370 × 320 px
- main image: 240 × 240 px
- chat thumbnail icon: 96 × 74 px
- PNG format
- RGB color mode
- transparent image background
- even-numbered width and height
- at least 72 dpi guidance
- maximum 1 MB per image
- ZIP upload maximum 60 MB when all images are submitted together
- LINE recommends around 10 px margin between trimmed image and surrounding content, considering overall visual balance

Official source: https://creator.line.me/en/guideline/sticker/

## Working Frame vs Final Export

```text
Working frame (for example 512×512 or larger)
        ↓
Border/foreground/content analysis
        ↓
Smart fit on lossless working representation
        ↓
Single final target resize when required
        ↓
LINE export canvas/profile
        ↓
Final PNG
```

The 512×512 source cell is never assumed to be the final upload size.

## Default Profile Candidate

```yaml
profile:
  id: line_static
  verified_date: 2026-09-19
  output_format: png
  color_mode: RGBA
  max_width: 370
  max_height: 320
  require_even_dimensions: true
  transparent_background: true
  min_dpi_guidance: 72
  recommended_content_margin_px: 10
  max_file_size_bytes: 1048576
  max_zip_size_bytes: 62914560
  allowed_counts: [8, 16, 24, 32, 40]
  main_image:
    width: 240
    height: 240
  tab_image:
    width: 96
    height: 74
```

## Validation Rules
A frame cannot be labeled LINE-ready unless all blocking profile checks pass. MTKrita must distinguish source working size from final export size and must not degrade source quality by repeatedly resizing intermediate artifacts.

## Versioning
Every release manifest should record the export-profile version and verification date used to generate the package.