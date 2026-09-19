# MTKrita Current Implementation Status and Known Gaps

## Status
SSOT — Engineering Implementation Status v2.1

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
Windows CI currently verifies:
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
- deterministic exact + controlled scaled 5×2 extraction with method/confidence evidence;
- source transparency classification captured before any alpha-generating cleanup (ADR-023);
- bounded inset-border discovery after transparent padding;
- per-side border offset/thickness/color/confidence/contact evidence;
- localized border-contact ranges and REVIEW-first contact safety;
- anchored frame-number metadata detection with geometry/compactness/dominance evidence;
- analysis-only border exclusion without granting deletion authority;
- safe fragment association when approved exclusion splits one raw metadata topology group;
- exact exclusion-mask identity binding between associated metadata and border evidence;
- enclosed-visible-hole completion for interior badge details such as dark numerals;
- exclusion-aware shape-confidence evidence without expanding the deletion mask or lowering thresholds;
- `JointCleanupPlanner` SAFE_PLAN/REVIEW contract with deterministic bounded mask/hash;
- transparent-source joint border+metadata cleanup wired into `FramePipeline` only for SAFE_PLAN;
- opaque-source metadata/joint cleanup remains plan-only and does not create alpha before M3;
- content analysis, no-upscale smart fit and LINE static validation;
- atomic PNG scratch/export with SHA-256 and overwrite refusal;
- `M2FrameTaskExecutor` behind the platform TaskExecutor boundary;
- real Windows spawned-child M2 execution through candidate → MainBoard validation → ADR-024 final commit;
- synthetic 10-frame E2E and regression suite.

## Tier-B Acceptance Boundary
Issue #12 tracks production-like transparent corpus hardening without committing user/source image bytes.

The implementation blockers discovered from representative sheets have now been addressed in code and regression tests:
- inset decorative border after transparent outer padding;
- same/near-border-color inner-contact refusal;
- metadata badge discrimination at the top-left anchor;
- localized contact evidence;
- joint border+metadata planning;
- fragment association under approved exclusion;
- exact border/exclusion identity validation;
- interior dark-detail completion;
- confidence preservation through analysis exclusion without threshold relaxation.

**Remaining M2 acceptance blocker:** run the current integrated head against the owner-approved Tier-B production/representative transparent corpus, record per-frame PASS/REVIEW/FAIL evidence, and confirm that no Critical silent-content-loss defect exists.

M2 shall not be declared complete from synthetic CI alone.

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
At the current PR #11 head:
- root tree contains only project source/config/docs/tests/tooling;
- no production/user Sticker Sheet bytes are committed for Tier-B diagnostics;
- no generated PNG/ZIP/database/log/cache/temp/build artifacts are part of the PR;
- `.gitignore` covers Python/test caches, environments, build/dist, logs and runtime `outputs/`/`jobs/` without hiding legitimate image/database fixtures globally;
- GitHub Actions use current `actions/checkout@v7` and `actions/setup-python@v7` with `contents: read` least privilege;
- Pillow `Image.fromarray(..., mode=...)` deprecation warnings in joint cleanup have been removed without behavior change;
- Windows CI #320 at commit `b23c9c6a6601bbbd0df0acc73976a723e943bfd0` passed setup, Ruff and pytest.

## Current Gate
PR #11 remains draft because Tier-B transparent corpus acceptance is still open. `REVIEW > destructive guess` remains mandatory.

## Immediate Engineering Sequence
1. run current PR #11 head against the owner-approved Tier-B representative transparent corpus;
2. capture source hash, extraction provenance, border/metadata/joint evidence and per-frame result without committing private source bytes;
3. fix only evidence-backed defects found by Tier-B, keeping thresholds and safety policy explicit;
4. close M2 acceptance / Issue #2 when Tier-B evidence is approved;
5. begin M3 opaque-background implementation;
6. then advance UI/batch productization and Windows packaging/release milestones.

## Canonical References
- `35_INTERFACE_AND_STAGE_CONTRACTS.md`
- `43_CURRENT_IMPLEMENTATION_STATUS_AND_KNOWN_GAPS.md`
- `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`
- `60_PLATFORM_FOUNDATION_IMPLEMENTATION_STATUS.md`
- `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`
- `37_DEVELOPER_HANDOFF_PACKAGE.md`
- `40_ACCEPTANCE_TEST_MATRIX.md`
- `41_M2_M3_IMPLEMENTATION_PLAN.md`
- PR #10, PR #11
- Issues #2, #12 and #3
