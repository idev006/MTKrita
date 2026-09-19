# MTKrita

MTKrita is an automation-first sticker production project for transforming sticker sheets into LINE-ready sticker assets with repeatable image processing, QA, and export workflows.

> Project status: Documentation / Architecture foundation

## Core idea

MTKrita is not intended to become a general-purpose image editor. Its primary role is a **Sticker Production Automation Machine** that sits between image generation/design and final LINE Creators Market assets.

The system is designed around three input modes:

- `AUTO` — inspect the input and select the processing pipeline automatically.
- `TRANSPARENT` — process sticker sheets that already contain meaningful alpha transparency.
- `OPAQUE` — process sticker sheets without transparency and derive/refine foreground masks before export.

## Initial architecture

- Python
- OpenCV
- Pillow
- NumPy
- ImageMagick (optional processing backend)
- PySide6 (planned desktop UI)
- Krita (planned manual-review integration; not forked for MVP)

## Project principles

1. Automation first.
2. Deterministic processing before AI where possible.
3. Non-destructive source handling.
4. Explainable QA findings.
5. Human review for uncertain cases.
6. Config-driven rules and export profiles.
7. Reproducible outputs and processing logs.

## Documentation

Project SSOT is maintained under [`docs/`](docs/).

Start with:

- [`docs/01_PROJECT_CHARTER.md`](docs/01_PROJECT_CHARTER.md)
- [`docs/02_PRODUCT_REQUIREMENTS.md`](docs/02_PRODUCT_REQUIREMENTS.md)
- [`docs/03_SYSTEM_ARCHITECTURE.md`](docs/03_SYSTEM_ARCHITECTURE.md)
- [`docs/04_IMAGE_PROCESSING_PIPELINE.md`](docs/04_IMAGE_PROCESSING_PIPELINE.md)
- [`docs/06_QA_RULEBOOK.md`](docs/06_QA_RULEBOOK.md)
- [`docs/08_MVP_SCOPE_AND_ROADMAP.md`](docs/08_MVP_SCOPE_AND_ROADMAP.md)

## Current phase

**Phase 0 — Documentation and architecture foundation**

The next implementation milestone is a Core MVP that can ingest one 5×2 sticker sheet, extract 10 frames, process transparent or opaque inputs, evaluate content bounds and edge safety, smart-fit the artwork, export PNG files, and emit machine-readable QA results.
