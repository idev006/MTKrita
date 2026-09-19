# UI/UX Specification

## Status
SSOT — UI/UX Baseline v1.1

## Core UI Architecture Principle
The UI is a **replaceable presentation shell around the MTKrita engine**.

The UI shall not own critical business rules, pipeline sequencing, provider-selection rules, QA policy, destructive-action policy, path/resource ownership, job state, or recovery logic.

The engine must remain fully usable through headless/CLI execution without a desktop UI. A future desktop UI, alternate UI toolkit, web UI, automation API, or other presentation layer must be able to use the same application/domain services without duplicating business logic.

```text
Desktop UI / CLI / Future UI
          ↓
Application Facade / Commands / View Models
          ↓
MainBoard / Orchestrator / Domain Services
          ↓
Provider Interfaces / Runtime Services
```

### UI boundary rules
- UI translates user intent into application commands.
- UI renders engine state/results/events.
- UI may validate presentation-level input constraints, but authoritative validation occurs in the application/domain layer.
- UI must not call OpenCV/Pillow/provider implementations directly.
- UI must not build runtime paths directly; use PathManager/application services.
- UI must not write shared state, manifests, job store, or final artifacts directly.
- UI must not invent PASS/REVIEW/FAIL decisions.

## UX Goal
ผู้ใช้ควรสามารถนำ Sticker Sheet เข้า → ตรวจผล → แก้เฉพาะ exception → export ได้ โดยไม่ต้องเข้าใจ OpenCV, alpha channels, pipeline internals หรือ command line

Primary objective: **simple enough for non-technical users, visual enough to understand what will happen before committing an action.**

## Visual / Theme Policy
- Follow the operating-system theme by default (light/dark/system appearance).
- Avoid custom theming that fights Windows conventions unless required for accessibility.
- Respect OS scaling/DPI and standard interaction conventions.
- All numeric values shown to users use **Arabic numerals 0–9** consistently, including Thai-language UI.
- Do not use Thai numerals for counters, dimensions, percentages, indices, ranges, progress, timestamps, or configuration values.

## Control Selection Principles
Prefer controls that reduce typing and make valid ranges visible:
- combo box for finite option sets
- slider for intuitive bounded scalar values
- range slider for min/max thresholds
- spin box only when precise numeric entry is useful
- segmented/toggle controls for small mutually exclusive modes
- visual preset/profile selection rather than free-form configuration
- direct manipulation / preview overlay where it reduces ambiguity

Avoid exposing raw technical parameters by default. Advanced values should use progressive disclosure.

## Primary Windows Workflow
1. Drag/drop one or more sheets
2. Select or auto-detect profile
3. Press `Analyze & Process`
4. View frame status board
5. Review only `REVIEW/FAIL`
6. Export eligible outputs

## Main Screen Concept
```text
┌──────────────────────────────────────────────┐
│ MTKrita                                     │
├──────────────────────────────────────────────┤
│ Drop Sticker Sheet Here                     │
│ Mode: [AUTO ▼]   Profile: [LINE Static ▼]  │
│ [Analyze & Process]                         │
├──────────────────────────────────────────────┤
│ 01 PASS   02 PASS   03 REVIEW   04 PASS ... │
│                                              │
│ Preview: Source | Mask | Processed | Final  │
│                                              │
│ Findings / Measurements / Actions           │
├──────────────────────────────────────────────┤
│ [Review Queue] [Export Passed] [Export All] │
└──────────────────────────────────────────────┘
```

## Progressive Disclosure
Default view shows only information needed to complete the task. Technical details such as alpha statistics, mask confidence, border thickness, provider strategy, worker/attempt information and diagnostic IDs are expandable.

Recommended levels:
1. Basic — normal users
2. Advanced — users tuning thresholds/profiles
3. Diagnostics — support/development information

## Review Experience
For a REVIEW frame show:
- source preview
- detected border overlay
- foreground/background mask overlay
- intended removal overlay
- reason for review in plain language
- confidence where useful
- recommended safe action

Controls should favor clear choices over technical editing:
- Accept proposed fix
- Keep as-is
- Keep border
- Force border removal (explicit risk confirmation)
- Re-run with selected preset/threshold
- Open in external editor/Krita
- Re-run QA

## Visualization Principles
Wherever practical show rather than describe:
- before/after preview
- transparency checkerboard
- detected frame/grid overlay
- border/metadata highlight
- mask overlay
- safe-margin guides
- target-size preview
- batch progress by sheet/frame

Changes to sliders/ranges should update preview when computationally safe and affordable; expensive recomputation should be explicitly triggered or debounced.

## Status Semantics
Do not rely on color alone. Always display text/icon:
- PASS
- AUTO FIXED
- REVIEW
- FAIL

## Batch / Multi-worker UX
UI presents centralized job state from MainBoard; it does not communicate with workers directly.

Show:
- total jobs/sheets/frames
- completed / running / queued / review / failed counts
- overall progress
- pause / resume / stop controls
- current stage in plain language

Worker-level details belong in Diagnostics view, not the normal workflow.

## Pause / Stop / Resume UX
- Pause = stop scheduling new work and reach safe checkpoint boundaries.
- Resume = continue from persisted state/checkpoints.
- Stop = controlled stop, not destructive process termination.
- UI must explain when an action is waiting for workers to reach a safe boundary.

## Error UX
Show user-centered error summaries first, with optional technical detail.

Example:
```text
ไม่สามารถประมวลผลเฟรม 07 ได้
ระบบไม่มั่นใจว่าพื้นที่สีดำส่วนใดเป็นพื้นหลัง
สถานะ: REVIEW
[ดูตัวอย่าง] [ปรับค่า] [รายละเอียด]
```

Technical details may expose stable error code/correlation ID for diagnosis.

## Destructive Action UX
Any operation capable of deleting uncertain pixels must be explicit, previewable and reversible within the job. Original files are never overwritten by default.

## Accessibility / Ease of Use
- keyboard-operable primary workflow
- readable Windows DPI scaling
- no color-only meaning
- clear focus states
- Thai and English text render correctly
- labels use plain language before technical jargon
- sensible defaults minimize configuration
- common workflow should require minimal clicks
- advanced configuration should never be required for supported standard input

## Performance UX
Long-running jobs must expose progress and never appear frozen. UI receives event/progress state from MainBoard/application services rather than polling provider internals directly.

## Installation UX
Normal user target: install → launch → drag/drop → process. Developer dependencies remain hidden from end users.

## Acceptance Rules
UI implementation is acceptable only if:
1. engine tests can run without importing UI packages;
2. critical behavior is reproducible through CLI/headless application path;
3. changing UI toolkit does not require moving domain rules;
4. no UI module directly owns provider/resource/shared-state behavior;
5. basic workflow is usable without exposing technical image-processing terminology;
6. numeric display follows Arabic-numeral policy;
7. system theme and OS scaling are respected.

References: `03_SYSTEM_ARCHITECTURE.md`, `29_UML_SYSTEM_MODEL.md`, `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`, `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`.
