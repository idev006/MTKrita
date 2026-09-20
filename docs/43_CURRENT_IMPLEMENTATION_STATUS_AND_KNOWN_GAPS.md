# MTKrita Current Implementation Status and Known Gaps

## Status
SSOT — Engineering Implementation Status v2.4

## Purpose
แยกให้ชัดเจนระหว่างสิ่งที่อยู่ในเอกสาร สิ่งที่ implement แล้วจริง สิ่งที่ verify แล้วจริง และงานที่ยังเป็น release blocker เพื่อให้ทีมพัฒนารับช่วงต่อโดยไม่ต้องเดาจาก commit history

## Current Development Topology
- `main` — approved baseline / merged history
- PR #10 / `feat/platform-control-foundation` — verified platform/control-plane foundation
- PR #11 / `feat/m2-platform-integration` — maintained M2 + platform integration authority, stacked on PR #10
- PR #9 — closed as superseded by PR #11
- PR #8 — legacy M2 line; not an active development authority

New M2 production work shall continue on PR #11 until its gate is satisfied.

## Implemented and Verified — Platform / Runtime
Windows CI verifies:
- centralized `PathManager` and typed path/resource ownership;
- immutable staged INPUT namespace, SHA-256/size verification and source preservation;
- `ResourceBroker`-controlled private scratch and final artifact promotion;
- SQLite `JobStore` v3, migrations, durable descriptors, generations, attempts, leases and stale-write protection;
- pause/stop/resume safe-boundary policy and startup reconciliation;
- ADR-024 durable artifact commit intent and crash recovery;
- MainBoard composition, EventBus, JSONL logging and diagnostic bundle baseline;
- bounded fair scheduler, durable reconstruction, backpressure and worker-loss handling;
- Windows `spawn` workers, versioned JSON IPC and real-process runtime tests;
- immutable ExecuteTask v2 and candidate-only worker results;
- CandidateResultCoordinator authority chain through ResourceBroker + ADR-024 before durable SUCCEEDED;
- strict M2 task descriptor and MainBoard-owned final target resolution.

## Implemented and Verified — M2 Transparent Pipeline
PR #11 includes verified coverage for:
- deterministic exact + controlled scaled 5×2 extraction;
- bounded visual separator refinement (`configured_refined`) near predicted separators without resampling source pixels;
- ADR-023 source transparency classification before alpha-generating cleanup;
- rounded/inset border discovery after transparent padding;
- visible-support vs visible-color-purity border evidence;
- original edge/single-tone border consensus plus conservative four-side multi-tone fallback;
- explicit `border_consensus_mode`, `border_requires_review` and `border_review_reason` frame evidence;
- fail-closed rejection of incoherent multi-tone constructed thickness;
- three-side differently colored border evidence routes REVIEW rather than collapsing into absence;
- per-side border offset/thickness/color/confidence/contact evidence;
- localized border-contact ranges and REVIEW-first contact safety;
- anchored frame-number metadata detection with geometry/compactness/dominance evidence;
- alpha-visible raw metadata topology for meaningfully transparent sources and RGB-background fallback for opaque sources;
- analysis-only border exclusion without granting deletion authority;
- post-exclusion local ownership and safe fragment association;
- exact exclusion-mask identity binding;
- enclosed-visible-hole completion for dark numeral/detail pixels;
- exclusion-aware shape confidence without expanding deletion scope or lowering thresholds;
- `JointCleanupPlanner` SAFE_PLAN/REVIEW contract;
- transparent-source joint border+metadata cleanup only for SAFE_PLAN;
- opaque-source metadata/joint cleanup remains plan-only and does not create alpha before M3;
- content analysis, no-upscale smart fit and LINE static validation;
- atomic PNG scratch/export with SHA-256 and overwrite refusal;
- `M2FrameTaskExecutor` behind the platform TaskExecutor boundary;
- real Windows spawned-child execution through candidate → MainBoard validation → ADR-024 final commit;
- synthetic 10-frame E2E and permanent regression coverage.

## Tier-B Acceptance Boundary
Issue #12 tracks production-like transparent corpus hardening without committing user/source bytes.

TB-001 through TB-005 and the corpus-driven TB-005 safety corrections are implemented and Windows-CI verified. Relevant checkpoints include #324, #328/#329, #330, #333, #340, #347 and #351. No safety threshold or global color tolerance was relaxed.

