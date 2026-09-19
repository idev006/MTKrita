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

## ADR-017 — Centralized PathManager and ResourceBroker
**Status:** Accepted

All runtime paths that participate in the application contract shall be resolved through `PathManager` or typed path references. Workers shall not construct shared project/output paths ad hoc. Shared mutable resources, final artifact promotion, manifest persistence and scarce resources are mediated by a `ResourceBroker`/`ResourceManager` owned by the control plane.

Workers may directly use only immutable inputs and their own private scratch resources.

## ADR-018 — MainBoard Is the Internal Control Plane
**Status:** Accepted

MTKrita uses a MainBoard/control-plane architecture composed of specialized services such as `JobController`, `Scheduler`, `WorkerManager`, `EventBus`, `ResourceBroker`, `JobStore`, `LogSink` and `PathManager`.

MainBoard is a coordination architecture, not a monolithic God Object. Cross-component communication uses explicit commands/events with correlation identifiers and versioned schemas.

## ADR-019 — Parallel Compute, Centralized Commit
**Status:** Accepted

MTKrita shall support batch and multi-worker parallel processing. CPU/image computation may execute concurrently in isolated worker processes, while shared-state commitment and final artifact publication are serialized/transactional through MainBoard-owned services.

Workers shall not directly mutate shared job state, manifests, final output namespaces or shared log files. Task attempts use leases/attempt IDs so stale or duplicate worker results cannot overwrite authoritative results.

## ADR-020 — Reliability, Recovery and Observability Are First-Class Requirements
**Status:** Accepted

Pause, stop, resume, retry, crash recovery, checkpointing, idempotency, structured logging, error codes, diagnostics and startup reconciliation are architectural requirements, not later operational add-ons.

Jobs and checkpoints must have durable state independent of worker memory. A process/worker crash must never create a false `COMPLETED` state. Critical outputs are atomically promoted and recorded with provenance/hashes before completion is accepted.

## ADR-021 — UI Is a Replaceable Presentation Shell
**Status:** Accepted

Desktop UI, CLI and future presentation layers are adapters over application/domain services. Critical business rules, pipeline sequencing, provider selection, QA decisions, resource/path ownership, persistence and recovery logic shall not live in the UI layer.

The engine must remain operational headlessly. Replacing the desktop toolkit or introducing another presentation surface must not require moving or duplicating domain rules.

UI design rules:
- follow OS theme and DPI conventions by default
- all user-visible numeric values use Arabic numerals 0-9
- prefer constrained visual controls such as combo boxes, sliders, range sliders and visual presets over free-form technical entry
- use progressive disclosure so normal users see simple task-oriented controls while advanced/diagnostic details remain available
- favor visual previews/overlays over technical explanations where practical
- UI communicates with MainBoard/application services, never directly with workers/providers/shared mutable stores

## ADR-022 — Design for Testability and Automated Verification
**Status:** Accepted

Testability is a first-class architecture property. Critical modules must be designed so they can be exercised headlessly and automatically without UI interaction.

Rules:
- inject/replace infrastructure and provider dependencies where needed
- avoid hidden global mutable state
- provide stable seams for filesystem/path, time, ID generation, stores, broker, transport and provider behavior
- business/domain logic must be independently testable
- provider implementations must pass shared contract tests
- CI must run automated unit/component/contract tests and selected regression fixtures
- critical reliability behavior must support automated fault-injection and recovery tests
- every reproducible critical defect should become a permanent regression test

Reference: `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`.
