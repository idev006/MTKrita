# MTKrita Product Use-Case Acceptance Matrix

## Status
SSOT Extension — Product Acceptance Contract v1.0

## Purpose
MTKrita is complete only when the program performs the intended user workflows safely, repeatably, and efficiently. Passing unit tests, synthetic fixtures, or individual algorithms is necessary evidence, but it is not by itself product acceptance.

This matrix ties every implementation milestone to an end-to-end user outcome.

## Product-Level Acceptance Principles

1. **Use Case First** — implementation work must identify which real user workflow it enables or hardens.
2. **Safety Before Automation** — `REVIEW > destructive guess` remains mandatory. Automation rate may improve only through stronger evidence, never by lowering a safety threshold.
3. **Source Immutability** — original user input is never modified in place.
4. **Deterministic Evidence** — identical immutable input and configuration must produce the same routing, findings, actions, and evidence.
5. **Control-Plane Authority** — workers use staged immutable input, write only private scratch, and return candidates. Final publication is owned by MainBoard / ResourceBroker / ADR-024.
6. **Representative Acceptance** — synthetic CI is required but cannot substitute for representative Tier-B corpus acceptance.
7. **UI Independence** — business rules and safety decisions remain in the engine/control plane. UI is a replaceable shell.
8. **Recoverability** — interruption, worker failure, stale results, or restart must not corrupt source data or publish an invalid artifact.
9. **Repository Hygiene** — production corpus bytes and generated runtime artifacts remain outside Git history.

## Core Use Cases

### UC-01 — Transparent 5×2 Sticker Sheet, Clean Geometry
**User goal:** Drop a transparent 5×2 sheet and obtain 10 correctly extracted LINE sticker candidates.

Required behavior:
- detect/refine 5×2 frame geometry;
- preserve source bytes;
- process all 10 frames deterministically;
- no resampling during extraction;
- remove only authorized border/metadata;
- smart-fit without upscaling;
- validate LINE static-sticker profile;
- export atomically through the control plane.

Acceptance evidence:
- Windows Ruff + pytest PASS;
- representative sheet produces correct 10-frame extraction;
- visual QA finds no crop loss, residue, or accidental deletion;
- source SHA-256 unchanged.

### UC-02 — Scaled or Slightly Misaligned 5×2 Sheet
**User goal:** Process a sheet whose separators do not land exactly on an ideal equal grid.

Required behavior:
- bounded deterministic separator refinement;
- no arbitrary free-form crop search;
- stable extraction rectangles across repeated runs;
- ambiguous geometry routes to REVIEW.

Current authority: TB-004.

### UC-03 — Single-Tone Transparent Border
**User goal:** Remove a confidently detected border while preserving sticker artwork.

Required behavior:
- border color may vary by input;
- transparent outer padding must not be mistaken for black border;
- same-color artwork away from the border is preserved;
- same-color artwork touching the inner boundary remains REVIEW unless ownership is independently proven.

### UC-04 — Rounded / Multi-Tone Decorative Border
**User goal:** Automatically clean supported rounded or multi-tone decorative borders without deleting artwork.

Required behavior:
- rounded visible support is separate from color purity;
- multi-tone fallback requires coherent side geometry;
- rejected strong border evidence remains explicit REVIEW rather than collapsing to no-border;
- reciprocal rounded-corner continuation may reduce residual contact only under TB-006 Class A rules;
- long decorative-band continuation remains REVIEW until Class B completion is separately implemented and accepted.

Current authority: TB-001, TB-005, TB-006.

### UC-05 — Frame Number / Corner Metadata Cleanup
**User goal:** Remove frame-number badges or equivalent corner metadata when ownership is safe.

Required behavior:
- analysis exclusion prevents border pixels from corrupting metadata detection;
- local fragment association only;
- enclosed visible-hole handling remains bounded;
- border/metadata contact is owned by JointCleanupPlanner / ADR-028;
- remote artwork is never absorbed into metadata ownership.

### UC-06 — Mixed Border + Metadata Contact
**User goal:** Process a frame where decorative border and frame-number metadata touch or overlap.

Required behavior:
- produce an explicit joint cleanup plan;
- SAFE_PLAN is required before destructive cleanup;
- TB-006 corner explanation cannot double-count metadata ownership;
- unresolved contact remains REVIEW.

### UC-07 — Opaque Background Sticker Sheet
**User goal:** Process an opaque-background sheet into transparent LINE-ready stickers.

Required behavior:
- M2 recognizes that background removal is required;
- no destructive segmentation is performed before M3 authority exists;
- M3 must preserve character, text, dark details, thin strokes, and edge quality;
- halo and foreground loss must be bounded by explicit evidence/tests.

Gate: **Not accepted until M3 is implemented and separately approved.**

### UC-08 — Batch Processing Multiple Sheets
**User goal:** Process several sheets without manually repeating the workflow for each frame.

