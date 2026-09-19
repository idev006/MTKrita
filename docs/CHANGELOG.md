# Documentation Changelog

## v0.8 — 2026-09-19
- Accepted ADR-026: `ExecuteTask` is immutable and worker results remain candidates until durable control-plane acceptance.
- Added `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md` defining exact candidate validation order, one-primary-artifact MVP cardinality, MainBoard-owned target resolution and ADR-024 success commitment.
- Implemented Windows spawn worker process/session adapter, validated worker-event routing and WorkerRuntimeController.
- Added real Windows CI smoke coverage for spawn, ready, heartbeat, graceful stop/process exit and ExecuteTask transport.
- Added strict ExecuteTask command builder/parser, TaskExecutor interface and versioned candidate-result schema.
- Added `CandidateResultCoordinator` enforcing durable RUNNING worker/attempt authority, active lease, BUSY ownership, provisional hash/size validation and trusted final target resolution.
- Successful candidates now reach durable SUCCEEDED only through the existing ADR-024 artifact commit protocol; REVIEW/FAILED transition durably before runtime ownership release.
- Explicitly restricted current success contract to exactly one primary artifact per task; multi-artifact atomic/group commit requires a separate design decision.
- Added regression tests for stale attempts, wrong authority, hash/size mismatch, cross-job target, zero/multiple artifacts and runtime ownership release.
- Added component end-to-end authority test: dispatch → ExecuteTask → test executor scratch → validated candidate → ADR-024 commit → durable success.
- Updated Windows worker IPC spec to v1.2, platform status to v2.5 and documentation index to include task/result authority SSOT.
- Current code checkpoint passed Ruff + pytest on Windows CI; packaged/frozen spawn and concrete M2 image executor integration remain future gates.

## v0.7 — 2026-09-19
- Extended platform control-plane implementation with centralized JSONL logging, safe diagnostic bundles, bounded fair scheduling, WorkerManager heartbeat/lifecycle tracking, durable dispatch coordination and worker-loss watchdog recovery.
- Added ADR-025: scheduler reconstruction must use durable task descriptors rather than runtime-memory guesses.
- Upgraded JobStore to schema v3 with explicit v1→v2→v3 migration and durable task descriptor/priority metadata.
- Legacy v2 tasks without execution descriptors are explicitly non-reconstructable instead of receiving invented scheduling meaning.
- Added `SchedulerReconstructor` and automated tests for restart eligibility, priority preservation, deferred queue capacity and unsupported descriptor rejection.
- Added `61_WINDOWS_WORKER_PROCESS_AND_IPC_SPEC.md` defining Windows spawn isolation, explicit command/event channels and non-pickle authoritative IPC.
- Added versioned UTF-8 JSON worker IPC codec with schema/type/identity/size validation and automated protocol tests.
- Updated Platform Foundation Implementation Status to v2.3 and documentation index accordingly.
- Latest code verification for JobStore v3, scheduler reconstruction and JSON IPC passed Ruff + pytest.

## v0.6 — 2026-09-19
- Implemented and documented the platform-control foundation track in PR #10.
- Added PathManager typed resource ownership and ResourceBroker centralized artifact promotion.
- Added durable SQLite JobStore v2 with compatible v1→v2 migration, task attempts, leases and CAS stale-write protection.
- Added versioned command/event envelopes, in-process EventBus and MainBoard composition root.
- Added pause/stop/resume lifecycle control and idempotent startup reconciliation.
- Extended the state machine with PAUSING, PAUSED, STOPPING, STOPPED and INTERRUPTED semantics.
- Accepted ADR-024 for durable commit intent across filesystem and JobStore boundaries.
- Added durable artifact commit journal/coordinator/reconciler and fault-injection tests for crash-after-promotion, missing final files, hash mismatch and superseded attempts.
- Added ordered startup recovery so valid promoted artifacts are reconciled before orphaned RUNNING tasks are interrupted.
- Updated Platform Foundation Implementation Status to v1.7.

## v0.5 — 2026-09-19
- Finalized architecture principles for PathManager, MainBoard/control plane, ResourceBroker, multi-worker isolation, leases/attempts, centralized shared-state commitment, pause/resume/recovery and observability.
- Added engineering handoff checklist and reference implementation blueprint.
- Added golden corpus/test-data specification.
- Added operational runbook for pause/resume/recovery/worker loss/provider failure.
- Added release and sign-off checklist.
- Added project glossary/naming standard.
- Added maintenance/extension guide and team execution playbook.
- Added SSOT coverage audit and marked documentation READY FOR DEVELOPMENT HANDOFF.
- Updated Documentation Index and Master Project Control to expose the final handoff package.

## v0.4 — 2026-09-19
- Added developer handoff package and onboarding entry point.
- Added actionable implementation backlog / work breakdown for M2 through release.
- Added coding standards and repository conventions.
- Added formal acceptance test matrix mapped to mandatory MVP capabilities and milestone gates.
- Added M2/M3 near-term implementation sequence and integration checkpoints.
- Added current implementation status and known gaps to distinguish documented behavior from implemented/verified behavior.
- Updated documentation index and Master Project Control to expose a single developer handoff entry path.

## v0.3 — 2026-09-19
- Promoted supported input archetypes into main SSOT.
- Added formal end-to-end workflow specification including happy, alternate, review and failure flows.
- Added use case specification covering processing, review, resume/retry, export, transparent/opaque routing, border removal, metadata removal and 40-sticker batch flow.
- Added UML system model with context, component, class, provider and package dependency diagrams.
- Added sequence diagrams for main, transparent, opaque, review and recovery flows.
- Added job/frame/stage state machine specification.
- Added deployment and runtime architecture for Windows 11 standalone operation.
- Added error, recovery and idempotency specification.
- Added data flow and artifact lifecycle specification.
- Added interface and stage contracts for all critical pipeline stages.
- Added security and file safety model.
- Added project team roles and competency model.
- Strengthened Document-Driven SSOT rule: if important knowledge is not captured in approved SSOT, it is not yet project truth.
- Updated documentation index, Master Project Control and requirements traceability to reference the behavioral model suite.

## v0.2 — 2026-09-19
- Added project governance, virtual professional roles, RACI and quality gates.
- Expanded product requirements with adaptive per-frame border detection/removal.
- Added quality-preserving processing requirements: lossless-first, anti-aliased alpha preservation, minimal resize, no default upscaling.
- Added Quality Management Plan and comprehensive Software Test Strategy.
- Added Process Engineering Specification and Pipeline Engineering Guide.
- Added UI/UX Specification focused on exception-first review.
- Added Windows 11 standalone distribution plan.
- Added Audit/Compliance Plan and Requirements Traceability Matrix.
- Added Project Execution Plan and Definition of Done.
- Added documentation index and new ADRs for border removal, quality transforms, headless/Krita boundary and Windows distribution.
- Revalidated LINE static sticker export baseline against official guidelines dated 2026-09-19.

## v0.1 — 2026-09-19
- Initialized MTKrita project documentation.
- Defined automation-machine product vision.
- Defined transparent / opaque / auto processing modes.
- Defined MVP architecture and non-destructive safety principles.
- Defined QA states and auto-fix boundaries.
- Defined configurable LINE export profile.
- Defined roadmap, data models, test plan, risks and license notes.
- Recorded decision not to fork Krita during MVP.
