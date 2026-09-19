# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v2.4

## Purpose
Track implementation of the approved PathManager/MainBoard/ResourceBroker/multi-worker control-plane architecture separately from M2 image-processing work.

## Current Track
PR #10 / branch `feat/platform-control-foundation`

### Implemented in this track
#### PathManager foundation
- typed `PathRef` / `PathKind`
- centralized job/output/evidence/log/worker-scratch resolution
- typed worker-file references
- workspace isolation, traversal rejection and non-ASCII path tests
- explicit workspace ownership assertion

#### ResourceBroker foundation
- centralized worker-candidate validation and authoritative promotion
- source/target job identity and worker ownership validation
- SHA-256 and byte-size verification
- overwrite refusal for existing authoritative targets
- final artifact re-verification support for crash reconciliation

#### Durable JobStore foundation
- SQLite schema version 3
- explicit migration chain v1→v2→v3
- v2 introduced durable task state, generation, attempt, worker ownership and lease expiry
- v3 introduces durable task descriptors for scheduler reconstruction
- new reconstructable task descriptor records persist priority, descriptor schema version and JSON payload in the same task-creation transaction
- migrated legacy v2 tasks are explicitly marked `reconstructable=false` with descriptor version 0 rather than silently inventing execution meaning
- CAS job/task transitions and stale-attempt rejection
- append-oriented event journal
- WAL + foreign-key validation
- migration/reopen/stale-write/descriptor persistence regression tests

#### MainBoard communication foundation
- versioned `MessageEnvelope`
- command/event distinction with correlation/causation identity
- in-process EventBus behind replaceable transport contract
- MainBoard composition root; no sticker/image business algorithms
- composed PathManager, ResourceBroker, JobStore, EventBus, TaskLeaseRegistry, WorkerManager, WorkerEventRouter, scheduler reconstruction, lifecycle/recovery, artifact-commit, LogSink and diagnostic services

#### Task lease / stale-result guard
- authoritative attempt per task
- worker ownership + attempt identity
- configurable lease duration
- renewal/release restricted to authoritative attempt
- newer attempts invalidate old worker results
- runtime guard plus durable JobStore task identity
- recovery/watchdog may discard the exact matching runtime lease even after expiry without authorizing stale attempts

#### Pause / stop / resume lifecycle
- SSOT state model includes `PAUSING`, `PAUSED`, `STOPPING`, `STOPPED`, `INTERRUPTED`
- `JobLifecycleController` owns control-state policy
- pause/stop finalize only when authoritative RUNNING tasks have reached a safe boundary
- resume allowed only from approved durable states
- invalid transitions rejected before persistence

#### Startup reconciliation
- orphaned PROCESSING/PAUSING/STOPPING jobs reconcile to INTERRUPTED
- orphaned RUNNING tasks reconcile through durable worker/attempt CAS
- durable PAUSED/STOPPED/terminal jobs remain unchanged
- reconciliation is idempotent

#### Durable cross-resource artifact commit protocol
- ADR-024 accepted: filesystem rename + SQLite state cannot be one native ACID transaction, so MTKrita uses durable commit intent
- `ArtifactCommitJournal` persists commit identity in the same JobStore SQLite database under MainBoard single-writer policy
- intent records job/task/worker/attempt/task generation/source/target/hash/size/state
- `ArtifactCommitCoordinator` performs validate → intent → atomic promote → verify → durable finalize
- task success and commit-record finalization occur in the same SQLite transaction
- `ArtifactCommitReconciler` handles crash states idempotently
- missing final artifact never implies success; matching promoted artifact can finalize; hash mismatch becomes integrity failure; stale attempt becomes superseded

#### Ordered startup recovery
- `StartupRecoveryCoordinator` enforces artifact-commit reconciliation before orphan-task interruption
- valid work promoted immediately before a crash is preserved when authoritative
- remaining active/orphaned work then transitions to INTERRUPTED
- integration tests cover the post-promotion/pre-database-finalization crash boundary

#### Structured observability
- MainBoard-owned `JsonlLogSink` subscribes centrally to EventBus
- workers/UI do not append shared log files directly
- per-job UTF-8 JSONL logs are resolved through PathManager
- records preserve severity/component/code/job/correlation/frame/stage/task/worker/attempt/provider context
- writes flush and optionally fsync

