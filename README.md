# MTKrita

MTKrita is an automation-first sticker production project for transforming sticker sheets into LINE-ready sticker assets with repeatable image processing, QA, and export workflows.

> Project status: Documentation & Engineering Governance Baseline v0.2

## Core idea
MTKrita is not a general-purpose image editor. It is a **Sticker Production Automation Machine** positioned between image generation/design and final LINE Creators Market assets.

The system is designed around three input modes:
- `AUTO` — inspect input and select the appropriate processing path.
- `TRANSPARENT` — preserve and process existing meaningful alpha transparency.
- `OPAQUE` — derive/refine foreground masks from non-transparent inputs.

## Canonical production flow

```text
Sticker Sheet
  → Inspect
  → Split Frames
  → Adaptive Per-Frame Border Detection/Removal
  → Transparency / Background Processing
  → Content Analysis
  → Smart Fit
  → QA / Safe Auto-Fix
  → Re-QA
  → LINE Profile Export
  → Manifest / Report
```

## Important guarantees
1. Automation first, but never at the expense of artwork safety.
2. Deterministic processing before AI where practical.
3. Original source files are immutable by default.
4. Border detection is adaptive per frame and may not rely on global color deletion alone.
5. Low-confidence cases become `REVIEW` instead of destructive guesses.
6. Lossless-first processing; preserve anti-aliased alpha edges and minimize resizing.
7. Core processing remains headless-capable and does not require Krita.
8. Windows 11 production distribution targets a standalone installer; users should not need a Python development environment.

## Initial technology direction
- Python
- OpenCV
- Pillow
- NumPy
- ImageMagick (optional adapter/backend)
- PySide6 (planned desktop UI)
- Krita (optional manual-review/editor integration)

## Documentation
The project SSOT is under [`docs/`](docs/).

Start with [`docs/README.md`](docs/README.md), then review:
- [`docs/00_TEAM_GOVERNANCE.md`](docs/00_TEAM_GOVERNANCE.md)
- [`docs/02_PRODUCT_REQUIREMENTS.md`](docs/02_PRODUCT_REQUIREMENTS.md)
- [`docs/03_SYSTEM_ARCHITECTURE.md`](docs/03_SYSTEM_ARCHITECTURE.md)
- [`docs/13_QUALITY_MANAGEMENT_PLAN.md`](docs/13_QUALITY_MANAGEMENT_PLAN.md)
- [`docs/14_SOFTWARE_TEST_STRATEGY.md`](docs/14_SOFTWARE_TEST_STRATEGY.md)
- [`docs/21_PROJECT_EXECUTION_PLAN.md`](docs/21_PROJECT_EXECUTION_PLAN.md)
- [`docs/22_DEFINITION_OF_DONE.md`](docs/22_DEFINITION_OF_DONE.md)

## Current target
The next implementation milestone is **M1 — Core Skeleton**, followed by a Transparent MVP that processes one 5×2 sheet, performs adaptive border handling, preserves alpha/content quality, emits QA evidence and exports valid LINE-profile PNG assets.