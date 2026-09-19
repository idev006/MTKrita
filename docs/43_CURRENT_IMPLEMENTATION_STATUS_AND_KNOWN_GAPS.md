# MTKrita Current Implementation Status and Known Gaps

## Status
SSOT — Engineering Handoff Status v1.2

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

## Active M2 Development
The active implementation line is now **PR #9 / branch `feat/m2-refresh`**, created directly from the latest SSOT baseline on `main`.

PR #8 / branch `feat/m2-transparent-border` is considered the legacy M2 implementation line and should not receive new development once PR #9 is verified. It remains temporarily open only as historical comparison/reference until the refresh branch proves equivalent-or-better behavior.

Implemented on PR #9 at the current handoff point includes:
- configurable deterministic grid splitter
- alpha-aware adaptive per-frame border detector/remover baseline
- conservative top-left metadata/frame-number detector/remover baseline
- source-phase transparency/background routing decision
- provenance regression proving cleanup-generated alpha cannot redefine source transparency routing
- alpha-content analysis using true foreground occupancy
- smart-fit baseline with no upscale by default
- LINE static validator baseline including rejection of fully transparent empty output
- automated unit/component tests for grid, border, metadata, routing, content/fit and LINE validation

## M2 Known Remaining Work
- hybrid separator refinement for resized/non-divisible sheet geometry
- border/artwork same-color topology hardening
- metadata detector hardening against diverse badge styles
- end-to-end `FramePipeline` orchestration
- structured QA findings integrated with `FrameResult`
- manifest/output lineage integration
- transparent golden corpus gate
- final CI green evidence for PR #9

## Architecture Approved but Not Fully Implemented
The following are authoritative architecture, not completed runtime features yet:
- MainBoard control-plane composition
- PathManager + typed resource references
- ResourceBroker + centralized shared-state commit
- durable JobStore/checkpoints
- worker process manager
- task lease / attempt / stale-result rejection
- multi-worker parallel scheduling
- pause / stop / resume / startup reconciliation
- centralized structured logging/event collection
- diagnostic bundle generation
- atomic artifact commit flow

These capabilities should be implemented through the WBS before claiming M5/M6 production-automation readiness.

## M3 Not Yet Complete
Required opaque-background work still includes:
- background classifier
- edge-connected/flood-fill provider
- dark-foreground preservation strategy
- mask refinement / halo handling
- confidence-driven REVIEW fallback
- mixed transparent/opaque E2E

## Current CI Note
PR #9 CI has been started and must complete successfully before the refreshed M2 baseline is considered verified. Until CI is green, M2 remains `IN PROGRESS`.

## Important Handoff Warning
Do not assume a documented capability is implemented merely because it appears in SSOT. Use this status document, GitHub Issues/PRs, tests, and current branch contents together to determine implementation state.

## First Engineering Actions for Incoming Team
1. continue PR #9 from `feat/m2-refresh`;
2. obtain green Ruff + pytest CI evidence;
3. complete remaining M2 work packages and golden-corpus evidence;
4. merge only after gate criteria are met;
5. close/supersede PR #8 after PR #9 is verified;
6. implement M3 opaque pipeline;
7. implement runtime-control architecture work packages before production batch milestone.

## Canonical References
- `37_DEVELOPER_HANDOFF_PACKAGE.md`
- `38_IMPLEMENTATION_BACKLOG_AND_WORK_BREAKDOWN.md`
- `40_ACCEPTANCE_TEST_MATRIX.md`
- `41_M2_M3_IMPLEMENTATION_PLAN.md`
- `50_ENGINEERING_HANDOFF_CHECKLIST.md`
- `51_REFERENCE_IMPLEMENTATION_BLUEPRINT.md`
- `58_SSOT_COVERAGE_AUDIT.md`
- PR #9 (active)
- PR #8 (legacy/superseded after verification)
- Issues #2 and #3
