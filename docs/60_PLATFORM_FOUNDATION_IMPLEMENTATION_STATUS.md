# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v1.8

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
- SQLite schema version 2 with explicit v1→v2 migration
- durable job/task state independent of worker memory
- task generation, attempt, worker ownership and lease expiry
- CAS job/task transitions and stale-attempt rejection
- append-oriented event journal
- WAL + foreign-key validation
- migration/reopen/stale-write regression tests

#### MainBoard communication foundation
- versioned `MessageEnvelope`
- command/event distinction with correlation/causation identity
- in-process EventBus behind replaceable transport contract
- MainBoard composition root; no sticker/image business algorithms
- composed PathManager, ResourceBroker, JobStore, EventBus, TaskLeaseRegistry, lifecycle/recovery, artifact-commit, LogSink and diagnostic services

#### Task lease / stale-result guard
- authoritative attempt per task
- worker ownership + attempt identity
- configurable lease duration
- renewal/release restricted to authoritative attempt
- newer attempts invalidate old worker results
- runtime guard plus durable JobStore task identity

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
- `ArtifactCommitCoordinator` performs: validate candidate → persist intent → atomic promote → mark promoted → finalize artifact + task success
- task success and commit record finalization occur in the same SQLite transaction
- `ArtifactCommitReconciler` handles crash states idempotently
- intent without final file stays incomplete and never implies success
- matching promoted final file can be finalized after restart
- mismatching final hash becomes `FAILED_INTEGRITY`
- superseded/stale task attempts become `SUPERSEDED` and cannot claim success
- final file existence alone never implies task/job completion

#### Ordered startup recovery
- `StartupRecoveryCoordinator` enforces artifact-commit reconciliation before orphan-task interruption
- valid work promoted immediately before a crash is preserved when authoritative
- remaining active/orphaned work then transitions to INTERRUPTED
- integration tests cover the post-promotion/pre-database-finalization crash boundary

#### Structured observability
- MainBoard-owned `JsonlLogSink` subscribes centrally to EventBus
- workers/UI do not append shared log files directly
- per-job UTF-8 JSONL logs are resolved through PathManager
- log records preserve severity/component/code/job/correlation/frame/stage/task/worker/attempt/provider context
- writes flush and optionally fsync
- integration tests verify central EventBus → LogSink routing and per-job isolation

#### Diagnostic bundle baseline
- `DiagnosticBundleBuilder` produces a job-scoped ZIP in PathManager evidence space
- includes job/task state, durable event history, runtime/environment summary and structured log when available
- optional effective config is recursively redacted for secret/token/password/credential-like fields
- source/private image bytes are excluded by default
- diagnostic output refuses silent overwrite
- generation is read-only with respect to authoritative processing state

#### Bounded scheduler / backpressure foundation
- bounded queued-task capacity and inflight-task capacity
- duplicate task identity rejection
- round-robin fairness across jobs at equal priority
- job-dispatchability callback keeps lifecycle policy outside scheduler
- blocked jobs retain queued tasks without silent loss
- priority support with configurable burst limit to prevent lower-priority starvation
- task completion releases inflight capacity
- durable assignment/attempt/lease authority remains in JobStore/MainBoard, not the scheduler

### Architectural rule
Workers compute only against immutable input/private scratch. Shared/final mutations are MainBoard-owned. Authoritative job/task/artifact state is durable and single-writer. UI issues commands through application services and never mutates workers or persistence directly. Scheduler controls admission/dispatch only. `REVIEW > destructive guess` remains unchanged.

### CI status
- PathManager/ResourceBroker/JobStore/MainBoard/lifecycle/recovery baseline: Ruff + pytest PASS.
- JobStore v2 migration/task persistence: Ruff + pytest PASS.
- durable artifact commit + crash reconciliation fault-injection suite: Ruff + pytest PASS.
- artifact-first startup recovery integration: Ruff + pytest PASS.
- observability/diagnostics/scheduler head requires fresh green Ruff + pytest evidence before this revision is considered verified.

### Known reliability gaps
- `StartupReconciler` still interrupts multiple tasks then the job using separate SQLite transactions. The sequence is idempotent and safe from false success, but a future store-owned recovery transaction can reduce partial-reconciliation states further.
- artifact-commit journal currently has its own explicit schema-version metadata inside the JobStore SQLite database rather than being folded into the global JobStore schema migration number; this is intentional modularity for the current foundation and should be reviewed before production schema freeze.
- diagnostic bundle baseline does not yet enumerate full artifact-commit journal history or provider/dependency inventories beyond available runtime summary.
- scheduler is currently an in-memory policy component; reconstruction from durable JobStore on resume/restart belongs to the WorkerManager/scheduler integration phase.

### Next work packages
1. process WorkerManager lifecycle + heartbeat/watchdog integration
2. connect scheduler dispatch to durable task assignment/lease creation
3. scheduler reconstruction from durable task state after pause/resume/restart
4. expand diagnostic bundle with artifact-commit journal and provider inventory
5. tighten multi-record startup reconciliation transaction where practical
6. production schema freeze/migration review for all persistence tables

## Separation from M2
This platform track is intentionally separate from PR #9 so image-processing verification and control-plane infrastructure can be reviewed independently.

## Verification
Every platform component remains headless-testable. Negative/fault tests cover path ownership, stale writes, duplicate/stale attempts, commit-intent crash boundaries, mismatching artifacts, recovery idempotency, diagnostic redaction/source-image exclusion, queue/inflight bounds and scheduling fairness. No final artifact or file-presence heuristic can bypass durable task/job state.

References: `31_STATE_MACHINE_SPEC.md`, `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`, `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`, `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`, `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`, `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`, ADR-017 through ADR-024.
