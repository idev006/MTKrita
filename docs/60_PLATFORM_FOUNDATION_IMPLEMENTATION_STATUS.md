# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v1.7

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
- composed PathManager, ResourceBroker, JobStore, EventBus, TaskLeaseRegistry, lifecycle/recovery and artifact-commit services

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
- this preserves valid work when a crash occurs after filesystem promotion but before database finalization
- remaining active/orphaned work is then transitioned to INTERRUPTED
- integration test simulates this crash boundary and verifies the promoted artifact is retained as committed task success while the job remains recoverable

### Architectural rule
Workers compute only against immutable input/private scratch. Shared/final mutations are MainBoard-owned. Authoritative job/task/artifact state is durable and single-writer. UI issues commands through application services and never mutates workers or persistence directly. `REVIEW > destructive guess` remains unchanged.

### CI status
- PathManager/ResourceBroker/JobStore/MainBoard/lifecycle/recovery baseline: Ruff + pytest PASS.
- JobStore v2 migration/task persistence: Ruff + pytest PASS.
- durable artifact commit + crash reconciliation fault-injection suite: Ruff + pytest PASS.
- artifact-first startup recovery integration: Ruff + pytest PASS.

### Known reliability gaps
- `StartupReconciler` still interrupts multiple tasks then the job using separate SQLite transactions. The sequence is idempotent and safe from false success, but a future store-owned recovery transaction can reduce partial-reconciliation states further.
- artifact-commit journal currently has its own explicit schema-version metadata inside the JobStore SQLite database rather than being folded into the global JobStore schema migration number; this is intentional modularity for the current foundation and should be reviewed before production schema freeze.

### Next work packages
1. centralized structured JSONL LogSink + diagnostic bundle baseline
2. bounded scheduler/backpressure foundation
3. process WorkerManager lifecycle/heartbeat integration
4. tighten multi-record startup reconciliation transaction where practical
5. production schema freeze/migration review for all persistence tables

## Separation from M2
This platform track is intentionally separate from PR #9 so image-processing verification and control-plane infrastructure can be reviewed independently.

## Verification
Every platform component remains headless-testable. Negative/fault tests cover path ownership, stale writes, duplicate/stale attempts, commit-intent crash boundaries, mismatching artifacts and recovery idempotency. No final artifact or file-presence heuristic can bypass durable task/job state.

References: `31_STATE_MACHINE_SPEC.md`, `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`, `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`, `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`, `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`, `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`, ADR-017 through ADR-024.