Required behavior:
- bounded scheduling/backpressure;
- task isolation;
- deterministic per-sheet/per-frame status;
- one failed or REVIEW frame must not corrupt unrelated work;
- final publication remains ResourceBroker/MainBoard-owned.

### UC-09 — REVIEW → Human Decision → Resume
**User goal:** Resolve only ambiguous frames instead of redoing the whole job.

Required behavior:
- REVIEW has concrete reason/evidence;
- no destructive action occurs before review resolution;
- approved continuation resumes from authoritative staged data;
- decisions are auditable;
- UI may present/collect the decision but may not contain the safety rule itself.

### UC-10 — Crash / Restart / Stale Worker Recovery
**User goal:** Recover safely after process interruption or worker failure.

Required behavior:
- leasing/CAS prevents stale-result publication;
- startup reconciliation identifies incomplete work;
- worker private scratch cannot become durable success by itself;
- successful final artifacts remain consistent and atomic.

Current authority: platform foundation, JobStore v3, ADR-024.

### UC-11 — LINE-Ready Export
**User goal:** Receive files that satisfy the configured LINE static sticker profile.

Required behavior:
- required output mode/size constraints validated;
- transparent output where required;
- no unintended upscale;
- atomic PNG write and hash evidence;
- invalid export remains REVIEW/FAIL rather than silently publishing.

### UC-12 — Practical Desktop Workflow
**User goal:** Use the system without understanding the internal algorithms.

Required behavior:
- drag/drop or equivalent input selection;
- clear progress/status per sheet/frame;
- clear distinction among PASS, AUTO_FIXED, REVIEW, FAIL;
- preview of REVIEW cases and reasons;
- safe resume/export actions;
- OS theme;
- Arabic numerals for numeric UI;
- combo boxes / sliders / range sliders where they improve direct manipulation;
- no important business rule embedded in the UI.

Gate: UI acceptance occurs only after the engine workflows it exposes have authoritative behavior.

## Product KPI Contract

The following shall be measured on representative accepted corpus/workloads rather than inferred from unit tests alone:

- `auto_process_rate` — percentage of frames ending PASS/AUTO_FIXED without human intervention;
- `review_rate` — percentage routed to REVIEW;
- `false_safe_rate` — automatic outputs later found to contain destructive loss or unsafe residue; target is effectively zero for accepted supported classes;
- `false_review_rate` — supported safe cases unnecessarily routed to REVIEW;
- `visual_acceptance_rate` — automatic outputs passing representative visual QA;
- `sheet_processing_time` — end-to-end time for a 10-frame sheet on the reference Windows environment;
- `recovery_success_rate` — interrupted jobs restored/reconciled without invalid publication;
- `interaction_count` — user actions required from import to accepted export for normal supported workflows.

Performance optimization must not trade away safety evidence.

## Milestone Gate Mapping

### M2 — Transparent Workflow
M2 is accepted only when:
- UC-01 through UC-06 and UC-11 are demonstrated for the supported transparent classes;
- representative Tier-B corpus demonstrates useful automatic behavior, not 100% REVIEW;
- every newly automatic representative output is visually inspected;
- no known false-safe path remains open;
- Windows CI is green;
- owner acceptance is recorded.

Current state: **NOT ACCEPTED**.

### M3 — Opaque Background Workflow
M3 begins only after the M2 gate is closed.
M3 acceptance is primarily UC-07 plus regressions proving M2 behavior remains intact.

### Desktop Product Acceptance
Desktop product acceptance requires the accepted engine milestones plus UC-08, UC-09, UC-10, and UC-12 end-to-end evidence.

## Work Prioritization Rule

Every non-maintenance implementation item should answer:

> Which Use Case does this change enable, improve, or make safer, and what acceptance evidence will prove that outcome?

If an item cannot answer that question, it is not a product-priority item unless it is explicitly classified as infrastructure debt, security work, or repository hygiene.

## Immediate Mapping

- TB-006 Phase 1 → UC-04 and UC-06; objective is reducing false REVIEW from proven reciprocal rounded-corner continuation without lowering safety thresholds.
- Future TB-006 Class B → UC-04; objective is complete decorative border-band ownership.
- Representative Candidate A/B rerun → M2 product acceptance evidence for UC-01/04/05/06/11.
- M3 work remains blocked until M2 product gate closes.

References: `43_CURRENT_IMPLEMENTATION_STATUS_AND_KNOWN_GAPS.md`, `60_PLATFORM_FOUNDATION_IMPLEMENTATION_STATUS.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`, `67_MULTITONE_BORDER_CONSENSUS_SPEC.md`, `68_BORDER_CONTACT_TOPOLOGY_SPEC.md`, ADR-024, ADR-028, Issue #2, Issue #12, PR #11.
