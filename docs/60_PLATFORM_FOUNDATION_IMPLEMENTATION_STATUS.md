# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v1.5

## Purpose
Track implementation of the approved PathManager/MainBoard/ResourceBroker/multi-worker control-plane architecture separately from M2 image-processing work.

## Current Track
PR #10 / branch `feat/platform-control-foundation`

### Implemented in this track
#### PathManager foundation
- typed `PathRef` / `PathKind`
- centralized `PathManager`
- deterministic job-root/output/evidence/log/worker-scratch resolution
- typed worker-file references
- job/workspace isolation
- unsafe job-id / filename / traversal rejection
- non-ASCII path coverage through automated tests
- explicit workspace ownership assertion

#### ResourceBroker foundation
- centralized promotion from worker scratch to authoritative output/evidence
- source/target job-identity validation
- worker ownership evidence
- SHA-256 verification before commit
- authoritative target overwrite refusal
- move/promotion only after validation
- automated tests for success, cross-job rejection, hash mismatch and existing-target protection

#### Durable JobStore foundation
- SQLite schema version 2
- explicit migration path from schema v1 to v2
- durable job state independent of worker memory
- durable task state independent of worker memory
- task generation, attempt, worker ownership and lease-expiry fields
- source/config hash fields
- monotonic generation counters
- compare-and-set job transitions using expected state + expected generation
- compare-and-set task assignment/renewal/completion using generation + worker + attempt identity
- stale worker/attempt result rejection at durable-store boundary
- transaction rollback on stale/invalid transitions
- append-oriented event journal with structured detail payload
- WAL mode and foreign-key validation
- persistence/reopen, migration, stale-transition and stale-attempt regression tests

#### MainBoard communication foundation
- versioned `MessageEnvelope`
- explicit command/event kind
- message/correlation/causation identity
- optional frame/stage/task/worker/attempt context
- replaceable synchronous in-process EventBus for local MVP
- typed and global subscriptions with unsubscribe support
- `MainBoard` composition root containing PathManager, ResourceBroker, JobStore, EventBus and TaskLeaseRegistry
- no sticker/image business algorithms inside MainBoard
- automated message routing/composition tests

#### Task lease / stale-result guard
- authoritative task attempt per `task_id`
- worker ownership + attempt identity
- configurable lease duration
- renew/release only by authoritative worker/attempt
- newer attempt invalidates older worker result
- expired attempt rejected and enumerable for watchdog/requeue policy
- injectable clock for deterministic automated testing
- durable equivalent of assignment/lease/attempt state now stored in JobStore v2

The in-memory `TaskLeaseRegistry` remains useful as a fast runtime guard, but durable JobStore state is authoritative across restart/recovery boundaries.

### Architectural rule
Workers produce candidate artifacts only in private scratch. Shared/final artifacts are committed through MainBoard-owned ResourceBroker services using PathManager-resolved references. Authoritative job/task state is persisted through a single-logical-writer JobStore; workers never write JobStore directly. Cross-component communication uses the versioned message envelope. Worker results are accepted only when lease/attempt identity is current in both runtime guard and durable state.

### CI status
PR #10 previously passed Ruff + pytest before JobStore v2 changes. The v2 migration/task-persistence head requires fresh green Ruff + pytest evidence before this phase is considered verified.

### Next work packages
1. startup reconciliation for persisted RUNNING tasks / lost workers
2. pause/stop/resume state integration
3. structured event/log sink and diagnostics
4. ResourceBroker ↔ JobStore coordinated commit transaction pattern
5. bounded scheduler/backpressure foundation
6. process WorkerManager lifecycle/heartbeat integration

## Separation from M2
This platform track is intentionally separate from PR #9 so image-processing verification and control-plane infrastructure can be reviewed independently.

## Verification
Every platform component must be headless-testable. Filesystem/resource dependencies require isolated temporary-workspace tests and fault cases. Shared-resource mutation must have explicit negative tests for ownership, stale/duplicate writes and overwrite behavior. State-store tests must prove stale writes do not mutate authoritative state or journal history. Message tests must preserve correlation/attempt identity independently of transport. Lease tests must prove old/expired attempts cannot become authoritative again. Schema migration tests must prove prior durable job state survives compatible upgrades.

References: `31_STATE_MACHINE_SPEC.md`, `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`, `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`, `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`, `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`, `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`, ADR-017 through ADR-020.
