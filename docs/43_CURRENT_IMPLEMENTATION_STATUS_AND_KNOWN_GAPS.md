# MTKrita Current Implementation Status and Known Gaps

## Status
SSOT — Engineering Handoff Status v1.1

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
Active work is represented by PR #8 / branch `feat/m2-transparent-border`.

Implemented there at handoff time includes:
- configurable deterministic grid splitter
- adaptive per-frame border detector/remover baseline
- alpha-content analysis
- smart-fit baseline
- LINE static validator baseline
- transparency/background routing decision
- conservative top-left metadata/frame-number detector/remover baseline
- unit tests for major M2 components

## M2 Known Remaining Work
- hybrid separator refinement for resized/non-divisible sheet geometry
- border/artwork same-color topology hardening
- metadata detector hardening against diverse badge styles
- end-to-end `FramePipeline` orchestration
- structured QA findings integrated with `FrameResult`
- manifest/output lineage integration
- transparent golden corpus gate
- final CI green evidence after integration with current `main`

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
The last observed M2 CI failure was static-analysis related (`B008` object construction in default arguments), not a known image-processing logic failure. The relevant defaults were changed to instantiate inside functions on the M2 branch. A fresh CI result is still required before M2 is considered verified.

## Important Handoff Warning
Do not assume a documented capability is implemented merely because it appears in SSOT. Use this status document, GitHub Issues/PRs, tests, and current branch contents together to determine implementation state.

## First Engineering Actions for Incoming Team
1. read `42_DEVELOPER_START_HERE.md` and complete `50_ENGINEERING_HANDOFF_CHECKLIST.md`;
2. sync/rebase or merge current `main` SSOT changes into active implementation branches as appropriate;
3. run Ruff + pytest locally/CI;
4. complete M2 work packages and produce acceptance evidence;
5. merge only after gate criteria are met;
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
- PR #8
- Issues #2 and #3
