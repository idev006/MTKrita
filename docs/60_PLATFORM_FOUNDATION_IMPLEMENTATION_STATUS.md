# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v2.8

## Purpose
Track implementation of the PathManager/MainBoard/ResourceBroker/multi-worker/control-plane architecture separately from image-algorithm maturity while reflecting the verified integration now maintained on PR #11.

## Current Tracks
- PR #10 / `feat/platform-control-foundation` — platform/control-plane foundation
- PR #11 / `feat/m2-platform-integration` — stacked integration authority combining the verified platform boundary with the M2 image pipeline

## Implemented and Verified Platform Foundation

### Durable authority and resources
- typed `PathRef` and centralized `PathManager`;
- immutable staged job INPUT namespace;
- `ResourceBroker`-controlled staging, verification, private scratch and final promotion;
- source preservation, overwrite refusal, SHA-256 and byte-size evidence;
- SQLite `JobStore` v3 with explicit migrations;
- durable job/task state, generation, attempt, worker identity, leases and stale-write protection;
- durable versioned task descriptors and scheduler priority.

### Lifecycle, recovery and commitment
- pause/stop/resume safe-boundary policy;
- startup reconciliation for orphaned jobs/tasks;
- ADR-024 durable artifact commit intent bridging filesystem promotion and JobStore finalization;
- artifact-first startup reconciliation;
- stale/superseded attempts cannot claim success.

### MainBoard / observability
- MainBoard composition root with specialized services rather than a God Object;
- versioned `MessageEnvelope` + EventBus;
- centralized JSONL LogSink;
- job-scoped diagnostic bundle baseline with secret redaction and no source/private image bytes by default.

### Scheduler / workers
- bounded fair scheduler with queue/inflight limits, priority and anti-starvation;
- `DispatchCoordinator` with compensation on runtime assignment failure;
- `WorkerLossCoordinator` and heartbeat/watchdog;
- durable scheduler reconstruction from eligible task descriptors only;
- Windows `spawn` process adapter behind replaceable worker interfaces;
- separate command/event channels;
- versioned UTF-8 JSON IPC; authoritative pickle/domain-object IPC prohibited;
- `WorkerEventRouter` and `WorkerRuntimeController`;
- real Windows child-process lifecycle/heartbeat/graceful-stop CI coverage.

### ExecuteTask / result authority
- ADR-026 immutable ExecuteTask and candidate-only worker result model;
- ADR-027 control-plane-staged immutable worker inputs;
- ExecuteTask v2 with verified `inputs[]` and private scratch;
- no worker-selected final target;
- strict candidate payload validation;
- `CandidateResultCoordinator` verifies exact durable RUNNING job/task/worker/attempt/lease;
- successful candidate passes ResourceBroker verification and ADR-024 before durable SUCCEEDED;
- REVIEW/FAILED remain control-plane transitions;
- stale/malformed/hash-mismatch/size-mismatch/cross-job/multi-artifact candidates cannot create durable success.

## Verified M2 Integration on PR #11
The platform-only integration gap has been closed on the stacked branch:
- strict `M2FrameTaskDescriptor` schema;
- MainBoard-owned `M2FrameTargetResolver`;
- `M2FrameTaskExecutor` adapting the headless image pipeline behind injected seams;
- static built-in `m2.frame` registration; task payload cannot choose module/callable/import path;
- independent staged-input integrity verification inside worker execution;
- PASS/AUTO_FIXED → exactly one provisional scratch PNG candidate;
- REVIEW → no false success artifact;
- FAIL → structured task failure;
- source and staged input remain immutable;
- real Windows spawned-child E2E verifies staged input → durable dispatch/lease → ExecuteTask → child M2 pipeline → candidate → MainBoard validation → ResourceBroker/ADR-024 commit → durable SUCCEEDED → final PNG.

Final output is not published merely because a worker produced a candidate; final publication remains MainBoard authority.

## Current Image-Pipeline Hardening Boundary
PR #11 now contains verified Tier-B-oriented safety mechanisms while keeping policy in the image/domain layer:
- inset decorative border discovery after transparent padding;
- localized border contact ranges;
- anchored metadata discrimination;
- analysis-only border exclusion;
- safe fragment association for one approved raw metadata topology group;
- exact exclusion-mask identity binding to border evidence;
- enclosed-visible-hole completion for dark numeral/detail pixels;
- exclusion-aware confidence evidence without expanding deletion scope;
- `JointCleanupPlanner` SAFE_PLAN/REVIEW contract;
- transparent-source joint cleanup integrated in `FramePipeline` only for SAFE_PLAN;
- opaque-source cleanup remains plan-only pending M3.

These capabilities do not grant platform workers independent business authority; workers still compute candidates only.

## CI / Verification Evidence
Windows CI has passed Ruff + pytest for:
- platform lifecycle/recovery;
- durable artifact commit/crash reconciliation;
- logging/diagnostics/scheduler/WorkerManager/dispatch/watchdog;
- JobStore v3 migration and reconstruction;
- IPC codec and real Windows spawn;
- ExecuteTask v2 and worker runtime;
- immutable input staging and validation;
- M2 descriptor/target/executor adapter;
- CandidateResultCoordinator rejection/authority cases;
- component authority E2E;
- real-process successful M2 E2E;
- M2 regression suite including joint border/metadata safety.

Toolchain modernization at commit `b23c9c6a6601bbbd0df0acc73976a723e943bfd0` is verified by Windows CI #320:
- `actions/checkout@v7` PASS;
- `actions/setup-python@v7` PASS;
- Ruff PASS;
- pytest PASS;
- workflow token scope explicitly limited to `contents: read`;
- known Pillow `Image.fromarray(..., mode=...)` deprecation warnings removed from joint cleanup.

## Platform Known Gaps / Remaining Work
1. packaged/frozen Windows executable `spawn` behavior still needs distribution-gate smoke testing;
2. diagnostic bundle can expand with artifact-commit journal/provider inventory;
3. startup reconciliation may be tightened into a store-owned multi-record transaction;
4. persistence schema requires production schema-freeze/migration review;
5. worker start-failure hard-termination/escalation policy can be tightened before RC;
6. release signing/installer/release automation remains a later distribution milestone.

These gaps block production release readiness but do not invalidate the verified source-runtime M2 integration.

## Separation of Responsibilities
- UI is a replaceable presentation shell and never owns critical business rules.
- platform workers execute immutable commands and return candidates; they do not own image QA policy or final artifact authority.
- M2/M3 image algorithms remain in the headless image/domain pipeline.
- shared/final mutations remain MainBoard-owned.
- `REVIEW > destructive guess` remains mandatory.

## Immediate Next Work
1. execute owner-approved Tier-B representative transparent corpus validation on the current PR #11 head;
2. record per-frame evidence without committing private/source bytes;
3. close M2 acceptance only after Tier-B approval;
4. begin M3 opaque-background implementation;
5. later return to production schema freeze, packaged-runtime smoke and release hardening.

## References
- `31_STATE_MACHINE_SPEC.md`
- `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`
- `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`
- `61_WINDOWS_WORKER_PROCESS_AND_IPC_SPEC.md`
- `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md`
- `63_IMMUTABLE_TASK_INPUT_AND_M2_EXECUTOR_MAPPING_SPEC.md`
- `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`
- ADR-017 through ADR-028
- PR #10, PR #11
