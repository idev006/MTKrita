# MTKrita Implementation Backlog and Work Breakdown

## Status
SSOT — Engineering Work Breakdown v1.1

## Purpose
แปลง requirement และ architecture ของ MTKrita เป็น work packages ที่ทีมพัฒนาสามารถดำเนินการได้โดยรักษา dependency, acceptance criteria และ quality gates

## Work Package Rules
ทุก work package ต้องมี requirement/ADR mapping, dependency, owner role, acceptance criteria, verification method และ target gate

---

## M2 — Transparent Processing Baseline

### WP-M2-01 Hybrid Sheet Geometry
Requirement: PR-003, PR-004, MF-001
Owner: Senior Software Engineer + Pipeline Engineer
Acceptance: exact 5x2 unchanged; resized sheet splits correctly; ambiguity does not guess destructively.

### WP-M2-02 Border Topology Hardening
Requirement: PR-012, MF-002
Owner: Process Engineer + Software Engineer
Acceptance: supported border variants pass; ambiguous border/artwork contact -> REVIEW.

### WP-M2-03 Frame Metadata / Number Removal Hardening
Requirement: PR-017, MF-003
Owner: Software Engineer + Tester
Acceptance: supported badge removed; artwork numbers preserved; ambiguity refused.

### WP-M2-04 Frame Pipeline Orchestrator
Requirement: PR-019
Owner: Pipeline Engineer
Acceptance: ordered stages, structured results/evidence, no GUI dependency.

### WP-M2-05 Manifest / FrameResult Integration
Requirement: PR-009, PR-011, MF-005
Owner: Pipeline Engineer + Audit roles
Acceptance: every PNG traces to source/config/version/actions.

### WP-M2-06 Transparent Corpus Gate
Owner: Tester + QA Auditor
Acceptance: approved M2 golden corpus + source immutability + CI evidence.

---

## M3 — Opaque Processing Baseline

### WP-M3-01 Background Classification
Classify uniform / near-uniform / complex with evidence and REVIEW fallback.

### WP-M3-02 Edge-Connected Background Provider
OpenCV-based connectivity/flood-fill provider preserving disconnected dark foreground.

### WP-M3-03 Mask Refinement
Preserve anti-alias/white outline and detect/refine halos.

### WP-M3-04 Advanced Fallback Provider Boundary
Stable interface for GrabCut/future ML without provider-specific domain rules.

### WP-M3-05 Opaque Routing Orchestration
Transparent frames bypass segmentation; opaque frames produce RGBA or REVIEW.

### WP-M3-06 Mixed Corpus E2E Gate
Mixed transparent+opaque acceptance evidence; no unsafe foreground deletion.

---

## Platform Architecture Foundation — Before Production Batch M5

### WP-PLAT-01 PathManager + Typed Resource References
**ADR:** ADR-017
**Owner:** Senior Software Engineer
**Work:** central path resolution; SourceRef/ArtifactRef/ScratchRef/OutputRef/EvidenceRef; safe job/worker isolation.
**Acceptance:** no critical runtime path is constructed ad hoc outside approved boundary; traversal/overwrite tests pass.

### WP-PLAT-02 MainBoard Composition Root
**ADR:** ADR-018
**Owner:** Senior Software Engineer + Pipeline Engineer
**Work:** compose JobController, Scheduler, WorkerManager, ResourceBroker, EventBus, JobStore, diagnostics and provider registry without God Object behavior.
**Acceptance:** services have explicit contracts/lifecycle and are testable independently.

### WP-PLAT-03 Durable JobStore
**ADR:** ADR-020
**Owner:** Software Engineer
**Work:** persistent jobs/tasks/attempts/checkpoints/artifact/event/error metadata; SQLite baseline acceptable.
**Acceptance:** abnormal termination does not lose authoritative progress; startup reconciliation tests pass.

### WP-PLAT-04 ResourceBroker + Atomic Artifact Commit
**ADR:** ADR-018, ADR-020
**Owner:** Pipeline Engineer
**Work:** centralized shared-resource ownership and temp->validate->hash->atomic commit flow.
**Acceptance:** workers cannot overwrite final/shared state directly; disk/write failure leaves no false-complete artifact.

### WP-PLAT-05 Worker Manager + Process Isolation
**ADR:** ADR-019
**Owner:** Pipeline Engineer
**Work:** process-based worker pool baseline; private scratch; immutable task envelope; heartbeat.
**Acceptance:** worker crash is isolated and recoverable without crashing whole job.

### WP-PLAT-06 Scheduler / Lease / Attempt Protocol
**ADR:** ADR-019, ADR-020
**Owner:** Pipeline Engineer
**Work:** task leases, attempts, retry policy, stale-result rejection, bounded inflight work.
**Acceptance:** late stale result cannot overwrite newer authoritative attempt.

### WP-PLAT-07 Pause / Stop / Resume / Reconciliation
**ADR:** ADR-020
**Owner:** Pipeline Engineer + Tester
**Work:** safe-boundary pause, graceful stop, durable checkpoint, resume, startup reconciliation.
**Acceptance:** interrupted batch resumes without repeating committed stages or degrading image quality.

### WP-PLAT-08 Central Logging / Events / Diagnostics
**ADR:** ADR-020
**Owner:** Software Engineer + QA/Audit
**Work:** structured log/event sink, stable error codes, correlation IDs, diagnostic bundle.
**Acceptance:** job/frame/stage/worker/attempt can be diagnosed from evidence without relying on console text.

### WP-PLAT-09 Fault-Injection and Recovery Gate
**Owner:** Tester + QA Auditor
**Depends on:** PLAT-01..08
**Work:** worker loss, stale attempt, disk full/write failure, provider failure, forced termination, resume.
**Acceptance:** integrity/recovery invariants in `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md` pass.

---

## M4 — Desktop Beta
- PySide6 shell
- drag/drop job creation
- frame status grid
- source/mask/final overlays
- REVIEW actions
- export flow
- Windows usability/smoke tests

## M5 — Production Automation
Depends on Platform Architecture Foundation gate.
- batch 4 sheets / 40 stickers
- multi-worker parallel processing
- pause/stop/resume/retry/recovery
- batch manifest/report
- ZIP packaging
- resource-aware scheduling/performance evidence

## M6 — Release Candidate
- installer + portable build
- clean Windows verification
- dependency/license inventory
- full golden regression
- reliability fault-injection gate
- operational runbook validation
- known limitations + release audit

## M7 — Production Release
- G4 approval
- checksums/artifacts/release notes
- versioned SSOT snapshot
- release decision record

## Priority Order
1. content safety
2. data/state integrity
3. mandatory MVP contract
4. SSOT/traceability
5. deterministic correctness
6. recoverability
7. LINE compliance
8. usability
9. throughput
10. advanced AI
