# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v2.3

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
- composed PathManager, ResourceBroker, JobStore, EventBus, TaskLeaseRegistry, WorkerManager, scheduler reconstruction, lifecycle/recovery, artifact-commit, LogSink and diagnostic services

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

#### Windows worker/IPC contract foundation
- `61_WINDOWS_WORKER_PROCESS_AND_IPC_SPEC.md` defines Windows spawn/process boundary
- worker process remains computation-only; MainBoard retains all authority
- Python pickle/domain-object serialization is not the authoritative IPC contract
- `JsonMessageCodec` uses versioned UTF-8 JSON bytes with explicit size/type/schema validation
- worker identity can be validated at decode boundary
- malformed JSON/types, unsupported schema and oversized messages are rejected before publish
- `JsonMessageSender` / `JsonMessageReceiver` abstract byte channels so real multiprocessing transport is replaceable/testable
- automated tests cover round trip, UTF-8 data, identity mismatch, invalid types, non-JSON payload and size limits
- concrete Windows spawn process adapter is intentionally the next phase, not hidden inside the codec

### Architectural rule
Workers compute only against immutable input/private scratch. Shared/final mutations are MainBoard-owned. Authoritative job/task/artifact state is durable and single-writer. UI issues commands through application services and never mutates workers or persistence directly. Scheduler controls admission/dispatch only. WorkerManager owns runtime process/liveness state but does not replace durable JobStore authority. Runtime state must reconcile to durable authority, never the reverse. `REVIEW > destructive guess` remains unchanged.

### CI status
- core platform/lifecycle/recovery baseline: Ruff + pytest PASS
- durable artifact commit + crash reconciliation: Ruff + pytest PASS
- observability/diagnostics/scheduler/WorkerManager/dispatch/watchdog: Ruff + pytest PASS
- JobStore v3 migration + durable scheduler reconstruction + JSON IPC codec: Ruff + pytest PASS

### Known reliability gaps
- `StartupReconciler` still interrupts multiple tasks then the job using separate SQLite transactions; behavior is idempotent/safe from false success but can be tightened into a store-owned transaction.
- artifact-commit journal has its own explicit schema-version metadata inside the JobStore database and requires production schema-freeze review.
- diagnostic bundle does not yet enumerate full artifact-commit journal history/provider inventory.
- concrete Windows spawn worker process + command/event transport is not yet implemented.
- reconstructed scheduler descriptors currently restore admission identity/priority; concrete worker execution will validate the full descriptor contract when process transport is connected.

### Next work packages
1. concrete Windows spawn process-worker adapter and command/event channel
2. connect validated worker heartbeat/result events into EventBus/WorkerManager and task-result handling
3. real Windows child-process CI smoke test
4. expand diagnostic bundle with artifact-commit journal/provider inventory
5. tighten multi-record startup reconciliation transaction where practical
6. production persistence-schema freeze/migration review

## Separation from M2
This platform track remains intentionally separate from PR #9 so image-processing verification and control-plane infrastructure can be reviewed independently.

## Verification
Platform components remain headless-testable. Negative/fault tests cover path ownership, stale writes, task attempts, crash boundaries, artifact integrity, recovery idempotency, diagnostics safety, scheduler bounds/fairness/reconstruction, worker liveness, dispatch compensation and IPC validation. No file-presence heuristic or runtime-only state may bypass durable authority.

References: `31_STATE_MACHINE_SPEC.md`, `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`, `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`, `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`, `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`, `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`, `61_WINDOWS_WORKER_PROCESS_AND_IPC_SPEC.md`, ADR-017 through ADR-025.
