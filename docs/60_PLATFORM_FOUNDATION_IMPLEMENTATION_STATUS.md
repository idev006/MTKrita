# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v2.5

## Purpose
Track implementation of the approved PathManager/MainBoard/ResourceBroker/multi-worker control-plane architecture separately from M2 image-processing work.

## Current Track
PR #10 / branch `feat/platform-control-foundation`

## Implemented and Verified Foundation

### Durable authority and resources
- typed `PathRef` / centralized `PathManager` with workspace ownership and worker-private scratch;
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

### ExecuteTask / result candidate authority
- ADR-026 accepted: ExecuteTask is immutable and worker results are candidates;
- `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md` is the detailed SSOT for task/result authority;
- `ExecuteTaskCommandBuilder` builds commands only from authoritative RUNNING task state + durable descriptor + PathManager worker scratch;
- ExecuteTask payload has an explicit schema and carries no authoritative final-output target;
- `TaskExecutor` is a replaceable interface boundary;
- provisional artifacts are limited to safe scratch filename + SHA-256 + byte size evidence;
- candidate result payloads are versioned and strictly parsed;
- baseline real child process validates ExecuteTask and emits `TaskStarted → TaskFailed(WORKER.EXECUTOR_NOT_CONFIGURED)` until a concrete production image executor is connected, preventing false success.

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
- ExecuteTask/result schemas and real child-process ExecuteTask failure-safe smoke;
- CandidateResultCoordinator authority/rejection cases;
- component end-to-end authority chain:
  scheduler dispatch → durable RUNNING/lease → ExecuteTask builder → test TaskExecutor private scratch → validated TaskStarted/candidate → CandidateResultCoordinator → ADR-024 commit → durable SUCCEEDED → runtime ownership release.

The component E2E uses a test-only executor and does not add a production fake-success mode.

## Architectural Rules

Workers compute only against immutable approved inputs/private scratch. Shared/final mutations are MainBoard-owned. JobStore remains durable authority. Scheduler runtime memory is disposable. Worker/process state reconciles to durable authority, never the reverse. Candidate events are evidence, not completion. `REVIEW > destructive guess` remains unchanged.

## Known Gaps / Remaining Platform Work

1. A concrete production image-processing `TaskExecutor` is not yet connected; this belongs to integration with M2 image-processing contracts rather than being faked in platform runtime.
2. Production task-descriptor fields consumed by the image executor must be formalized without arbitrary path/callable semantics.
3. Real-process success E2E awaits the concrete image executor; current real-process ExecuteTask path is deliberately failure-safe.
4. Packaged/frozen Windows executable spawn behavior requires distribution-stage smoke testing.
5. Diagnostic bundle should expand with artifact-commit journal and provider inventory.
6. Startup reconciliation can be tightened into a store-owned multi-record transaction.
7. Artifact-commit and JobStore persistence schemas require production schema-freeze/migration review.
8. WorkerRuntimeController start-failure hard-termination/escalation policy can be tightened before release candidate.

## Next Work Packages

1. hand the verified `TaskExecutor` / ExecuteTask / candidate-result boundary to M2 image-processing integration;
2. define production task descriptor mapping from frame/pipeline contracts into the worker executor;
3. add real-process success integration once M2 executor is available;
4. expand diagnostics and tighten startup recovery transaction;
5. perform persistence schema-freeze review;
6. add packaged-runtime spawn smoke during Windows distribution milestone.

## Separation from M2

This platform track remains intentionally separate from PR #9 so image-processing verification and control-plane infrastructure can be reviewed independently. Platform code defines the safe executor boundary; it does not reimplement or silently alter M2 image-processing decisions.

## References

- `31_STATE_MACHINE_SPEC.md`
- `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`
- `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`
- `61_WINDOWS_WORKER_PROCESS_AND_IPC_SPEC.md`
- `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md`
- ADR-017 through ADR-026
