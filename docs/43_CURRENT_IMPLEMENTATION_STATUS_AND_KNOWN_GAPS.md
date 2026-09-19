# MTKrita Current Implementation Status and Known Gaps

## Status
SSOT — Engineering Implementation Status v2.0

## Purpose
ป้องกันความสับสนระหว่างสิ่งที่กำหนดในเอกสารกับสิ่งที่ implement/verify แล้วจริง และระบุเส้นทางพัฒนาปัจจุบันเพียงเส้นเดียว

## Current Development Topology
- `main` — approved baseline / merged history
- PR #10 / `feat/platform-control-foundation` — platform/control-plane foundation
- PR #11 / `feat/m2-platform-integration` — maintained M2 + platform integration authority, stacked on PR #10
- PR #9 — closed as superseded by PR #11
- PR #8 — legacy M2 line, no longer an active development authority

New M2 production work shall continue on PR #11 until its gate is satisfied. Do not restart work on PR #8/#9.

## Implemented and Verified — Core / Platform
Verified Windows CI coverage now includes:
- centralized PathManager and typed path/resource ownership;
- immutable staged INPUT namespace and source hash verification;
- ResourceBroker-controlled shared/final artifact promotion;
- SQLite JobStore v3, migrations, durable jobs/tasks/descriptors, leases/attempts and stale-write CAS protection;
- pause/stop/resume policy and startup reconciliation;
- ADR-024 durable artifact commit intent and crash reconciliation;
- MainBoard composition, EventBus, centralized JSONL logging and diagnostic bundle baseline;
- bounded fair scheduler, durable scheduler reconstruction and backpressure;
- WorkerManager, heartbeat/watchdog and worker-loss interruption/requeue path;
- Windows `spawn` worker process adapter, versioned JSON IPC and real-process smoke tests;
- immutable ExecuteTask v2 contract and candidate-only worker results;
- CandidateResultCoordinator authority chain through ResourceBroker + ADR-024 before durable SUCCEEDED;
- strict M2 durable task descriptor and MainBoard-owned final target resolution.

## Implemented and Verified — M2 Transparent Pipeline
PR #11 currently includes and tests:
- deterministic exact + controlled scaled 5×2 extraction with method/confidence evidence;
- source transparency classification captured before alpha-generating cleanup (ADR-023);
- alpha-aware border detection including bounded inset-border discovery after transparent padding;
- per-side border offset/thickness/color/confidence/contact evidence;
- localized border contact ranges and REVIEW-first contact safety;
- conservative anchored frame-number metadata detection with geometry/compactness/dominance evidence;
- analysis-only border exclusion for metadata diagnostics without granting deletion authority;
- enclosed-visible-hole completion for safe inclusion of interior badge details such as dark numerals;
- metadata/exclusion completeness guards that prohibit standalone removal when joint cleanup is required;
- content analysis, no-upscale smart fit and LINE static validation;
- atomic PNG scratch/export support with SHA-256 and overwrite refusal;
- `M2FrameTaskExecutor` mapping behind the platform TaskExecutor boundary;
- real Windows spawned-child M2 execution through candidate result → MainBoard validation → ADR-024 final commit;
- synthetic 10-frame E2E and imported M2 regression suite.

## Active Tier-B Hardening
Issue #12 tracks production-like transparent corpus findings discovered without committing user/source image bytes.

Implemented/verified hardening:
- inset decorative border detection after transparent outer padding;
- same/near-border-color inner-contact refusal;
- anchor-aware metadata discrimination;
- localized border-contact evidence;
- `JointCleanupPlanner` baseline producing SAFE_PLAN/REVIEW without mutating during planning;
- deterministic bounded joint mask/hash and removal-ratio safety;
- analysis exclusion fragmentation evidence and planner refusal when metadata completeness is unresolved;
- enclosed-visible-hole completion for interior numeral/detail pixels.

Still in progress:
- safe fragment association for metadata split by approved border-analysis exclusion;
- proof that associated metadata mask is complete and can be used only with the exact border evidence;
- wiring approved joint border+metadata cleanup into `FramePipeline` while preserving ADR-023 source transparency provenance;
- Tier-B owner-approved production/representative transparent corpus acceptance.

Until these are complete, overlap/ambiguous cases remain REVIEW. No threshold is lowered merely to force automation.

## M3 Opaque Route — Not Yet Implemented to Production Level
Required work remains:
- opaque background classifier;
- edge-connected/flood-fill background provider;
- dark foreground preservation and safe background/foreground topology;
- mask refinement/halo handling;
- confidence-driven REVIEW fallback;
- metadata-mask integration with opaque background removal;
- mixed transparent/opaque E2E and Tier-B corpus evidence.

## UI / UX
Architecture and UX SSOT are defined, but production desktop UI is not yet the active implementation milestone.

Rules already locked:
- UI is a replaceable presentation shell around MainBoard/application services;
- no critical business/pipeline rules in UI callbacks;
- OS theme/DPI behavior;
- Arabic numerals 0–9;
- task-oriented controls, combo boxes, sliders/range sliders, presets and visual previews;
- engine remains fully headless/testable.

## Windows Distribution
Architecture and distribution plan are documented. Current Windows CI proves Python/runtime child-process behavior, but packaged/frozen executable verification is still pending.

Remaining distribution work includes installer/frozen-runtime selection, packaged `spawn` smoke, signing/release pipeline and final release evidence.

## Repository / Verification State
- PR #11 is the maintained M2 integration authority and remains draft.
- PR #9 is superseded and closed.
- no production/user Sticker Sheet bytes are committed for Tier-B diagnostics; hashes/measurements only.
- generated PNG/log/database/cache/temp/build artifacts are not part of the PR.
- every accepted behavioral change is expected to carry regression coverage and Windows CI evidence.

## Current Gate
M2 is not yet release-complete because Tier-B transparent corpus acceptance remains open. The current implementation deliberately prefers REVIEW over destructive guessing.

## Immediate Engineering Sequence
1. finish safe metadata fragment association under the SSOT v1.9 rules;
2. verify fragment completeness + enclosed-detail mask evidence;
3. integrate JointCleanupPlanner into FramePipeline only for SAFE_PLAN;
4. rerun full Windows Ruff + pytest + real-process E2E;
5. run representative Tier-B transparent corpus and record owner acceptance;
6. close M2 gate / Issue #2 when acceptance evidence is complete;
7. begin M3 opaque-background implementation;
8. then advance UI/batch-productization/distribution milestones.

## Canonical References
- `35_INTERFACE_AND_STAGE_CONTRACTS.md`
- `43_CURRENT_IMPLEMENTATION_STATUS_AND_KNOWN_GAPS.md`
- `60_PLATFORM_FOUNDATION_IMPLEMENTATION_STATUS.md`
- `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`
- `37_DEVELOPER_HANDOFF_PACKAGE.md`
- `40_ACCEPTANCE_TEST_MATRIX.md`
- `41_M2_M3_IMPLEMENTATION_PLAN.md`
- `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`
- PR #10, PR #11
- Issues #2, #12 and #3
