# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v3.0

## Purpose
Track implementation of the PathManager/MainBoard/ResourceBroker/multi-worker/control-plane architecture separately from image-algorithm maturity while reflecting the verified integration maintained on PR #11.

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
- strict `M2FrameTaskDescriptor` schema;
- MainBoard-owned `M2FrameTargetResolver`;
- `M2FrameTaskExecutor` adapting the headless image pipeline behind injected seams;
- static built-in `m2.frame` registration; task payload cannot choose module/callable/import path;
- staged-input integrity verification inside worker execution;
- PASS/AUTO_FIXED → exactly one provisional scratch PNG candidate;
- REVIEW → no false success artifact;
- FAIL → structured task failure;
- source and staged input remain immutable;
- real Windows spawned-child E2E verifies staged input → durable dispatch/lease → ExecuteTask → child M2 pipeline → candidate → MainBoard validation → ResourceBroker/ADR-024 commit → durable SUCCEEDED → final PNG.

Final output is not published merely because a worker produced a candidate; final publication remains MainBoard authority.

## Current Image-Pipeline Hardening Boundary
PR #11 contains verified Tier-B-oriented safety mechanisms while keeping policy in the image/domain layer:
- inset/rounded border discovery after transparent padding;
- visible-support vs visible-color-purity evidence;
- conservative four-side multi-tone fallback without widened global tolerance;
- explicit frame evidence for border consensus mode;
- localized border contact ranges;
- alpha-visible metadata topology for transparent inputs;
- post-exclusion local metadata ownership and remote-artwork preservation;
- exact exclusion-mask identity binding;
- enclosed-visible-hole completion;
- `JointCleanupPlanner` SAFE_PLAN/REVIEW contract;
- bounded transparent-gutter separator refinement around configured grid predictions;
- transparent-source joint cleanup only for SAFE_PLAN;
- opaque-source cleanup remains plan-only pending M3.

These capabilities do not grant platform workers independent business authority; workers still compute candidates only.

## CI / Verification Evidence
Windows CI has passed Ruff + pytest for platform and M2 integration including:
- lifecycle/recovery and durable artifact commit/crash reconciliation;
- logging/diagnostics/scheduler/WorkerManager/dispatch/watchdog;
- JobStore v3 migration/reconstruction;
- IPC codec and real Windows spawn;
- ExecuteTask v2 and worker runtime;
- immutable input staging;
- M2 descriptor/target/executor adapter;
- CandidateResultCoordinator authority/rejection cases;
- real-process successful M2 E2E;
- joint border/metadata safety;
- TB-001/TB-002 evidence and ownership refinements;
- TB-003 transparent metadata topology;
- TB-004 bounded separator refinement;
- TB-005 conservative multi-tone four-side fallback and explicit consensus-mode evidence.

Recent checkpoints:
- CI #324 — TB-002 PASS;
- CI #328/#329 — TB-003 behavior/evidence PASS;
- CI #330 — TB-004 PASS;
- CI #333 — initial TB-005 PASS;
- CI #340 at `55749b2f378dcd703f6e2baa907eaae144efb093` — completed TB-005 regression/evidence contract PASS (Ruff + pytest).

CI #340 includes explicit synthetic coverage for four-side success, three-side refusal, insufficient-side-support refusal, preserved contact risk, unchanged single-tone mode, deterministic repeat and frame evidence propagation. No automatic threshold or global color tolerance was relaxed.

Toolchain remains current:
- `actions/checkout@v7`;
- `actions/setup-python@v7`;
- workflow token scope `contents: read`;
- known Pillow joint-cleanup deprecation warning removed.

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
1. make the owner-held Candidate A/B bytes available read-only and verify their recorded SHA-256 values;
2. execute the final integrated Tier-B Candidate A/B run on the current PR #11 head using refined extraction;
3. record per-frame extraction, border consensus mode, metadata, joint-plan and output-inspection evidence without committing private/source bytes;
4. close M2 acceptance only after Tier-B approval;
5. begin M3 opaque-background implementation;
6. later return to production schema freeze, packaged-runtime smoke and release hardening.

Synthetic CI, historical diagnostics or hash-only records do not substitute for the final hash-matched representative corpus run.

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
- `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`
- `66_TIER_B_METADATA_AND_EXTRACTION_REFINEMENT_SPEC.md`
- `67_MULTITONE_BORDER_CONSENSUS_SPEC.md`
- ADR-017 through ADR-028
- PR #10, PR #11
