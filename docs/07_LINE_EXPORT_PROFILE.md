# LINE Export Profile

## Purpose
LINE-specific constraints are isolated from the core engine so rules can be updated without rewriting image-processing logic.

## Static Sticker Baseline
The project currently targets standard static LINE stickers. Before every production release, verify the current official LINE Creators Market guidelines.

Reference assumptions for the initial profile:
- PNG output
- RGB/RGBA
- transparent sticker background
- sticker image maximum canvas: 370 × 320 px
- main image: 240 × 240 px
- chat thumbnail/tab image: 96 × 74 px
- allowed set counts include 8 / 16 / 24 / 32 / 40

## Working Frame vs Final Export

```text
Working frame (e.g. 512×512)
        ↓
Content analysis + smart fit
        ↓
LINE export canvas/profile
        ↓
Final PNG
```

The 512×512 source cell is never assumed to be the final upload size.

## Config Example

```yaml
profile:
  id: line_static
  output_format: png
  color_mode: RGBA
  max_width: 370
  max_height: 320
  require_even_dimensions: true
  transparent_background: true
  max_file_size_bytes: 1048576
  allowed_counts: [8, 16, 24, 32, 40]
  main_image:
    width: 240
    height: 240
  tab_image:
    width: 96
    height: 74
```

Official LINE documentation remains authoritative at release time.