#### Diagnostic bundle baseline
- `DiagnosticBundleBuilder` produces a job-scoped ZIP in PathManager evidence space
- includes job/task state, durable event history, runtime/environment summary and structured log when available
- optional effective config is recursively redacted for secret/token/password/credential-like fields
- source/private image bytes are excluded by default
- diagnostic output refuses silent overwrite and is read-only with respect to processing authority

#### Bounded scheduler / backpressure foundation
- bounded queued-task and inflight-task capacity
- duplicate task identity rejection
- round-robin fairness across jobs at equal priority
- lifecycle admission callback remains outside scheduler logic
- blocked jobs retain queued tasks without silent loss
- priority burst limit prevents lower-priority starvation
- durable assignment/attempt/lease authority remains in JobStore/MainBoard

#### Durable scheduler reconstruction
- ADR-025 accepted: in-memory scheduler is disposable and reconstructed from durable task descriptors
- `SchedulerReconstructor` rebuilds only PENDING and eligible INTERRUPTED tasks
- RUNNING/terminal/REVIEW/legacy non-reconstructable tasks are not silently requeued
- durable priority survives restart
- unsupported descriptor version/priority fails before partial enqueue
- queue-capacity overflow is reported as deferred rather than discarded
- stable job/task ordering is used for deterministic rebuild
- reconstruction mutates scheduler memory only, never durable task state
- MainBoard exposes the reconstructor as a control-plane service

#### WorkerManager lifecycle / heartbeat foundation
- interface-first `WorkerHandle` protocol keeps process backend replaceable and fakeable in tests
- worker states STARTING, READY, BUSY, STOPPING, STOPPED, LOST
- task ownership contains task id + attempt identity
- cooperative stop remains behind process-handle contract
- injectable clock enables deterministic heartbeat/loss tests
- dead process or timeout becomes LOST; stale release is rejected
- explicit `mark_stopped` transition accepts only authoritative STOPPING workers

#### Durable dispatch coordination
- `DispatchCoordinator` bridges scheduler policy to durable JobStore assignment, runtime TaskLeaseRegistry and WorkerManager ownership
- new attempt derives from durable task state
- durable lease expiry is persisted before worker execution authority is accepted
- runtime assignment failure compensates the exact authoritative task to INTERRUPTED and releases runtime/inflight ownership
- stale scheduler entries cannot overwrite durable state

#### Worker-loss watchdog reconciliation
- `WorkerLossCoordinator` reconciles WorkerManager LOST state against exact durable task worker/attempt identity
- authoritative lost work becomes INTERRUPTED, never false FAIL/SUCCESS
- matching runtime lease and inflight slot are released
- optional in-memory requeue is safe when capacity exists
- idle worker loss does not mutate unrelated tasks

#### Windows worker process / IPC runtime
- `61_WINDOWS_WORKER_PROCESS_AND_IPC_SPEC.md` defines the Windows spawn/process boundary
- `JsonMessageCodec` uses versioned UTF-8 JSON bytes with explicit size/type/schema/worker-identity validation
- Python pickle/domain-object serialization is not the authoritative IPC contract
- `WindowsSpawnWorkerFactory` uses explicit `multiprocessing` spawn context behind an adapter boundary
- `ProcessWorkerHandle` satisfies the WorkerHandle lifecycle contract without exposing process primitives to MainBoard/domain code
- command and event traffic use separate unidirectional Pipe-style byte channels
- `ProcessWorkerSession` owns both parent-side channel endpoints and supports bounded receive timeout, graceful process wait and deterministic close
- spawned child entrypoint is top-level/importable and has no authoritative JobStore/scheduler/final-output access
- baseline child protocol implements WorkerInitialize → WorkerReady, PingWorker → WorkerHeartbeat and StopWorker → WorkerStopping/WorkerStopped
- ExecuteTask is deliberately rejected with a structured WorkerInternalError until the task-executor contract is approved/implemented
- real Windows CI child-process smoke tests verify spawn, WorkerReady, heartbeat, graceful stop and process exit

