# Architecture Decision Records

## ADR-001 — Build an Automation Engine, Not a General Image Editor
**Status:** Accepted

Project value is sticker-specific automation. Existing editors already solve general canvas/layer/manual-editing problems.

## ADR-002 — Do Not Fork Krita for MVP
**Status:** Accepted

Build an independent engine first to avoid upstream merge and maintenance complexity.

## ADR-003 — Deterministic Before AI
**Status:** Accepted

Use rule-based image processing whenever the problem can be solved reliably without AI.

## ADR-004 — Three Input Modes
**Status:** Accepted

`AUTO`, `TRANSPARENT`, `OPAQUE`.

## ADR-005 — Conservative Automation
**Status:** Accepted

If uncertain, return `REVIEW` rather than perform destructive correction.

## ADR-006 — Config-Driven Export Profiles
**Status:** Accepted

LINE-specific constraints must not be scattered through core source code.

## ADR-007 — 512×512 Is a Working Frame
**Status:** Accepted

The source production sheet may use 512×512 cells. Final upload assets are generated through an export profile.

## ADR-008 — Adaptive Border Removal Runs Per Frame After Split
**Status:** Accepted

Borders may differ by color, thickness and side. Detect/removal therefore occurs on each extracted frame using edge position, continuity, geometry and connectivity. Color-only deletion is prohibited as a general strategy. Ambiguous border/artwork contact becomes `REVIEW`.

## ADR-009 — Quality-Preserving Transform Policy
**Status:** Accepted

Use lossless-first processing, preserve alpha edge information, avoid repeated resizing, preserve aspect ratio and disable automatic upscaling by default. Prefer one final resize for target export.

## ADR-010 — Core Must Remain Headless and Krita-Optional
**Status:** Accepted

Krita is a manual-review/editor integration, not a mandatory runtime dependency of the core pipeline.

## ADR-011 — Windows Distribution Hides Developer Dependencies
**Status:** Accepted

Production Windows users should receive a standalone application/installer and must not be required to install Python/OpenCV/toolchains manually.

## ADR-012 — Python Is the MTKrita Orchestration and Control Plane
**Status:** Accepted

Python coordinates the end-to-end sticker workflow, applies domain rules, selects processing routes/providers, enforces confidence thresholds and QA states, and records manifests/evidence. Python is not required to reimplement every lower-level image algorithm.

## ADR-013 — Engine-Agnostic Provider Architecture
**Status:** Accepted

OpenCV, Pillow, ImageMagick or future ML providers may implement lower-level image-processing capabilities behind stable interfaces. MTKrita domain logic owns when and why a provider is used. Replacing a provider should not require rewriting the complete workflow where practical.

## ADR-014 — Document-Driven SSOT Governs Implementation
**Status:** Accepted

Approved SSOT documents define product behavior, architecture, processing rules, acceptance criteria and release gates before or together with implementation. Source code and GitHub execution records must not silently redefine upstream requirements. Critical changes require synchronized requirement/design/test/traceability evidence before completion.

## ADR-015 — Interface-First Provider Boundaries
**Status:** Accepted

All replaceable processing capabilities shall be accessed through explicit provider interfaces or protocols. The Python orchestrator depends on contracts, not concrete OpenCV/Pillow/ImageMagick/ML implementations. Concrete providers may be swapped through configuration without changing sticker-domain workflow code where practical.

Mandatory provider boundaries include, at minimum:
- layout/grid detection
- border detection/removal
- frame metadata detection/removal
- background classification/removal
- content analysis
- image transform/smart fit
- export

Provider interfaces must return structured results/evidence rather than only modified images.

## ADR-016 — TOML Is the Canonical Configuration Format
**Status:** Accepted

Human-maintained MTKrita configuration shall use TOML as the canonical format. Python 3.11+ shall load TOML using the standard-library `tomllib` for read operations. Runtime configuration models validate parsed data before pipeline execution.

Rules:
- configuration is external to source code where behavior is intended to be configurable
- shipped profiles are version-controlled TOML files
- unknown/invalid critical keys fail validation rather than being silently ignored
- config hashes are included in job evidence for reproducibility
- JSON remains acceptable for machine-generated manifests/evidence; TOML is the human configuration standard
