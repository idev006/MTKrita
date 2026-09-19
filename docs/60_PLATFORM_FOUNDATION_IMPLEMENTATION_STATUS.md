# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v2.6

## Purpose
Track implementation of the approved PathManager/MainBoard/ResourceBroker/multi-worker control-plane architecture separately from M2 image-processing work.

## Current Track
PR #10 / branch `feat/platform-control-foundation`

## Implemented and Verified Foundation

### Durable authority and resources
- typed `PathRef` / centralized `PathManager` with workspace ownership and worker-private scratch;
- typed immutable job `INPUT` namespace under `jobs/<job_id>/inputs/`;
- `ResourceBroker.stage_input_file()` copies external/control-plane source bytes into job input space without mutating the original source;
- staged input uses overwrite refusal, flush/fsync, SHA-256, byte-size evidence and atomic promotion;
- `ResourceBroker.verify_input_file()` verifies staged immutable input before dispatch;
- `ResourceBroker` validates worker candidates, SHA-256 and authoritative promotion;
- SQLite `JobStore` schema v3 with explicit v1→v2→v3 migration;
- durable job/task state, generation, attempts, worker identity, leases, CAS stale-write protection and event journal;
- durable task descriptors persist priority, descriptor version and JSON payload;
- legacy v2 tasks remain explicitly non-reconstructable rather than receiving guessed descriptors.

### Lifecycle, recovery and artifact commitment
- `JobLifecycleController` implements pause/stop/resume safe-boundary policy;
- idempotent startup reconciliation handles orphaned jobs/tasks;
- ADR-024 durable artifact commit intent bridges filesystem promotion and JobStore finalization;
- artifact-first startup recovery preserves valid promoted artifacts before generic interruption;
- stale/superseded attempts and hash/integrity failures cannot claim success.

### MainBoard, observability and diagnostics
- versioned `MessageEnvelope` and replaceable in-process EventBus;
- MainBoard composition root contains no sticker/image business algorithms;
- centralized `JsonlLogSink` records validated EventBus messages with correlation/task/worker context;
- `DiagnosticBundleBuilder` emits job-scoped diagnostics with secret redaction and excludes source/private image bytes by default.

### Scheduler / worker control plane
- bounded fair scheduler with queue/inflight limits, per-job fairness and priority anti-starvation;
- `DispatchCoordinator` bridges scheduler → durable assignment/lease → runtime lease → WorkerManager with compensation on assignment failure;
- `WorkerLossCoordinator` interrupts exact LOST attempts, releases runtime ownership and optionally requeues;
- ADR-025 durable scheduler reconstruction restores only eligible PENDING/INTERRUPTED tasks from durable descriptors;
- RUNNING, terminal, REVIEW and legacy non-reconstructable work is never silently requeued.

### Windows worker runtime / IPC
- explicit Windows `spawn` process adapter behind `WorkerProcessFactory` / `WorkerHandle` contracts;
- separate unidirectional command/event channels;
- versioned UTF-8 JSON wire schema with size/type/schema/identity validation; no authoritative pickle/domain-object IPC;
- `ProcessWorkerSession` owns channel endpoints and bounded receive/wait/close lifecycle;
- `WorkerEventRouter` validates worker/task/attempt identity before WorkerManager mutation and EventBus publish;
- `WorkerRuntimeController` manages start/pump/ping/cooperative stop/process exit/session close without owning durable authority;
- real Windows CI verifies spawn → WorkerReady → heartbeat → graceful stop → process exit.

### ExecuteTask / immutable input / result candidate authority
- ADR-026 accepted: ExecuteTask is immutable and worker results are candidates;
- `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md` is the detailed task/result authority SSOT;
- `63_IMMUTABLE_TASK_INPUT_AND_M2_EXECUTOR_MAPPING_SPEC.md` defines staged immutable input and M2 mapping;
- ExecuteTask payload version 2 carries explicit verified immutable `inputs[]` plus worker-private scratch;
- durable descriptors carry logical input identity/hash rather than arbitrary external absolute paths;
- `ExecuteTaskCommandBuilder` reconstructs staged input through `PathManager.input()` and verifies hash before command creation;
- generic no-input tasks remain valid with `inputs=[]`;
- worker command carries no authoritative final-output target;
- `TaskExecutor` is a replaceable interface boundary;
- provisional artifacts are limited to safe scratch filename + SHA-256 + byte size evidence;
- candidate result payloads are versioned and strictly parsed;
- baseline real child process validates ExecuteTask and emits `TaskStarted → TaskFailed(WORKER.EXECUTOR_NOT_CONFIGURED)` until a concrete production image executor is connected, preventing false success.