#### Validated worker-event routing
- `WorkerEventRouter` validates decoded worker events before any WorkerManager mutation or EventBus publication
- unknown event types, missing worker identity and stale task/attempt identity are rejected before publish
- BUSY heartbeat must carry the authoritative task/attempt; idle heartbeat may not claim task ownership
- TaskStarted/TaskSucceededCandidate/TaskReviewCandidate/TaskFailed require exact BUSY worker ownership
- TaskSucceededCandidate remains only a candidate: routing does not release the worker or mark durable task success
- WorkerStopping/WorkerStopped require authoritative STOPPING lifecycle; WorkerStopped then transitions WorkerManager to STOPPED
- MainBoard composes a single router against the same WorkerManager/EventBus instances used by the rest of the control plane

#### Worker runtime controller
- `WorkerRuntimeController` coordinates factory/session lifecycle without owning durable authority
- start sequence: spawn session → register WorkerHandle → route WorkerReady
- ping includes active task/attempt identity automatically when worker is BUSY
- cooperative stop drains validated WorkerStopping/WorkerStopped events and waits for actual process exit
- runtime session close is allowed only after STOPPED/LOST
- fake-session component tests cover start/ping/BUSY identity/stop/close/duplicate-session behavior separately from real OS process smoke tests

### Architectural rule
Workers compute only against immutable input/private scratch. Shared/final mutations are MainBoard-owned. Authoritative job/task/artifact state is durable and single-writer. UI issues commands through application services and never mutates workers or persistence directly. Scheduler controls admission/dispatch only. WorkerManager owns runtime process/liveness state but does not replace durable JobStore authority. Runtime state must reconcile to durable authority, never the reverse. `REVIEW > destructive guess` remains unchanged.

### CI status
- core platform/lifecycle/recovery baseline: Ruff + pytest PASS
- durable artifact commit + crash reconciliation: Ruff + pytest PASS
- observability/diagnostics/scheduler/WorkerManager/dispatch/watchdog: Ruff + pytest PASS
- JobStore v3 migration + durable scheduler reconstruction + JSON IPC codec: Ruff + pytest PASS
- concrete Windows spawn worker/process-channel smoke test: Ruff + pytest PASS on Windows runner
- WorkerEventRouter/MainBoard wiring/WorkerRuntimeController component suite: Ruff + pytest PASS

### Known reliability gaps
- `StartupReconciler` still interrupts multiple tasks then the job using separate SQLite transactions; behavior is idempotent/safe from false success but can be tightened into a store-owned transaction.
- artifact-commit journal has its own explicit schema-version metadata inside the JobStore database and requires production schema-freeze review.
- diagnostic bundle does not yet enumerate full artifact-commit journal history/provider inventory.
- ExecuteTask has no approved concrete worker task-executor/result payload contract yet; process runtime therefore refuses to pretend execution support exists.
- packaged/frozen Windows executable spawn behavior still requires distribution-stage smoke testing.
- WorkerRuntimeController start-failure cleanup can be tightened further when hard-termination/escalation policy is implemented.

### Next work packages
1. define and implement immutable ExecuteTask command + worker task-executor interface/result-candidate schema
2. connect validated TaskSucceededCandidate/TaskReviewCandidate/TaskFailed handling to durable task/result/artifact-commit services
3. add end-to-end dispatched-task → child process → candidate → authoritative commit integration test
4. expand diagnostic bundle with artifact-commit journal/provider inventory
5. tighten multi-record startup reconciliation transaction where practical
6. production persistence-schema freeze/migration review
7. packaged-runtime spawn smoke test during Windows distribution milestone

## Separation from M2
This platform track remains intentionally separate from PR #9 so image-processing verification and control-plane infrastructure can be reviewed independently.

## Verification
Platform components remain headless-testable. Negative/fault tests cover path ownership, stale writes, task attempts, crash boundaries, artifact integrity, recovery idempotency, diagnostics safety, scheduler bounds/fairness/reconstruction, worker liveness, dispatch compensation, IPC validation, real Windows process spawning, validated event routing and runtime lifecycle orchestration. No file-presence heuristic or runtime-only state may bypass durable authority.

References: `31_STATE_MACHINE_SPEC.md`, `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`, `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`, `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`, `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`, `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`, `61_WINDOWS_WORKER_PROCESS_AND_IPC_SPEC.md`, ADR-017 through ADR-025.
