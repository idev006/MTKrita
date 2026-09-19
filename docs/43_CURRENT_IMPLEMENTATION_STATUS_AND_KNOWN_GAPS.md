# MTKrita Current Implementation Status and Known Gaps

## Status
SSOT — Engineering Handoff Status v1.0

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
- versioned LINE static configuration
- project architecture, workflow, use cases, UML, sequence, state, deployment, recovery, data-flow, stage contracts, security model
- developer handoff/WBS/coding standards/acceptance matrix

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
1. sync/rebase or merge current `main` documentation/governance changes into the M2 branch as appropriate;
2. run Ruff + pytest locally/CI;
3. resolve any conflicts without dropping SSOT changes;
4. complete WP-M2-01 through WP-M2-06;
5. produce M2 acceptance evidence;
6. merge only after gate criteria are met;
7. begin M3 work packages afterward.

## Canonical References
- `37_DEVELOPER_HANDOFF_PACKAGE.md`
- `38_IMPLEMENTATION_BACKLOG_AND_WORK_BREAKDOWN.md`
- `40_ACCEPTANCE_TEST_MATRIX.md`
- `41_M2_M3_IMPLEMENTATION_PLAN.md`
- PR #8
- Issues #2 and #3