### M2 production descriptor and executor boundary
- strict `M2FrameTaskDescriptor` schema version 1 is implemented;
- descriptor rejects unknown critical fields, path-like `input_name`/`output_name`, invalid SHA-256, bad extraction geometry, invalid confidence/threshold values and invalid `.png` output identity;
- production M2 descriptor includes frame index/row/column, extraction provenance and immutable pipeline configuration snapshot;
- `M2FrameTargetResolver` validates durable descriptor identity and resolves final output only through `PathManager.output()`;
- `M2FrameTaskExecutor` adapts the headless M2 pipeline behind injected processor/config/writer seams without duplicating M2 algorithms in platform code;
- worker independently verifies staged input file existence/hash/size before image processing;
- PASS/AUTO_FIXED maps to one provisional scratch PNG success candidate;
- REVIEW produces no final/provisional success artifact;
- FAIL maps to structured failure using pipeline finding identity;
- executor serializes frame findings/actions/evidence into JSON-compatible candidate evidence;
- source/staged input is never mutated by the executor.

### Durable candidate result coordination
- `CandidateResultCoordinator` accepts candidate events only for the exact durable RUNNING job/task/worker/attempt;
- WorkerManager must be BUSY on the same task/attempt and the runtime lease must still be authoritative;
- MVP successful candidate requires exactly one primary provisional artifact;
- worker cannot select final output destination;
- MainBoard-side `CandidateTargetResolver` resolves the final PathRef from trusted durable/domain context;
- ResourceBroker verifies provisional file existence, SHA-256 and byte size before commit;
- final target must be same-job OUTPUT or EVIDENCE and non-worker-owned;
- success flows through the existing ADR-024 `ArtifactCommitCoordinator`; durable task reaches SUCCEEDED only after commit finalization;
- REVIEW/FAILED use exact JobStore task transition before runtime ownership is released;
- accepted terminal/review outcome releases TaskLeaseRegistry, WorkerManager BUSY ownership and scheduler inflight ownership;
- malformed/stale/wrong-worker/hash-mismatch/size-mismatch/cross-job/zero-artifact/multi-artifact candidates cannot produce durable success.

## CI / Verification Evidence

Current code checkpoints on Windows CI have Ruff PASS + pytest PASS for:
- core platform/lifecycle/recovery;
- durable artifact commit and crash reconciliation;
- observability/diagnostics/scheduler/WorkerManager/dispatch/watchdog;
- JobStore v3 migration and scheduler reconstruction;
- JSON IPC codec and real Windows spawn runtime;
- WorkerEventRouter and WorkerRuntimeController;
- ExecuteTask v2/result schemas and real child-process ExecuteTask failure-safe smoke;
- immutable input staging, source-preservation, overwrite refusal and staged hash/size verification;
- strict M2 descriptor parsing and MainBoard-owned target resolution;
- M2 executor adapter PASS/AUTO_FIXED/REVIEW/FAIL mapping and tampered-input rejection;
- CandidateResultCoordinator authority/rejection cases;
- component end-to-end authority chain:
  scheduler dispatch → durable RUNNING/lease → ExecuteTask builder → test TaskExecutor private scratch → validated TaskStarted/candidate → CandidateResultCoordinator → ADR-024 commit → durable SUCCEEDED → runtime ownership release.

The component E2E uses a test-only executor and does not add a production fake-success mode. PR #9 remains the source of the actual M2 image-processing algorithms.

## Architectural Rules

Workers compute only against immutable approved inputs/private scratch. Shared/final mutations are MainBoard-owned. JobStore remains durable authority. Scheduler runtime memory is disposable. Worker/process state reconciles to durable authority, never the reverse. Candidate events are evidence, not completion. `REVIEW > destructive guess` remains unchanged.

## Known Gaps / Remaining Platform Work

1. The platform now has the M2 executor adapter contract, but PR #9 algorithm implementations are not yet wired into a production child-process bootstrap.
2. Real-process successful M2 image execution awaits a controlled integration branch that combines PR #9 algorithms with the verified PR #10 platform boundary.
3. Packaged/frozen Windows executable spawn behavior requires distribution-stage smoke testing.
4. Diagnostic bundle should expand with artifact-commit journal and provider inventory.
5. Startup reconciliation can be tightened into a store-owned multi-record transaction.
6. Artifact-commit and JobStore persistence schemas require production schema-freeze/migration review.
7. WorkerRuntimeController start-failure hard-termination/escalation policy can be tightened before release candidate.

## Next Work Packages

1. create a stacked M2/platform integration branch from this verified platform head;
2. wire PR #9 `process_frame` + `FramePipelineConfig` + `export_png_atomic` into `M2FrameTaskExecutor` through injected seams, without copying image policy into the platform layer;
3. add real-process successful M2 task integration: staged transparent frame → child executor → candidate → CandidateResultCoordinator → ADR-024 output commit;
4. verify source/staged input immutability and final LINE asset properties in the integrated path;
5. expand diagnostics and tighten startup recovery transaction;
6. perform persistence schema-freeze review;
7. add packaged-runtime spawn smoke during Windows distribution milestone.

## Separation from M2

This platform track remains intentionally separate from PR #9 so image-processing verification and control-plane infrastructure can be reviewed independently. Platform code defines the safe executor boundary and M2 descriptor/adapter contract; it does not reimplement or silently alter M2 image-processing decisions.

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
- ADR-017 through ADR-026
