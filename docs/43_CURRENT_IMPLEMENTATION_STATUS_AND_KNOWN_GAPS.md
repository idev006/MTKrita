# MTKrita Current Implementation Status and Known Gaps

## Status
SSOT — Engineering Implementation Status v2.2

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
PR #11 now includes verified coverage for:
- deterministic exact + controlled scaled 5×2 extraction;
- bounded visual separator refinement (`configured_refined`) near predicted separators without resampling source pixels;
- ADR-023 source transparency classification before alpha-generating cleanup;
- rounded/inset border discovery after transparent padding;
- visible-support vs visible-color-purity border evidence;
- original edge/single-tone border consensus plus conservative four-side multi-tone fallback;
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

Representative Candidate A/B have been hash-matched and inspected. Evidence-backed hardening TB-001 through TB-005 is now implemented and Windows-CI verified:
- TB-001 rounded-border evidence quality;
- TB-002 post-exclusion local metadata ownership;
- TB-003 alpha-visible metadata topology for transparent sources;
- TB-004 bounded visual separator refinement for shifted gutters;
- TB-005 conservative four-side multi-tone border consensus.

Verified CI checkpoints include #324, #328, #329, #330 and #333; all passed Ruff + pytest. No safety threshold was relaxed to obtain these results.

Representative diagnostics show Candidate B extraction contamination is corrected by bounded separator refinement, and frames requiring different side tones can now enter the explicit multi-tone fallback while normal frames retain the original single-tone path.

**Remaining M2 acceptance blocker:** execute the final integrated Tier-B run on the current PR #11 head, record per-frame PASS/REVIEW/FAIL plus extraction/border/metadata/joint evidence, inspect output for content loss/residue, and obtain owner acceptance.

M2 shall not be declared complete from synthetic CI or isolated component diagnostics alone.

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
- root tree contains only project source/config/docs/tests/tooling;
- production/user Tier-B source bytes are not committed;
- generated PNG/ZIP/database/log/cache/temp/build artifacts are not intentionally part of the PR;
- `.gitignore` covers Python/test caches, environments, build/dist, logs and runtime `outputs/`/`jobs/` without broad suppression of legitimate fixture types;
- GitHub Actions use `actions/checkout@v7` and `actions/setup-python@v7` with `contents: read` least privilege;
- known Pillow joint-cleanup deprecation warnings were removed without behavior change;
- CI #333 passed Ruff + pytest for the latest TB-005 behavior checkpoint.

## Current Gate
PR #11 remains draft because final Tier-B transparent corpus acceptance is still open. `REVIEW > destructive guess` remains mandatory.

## Immediate Engineering Sequence
1. run current PR #11 head against Candidate A/B through refined extraction and full frame pipeline;
2. record extraction provenance, border consensus mode, metadata/joint evidence and per-frame result without committing source bytes;
3. inspect generated provisional/final outputs for silent content loss, border/numeral residue and accidental artwork deletion;
4. fix only evidence-backed defects;
5. close Issue #12 and M2 / Issue #2 when Tier-B acceptance is approved;
6. begin M3 opaque-background implementation;
7. then advance UI/batch productization and Windows packaging/release milestones.

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
