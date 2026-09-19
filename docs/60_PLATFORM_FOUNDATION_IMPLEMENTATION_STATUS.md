# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v1.2

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
- non-ASCII Windows-compatible path coverage through automated tests
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
- SQLite schema version 1
- durable job state independent of worker memory
- source/config hash fields
- monotonic generation counter
- compare-and-set state transitions using expected state + expected generation
- transaction rollback on stale/invalid transitions
- append-oriented event journal with structured detail payload
- WAL mode and foreign-key validation
- persistence/reopen tests and stale-transition regression tests

### Architectural rule
Workers produce candidate artifacts only in private scratch. Shared/final artifacts are committed through MainBoard-owned ResourceBroker services using PathManager-resolved references. Authoritative job state is persisted through a single-logical-writer JobStore; workers never write JobStore directly.

### CI status
Initial PR #10 CI found only a Ruff import-order issue in PathManager. That issue was corrected. Current ResourceBroker/JobStore head requires fresh green Ruff + pytest evidence before this phase is considered verified.

### Next work packages
1. MainBoard composition root
2. Event/command envelope + correlation identifiers
3. WorkerManager lease/attempt protocol
4. pause/stop/resume/reconciliation state integration
5. structured event/log sink and diagnostics
6. ResourceBroker ↔ JobStore coordinated commit transaction pattern

## Separation from M2
This platform track is intentionally separate from PR #9 so image-processing verification and control-plane infrastructure can be reviewed independently.

## Verification
Every platform component must be headless-testable. Filesystem/resource dependencies require isolated temporary-workspace tests and fault cases. Shared-resource mutation must have explicit negative tests for ownership, stale/duplicate writes and overwrite behavior. State-store tests must prove stale writes do not mutate authoritative state or journal history.

References: `31_STATE_MACHINE_SPEC.md`, `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`, `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`, `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`, `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`, `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`, ADR-017 through ADR-020.