Current integrated hash-matched corpus run after CI #351:
- Candidate A: REVIEW 10/10;
- Candidate B: REVIEW 10/10;
- PASS/AUTO_FIXED/FAIL: 0 across the 20 representative frames;
- source SHA-256 remained unchanged before/after for both candidates;
- Candidate B frames 3 and 5 now route `BORDER.AMBIGUOUS` instead of the previous unsafe `AUTO_FIXED` border-residue path;
- no representative frame currently receives automatic destructive output.

This is a meaningful safety improvement but **does not satisfy M2 Tier-B acceptance** because supported decorative border/metadata cleanup has not yet demonstrated intended integrated automatic behavior.

The next evidence-backed blocker is border-contact topology / incomplete border-band ownership. Representative frames show very long inner matching strips (for example Candidate B frame 1 right ≈0.905 and bottom ≈0.809; frame 7 left ≈0.921) and other contact concentrated near rounded corners. These observations do not authorize lowering the contact threshold or widening color tolerance; a stronger ownership/topology model is required.

M2 shall not be declared complete from synthetic CI, isolated component diagnostics, or safety-only all-REVIEW corpus behavior.

## M3 Opaque Route — Not Yet Production-Complete
Remaining work:
- background classifier;
- edge-connected/flood-fill background provider;
- dark foreground preservation and safe foreground/background topology;
- mask refinement / halo handling;
- confidence-driven REVIEW fallback;
- combine approved metadata cleanup mask with opaque background removal in one final alpha result;
- mixed transparent/opaque E2E and Tier-B corpus evidence.

Opaque M2 inputs currently remain REVIEW/plan-only rather than being destructively modified before M3.

## UI / UX
Architecture and UX SSOT are defined; production desktop UI is not yet the active implementation milestone.

Locked rules:
- UI is a replaceable presentation shell around application/MainBoard services;
- no critical business/pipeline rules in UI callbacks;
- OS theme/DPI behavior;
- Arabic numerals `0–9` for user-visible numeric data;
- task-oriented controls, combo boxes, sliders/range sliders, presets and visual previews;
- engine remains fully headless and automation-testable.

## Windows Distribution
Source-runtime Windows processing and spawned-child execution are verified. Packaged/frozen executable verification remains pending.

Remaining distribution work includes packaged `spawn` smoke, installer/frozen-runtime selection, signing, release automation and final release evidence.

## Repository Hygiene / Toolchain State
At the current PR #11 line:
- production/user Tier-B source bytes are not committed;
- generated PNG/ZIP/database/log/cache/temp/build artifacts are not intentionally part of the PR;
- `.gitignore` covers runtime/caches without broad suppression of legitimate fixture types;
- GitHub Actions use `actions/checkout@v7` and `actions/setup-python@v7` with `contents: read` least privilege;
- CI #351 passed Ruff + pytest for the current border-ambiguity/evidence checkpoint.

## Current Gate
PR #11 remains draft. `REVIEW > destructive guess` remains mandatory.

**M2 Tier-B: NOT ACCEPTED.** Issue #12 and Issue #2 remain open.

## Immediate Engineering Sequence
1. specify the next border-contact topology / complete border-band ownership contract from current integrated evidence;
2. add synthetic regressions before/with implementation, including rounded-corner-only contact, long adjacent decorative-tone continuation and real artwork touching the inner edge;
3. preserve the existing contact-risk threshold and fail closed unless ownership is proven;
4. require Windows Ruff + pytest PASS;
5. rerun hash-matched Candidate A/B read-only and inspect every automatic output;
6. sync evidence and close M2 only after representative Tier-B acceptance is actually satisfied;
7. begin M3 opaque-background implementation only after M2 gate closure;
8. then advance UI/batch productization and Windows packaging/release milestones.

## Canonical References
- `35_INTERFACE_AND_STAGE_CONTRACTS.md`
- `43_CURRENT_IMPLEMENTATION_STATUS_AND_KNOWN_GAPS.md`
- `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`
- `60_PLATFORM_FOUNDATION_IMPLEMENTATION_STATUS.md`
- `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`
- `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`
- `66_TIER_B_METADATA_AND_EXTRACTION_REFINEMENT_SPEC.md`
- `67_MULTITONE_BORDER_CONSENSUS_SPEC.md`
- `37_DEVELOPER_HANDOFF_PACKAGE.md`
- `40_ACCEPTANCE_TEST_MATRIX.md`
- `41_M2_M3_IMPLEMENTATION_PLAN.md`
- PR #10, PR #11
- Issues #2, #12 and #3
