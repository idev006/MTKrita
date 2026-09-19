# MTKrita Developer Handoff Package

## Status
SSOT — Developer Handoff Baseline v1.1

## Purpose
เอกสารนี้เป็นจุดเริ่มต้นสำหรับทีมพัฒนา MTKrita เพื่อให้สามารถรับช่วงงานต่อได้โดยไม่ต้องตีความ requirement, architecture, workflow, quality gate หรือ acceptance criteria ใหม่จากศูนย์

## Read-First Order
ทีมพัฒนาต้องอ่านตามลำดับนี้ก่อนเริ่มแก้ source code:
1. `MASTER_PROJECT_CONTROL.md`
2. `25_DOCUMENT_DRIVEN_SSOT_OPERATING_MODEL.md`
3. `24_MVP_MINIMUM_FUNCTIONAL_BASELINE.md`
4. `02_PRODUCT_REQUIREMENTS.md`
5. `27_END_TO_END_WORKFLOW_SPEC.md`
6. `28_USE_CASE_SPECIFICATION.md`
7. `29_UML_SYSTEM_MODEL.md`
8. `30_SEQUENCE_DIAGRAMS.md`
9. `31_STATE_MACHINE_SPEC.md`
10. `35_INTERFACE_AND_STAGE_CONTRACTS.md`
11. `16_UI_UX_SPECIFICATION.md`
12. `20_REQUIREMENTS_TRACEABILITY_MATRIX.md`
13. `14_SOFTWARE_TEST_STRATEGY.md`
14. `22_DEFINITION_OF_DONE.md`

## Current Delivery State
- M0 Documentation Baseline — complete
- M1 Core Skeleton — complete
- M2 Transparent Processing Baseline — in progress
- M3 Opaque Processing Baseline — next
- M4 Desktop Beta — planned
- M5 Production Automation — planned
- M6 Release Candidate — planned
- M7 Production Release — planned

## Mandatory MVP Processing Contract
```text
Sticker Sheet
  -> Inspect / fingerprint
  -> Detect layout
  -> Split frames
  -> Remove frame border
  -> Remove frame number / metadata
  -> Detect meaningful transparency
       -> transparent: skip background removal
       -> opaque: remove background to transparency
  -> Content bounds / edge safety
  -> Smart fit
  -> QA state
  -> PNG export
  -> Manifest / evidence
```

## Architectural Principles
- Python is the orchestration/control plane.
- Third-party engines/providers are implementation details behind replaceable interfaces.
- Domain rules belong in MTKrita application/domain services, not in UI or provider-specific scripts.
- UI is a replaceable presentation shell and the engine must remain headless-capable.
- UI communicates through application/MainBoard contracts and never owns worker/provider/shared-resource logic.
- PathManager/typed refs control runtime paths.
- Shared mutable resources are brokered centrally.
- Content safety outranks automation rate.
- `REVIEW` is preferred over destructive guessing.
- Source input is immutable by default.
- Lossless-first processing is mandatory.
- No default upscaling.
- Already-transparent frames must not be re-segmented by default.

## UI Handoff Rules
For any desktop UI implementation:
- follow OS theme and DPI conventions by default;
- all user-visible numeric values use Arabic numerals 0-9;
- prefer combo boxes, sliders, range sliders, presets and visual previews over free-form technical input;
- keep normal workflow simple enough for non-technical users;
- expose advanced/diagnostic details through progressive disclosure;
- no authoritative validation, QA policy, stage order, provider choice, path construction, persistence or recovery logic belongs exclusively in the UI;
- the same critical behavior must be reproducible through headless/CLI application paths.

Authoritative UI/UX behavior: `16_UI_UX_SPECIFICATION.md`, ADR-021.

## Required Developer Behaviors
Before implementing a critical change:
1. identify authorizing requirement / ADR / stage contract;
2. confirm acceptance criteria;
3. identify destructive risk;
4. add or update tests;
5. implement behind existing interfaces where applicable;
6. preserve evidence and traceability;
7. update docs when behavior changes.

## Prohibited Shortcuts
- hard-code one observed sheet resolution as universal;
- globally delete a color to remove background, border, or metadata;
- silently crop foreground;
- overwrite source assets;
- put business rules only in GUI code;
- make UI call concrete image-processing providers/workers/shared stores directly;
- construct shared runtime paths directly in UI/worker modules;
- bypass QA state routing;
- change output contract without updating SSOT;
- merge a critical change without objective verification evidence.

## Repository Conventions
- core package: `src/mtkrita`
- tests: `tests/`
- configuration: `configs/`
- SSOT documentation: `docs/`
- CI: `.github/workflows/ci.yml`
- implementation PRs must follow `.github/pull_request_template.md`

## Immediate Development Priority
### M2
Finish transparent-path orchestration and verification:
- hybrid separator refinement
- end-to-end frame pipeline
- `FrameResult` / finding integration
- manifest evidence
- topology regression cases
- CI green

### M3
Implement opaque-path processing:
- uniform / near-uniform background classification
- edge-connected background extraction
- flood-fill / connectivity provider
- mask refinement
- dark-foreground preservation
- confidence-driven REVIEW fallback
- mixed transparent/opaque E2E

## Gate Rule
A milestone is not complete because code exists. It is complete only when:
- required behavior matches SSOT,
- tests pass,
- regression/golden evidence exists,
- traceability is current,
- quality gate criteria are met.

## Handoff Acceptance
The package is considered sufficient for developer onboarding when a developer can answer from SSOT alone:
- what to build,
- why it exists,
- processing order,
- interfaces involved,
- safe/unsafe behavior,
- expected outputs,
- tests required,
- UI/domain ownership boundaries,
- gate needed to finish.
