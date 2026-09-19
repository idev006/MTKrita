# MTKrita Current Implementation Status and Known Gaps

## Status
SSOT — Engineering Handoff Status v1.3

## Purpose
ป้องกันความสับสนระหว่างสิ่งที่ถูกกำหนดในเอกสารกับสิ่งที่ implement/verify แล้วจริง ณ จุด handoff

## Baseline on `main`
### Completed / Established
- document-driven SSOT governance
- M1 core skeleton
- Python package / CLI baseline
- input inspection + source hashing
- job manifest baseline
- Windows CI workflow
- TOML config baseline + `tomllib` loader/validation tests
- project architecture, workflow, use cases, UML, sequence, state, deployment, recovery, data-flow, stage contracts, security model
- provider interface architecture
- PathManager/MainBoard/ResourceBroker/multi-worker/reliability architecture specifications
- developer handoff/WBS/coding standards/acceptance matrix
- golden-corpus specification, runbook, release checklist, maintenance guide, glossary and team execution playbook

## Active M2 Development — PR #9
The active M2 implementation line is **PR #9 / branch `feat/m2-refresh`**.

PR #8 / `feat/m2-transparent-border` is closed without merge and superseded by PR #9.

Implemented and CI-verified on PR #9 includes:
- exact configured 5×2 extraction
- controlled scaled/non-divisible 5×2 extraction with method/confidence evidence
- alpha-aware adaptive border detection/removal
- full-edge border coverage measurement
- same/near-border-color artwork contact risk → `REVIEW`, no destructive auto-crop
- conservative top-left metadata/frame-number detection/removal
- source-phase transparency/background routing captured before alpha-generating cleanup
- provenance regression proving cleanup-generated alpha cannot redefine source routing
- true foreground occupancy/content analysis
- no-upscale smart fit
- LINE static validation including rejection of fully transparent empty output
- headless `FramePipeline` with structured findings/actions/evidence
- extraction and routing lineage retained in `FrameResult`
- atomic PNG exporter with SHA-256 and overwrite refusal
- manifest/output lineage fields
- synthetic 10-frame end-to-end gate covering split → border → metadata → route provenance → fit → validation → PNG export → manifest → source immutability
- Windows CI run #129: Ruff PASS + pytest PASS

### Remaining M2 Gate Blocker
- **Tier-B approved production/representative transparent corpus evidence**.

Visual separator/hybrid refinement is not an automatic M2 blocker. It becomes required before gate closure only if approved corpus cases cannot be handled safely by exact/scaled deterministic extraction.

## Active Platform Foundation — PR #10
A separate control-plane implementation track has started at **PR #10 / branch `feat/platform-control-foundation`**.

Phase 1 currently implements:
- typed `PathRef` / `PathKind`
- centralized `PathManager`
- isolated job root / output / evidence / log / worker-scratch resolution
- traversal/unsafe identifier rejection
- workspace ownership validation
- automated filesystem tests including non-ASCII path coverage
- `docs/60_PLATFORM_FOUNDATION_IMPLEMENTATION_STATUS.md`

This track is intentionally separate from M2 image-processing work.

## Architecture Approved but Not Fully Implemented
The following remain authoritative architecture with incomplete runtime implementation:
- ResourceBroker + centralized shared-state commit
- durable JobStore/checkpoints
- MainBoard composition root
- event/command envelope + correlation identifiers
- worker process manager
- task lease / attempt / stale-result rejection
- multi-worker parallel scheduling
- pause / stop / resume / startup reconciliation
- centralized structured logging/event collection
- diagnostic bundle generation
- full atomic artifact promotion through ResourceBroker

## M3 Not Yet Complete
Required opaque-background work still includes:
- background classifier
- edge-connected/flood-fill provider
- dark-foreground preservation strategy
- mask refinement / halo handling
- confidence-driven REVIEW fallback
- mixed transparent/opaque E2E

## Verification Note
PR #9 currently has green automated CI evidence including the synthetic E2E gate. It must remain draft until the required Tier-B production/representative corpus evidence is approved or the governing gate is explicitly changed through SSOT.

## Important Handoff Warning
Do not assume a documented capability is implemented merely because it appears in SSOT. Use this status document, GitHub Issues/PRs, tests, and current branch contents together to determine implementation state.

## Current Engineering Priorities
1. obtain/approve Tier-B M2 transparent corpus evidence;
2. keep PR #9 green and merge only after M2 exit criteria are satisfied;
3. continue PR #10 platform foundation with ResourceBroker/JobStore/MainBoard contracts;
4. begin M3 opaque pipeline only against the approved source-transparency provenance contract;
5. implement multi-worker/recovery work packages before claiming production batch readiness.

## Canonical References
- `37_DEVELOPER_HANDOFF_PACKAGE.md`
- `38_IMPLEMENTATION_BACKLOG_AND_WORK_BREAKDOWN.md`
- `40_ACCEPTANCE_TEST_MATRIX.md`
- `41_M2_M3_IMPLEMENTATION_PLAN.md`
- `50_ENGINEERING_HANDOFF_CHECKLIST.md`
- `51_REFERENCE_IMPLEMENTATION_BLUEPRINT.md`
- `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`
- `58_SSOT_COVERAGE_AUDIT.md`
- PR #9 — active M2
- PR #10 — active platform foundation
- PR #8 — closed/superseded
- Issues #2 and #3
