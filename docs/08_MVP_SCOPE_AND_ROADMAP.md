# MVP Scope and Roadmap

## Phase 0 — Documentation
Deliverables:
- architecture
- requirements
- processing rules
- QA rules
- data/config schema
- test plan

## Phase 1 — Core MVP
Goal: reliably process one 5×2 sticker sheet.

Features:
- CLI
- file inspection
- fixed/hybrid extraction
- transparent mode
- basic opaque background removal
- content bounds
- smart fit
- PNG export
- QA JSON + human-readable summary

## Phase 2 — Desktop UI
- drag/drop
- sheet preview
- 10-frame thumbnails
- status per frame
- before/after preview
- review queue
- manual override
- export controls

## Phase 3 — Robust Opaque Mode
- background classification
- multiple segmentation strategies
- mask confidence
- edge refinement

## Phase 4 — Production Automation
- 4-sheet / 40-sticker batch
- job queue
- presets
- ZIP output package
- reproducible manifests
- regression corpus

## Phase 5 — Krita Integration
- open REVIEW frame in Krita
- re-import corrected output
- re-QA

## Phase 6 — Intelligent QA
- OCR/caption verification
- duplicate detection
- visual consistency
- optional AI segmentation/review

## MVP Exit Criteria
- correct extraction of golden 5×2 sheets
- deterministic output
- no source overwrite
- no silent destructive crop
- per-frame QA reasons
- regression tests for both transparent and opaque inputs
