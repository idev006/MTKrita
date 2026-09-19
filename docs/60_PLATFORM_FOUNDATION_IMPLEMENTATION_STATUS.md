# MTKrita Platform Foundation Implementation Status

## Status
SSOT — Platform Foundation Implementation Track v1.0

## Purpose
Track implementation of the approved PathManager/MainBoard/ResourceBroker/multi-worker control-plane architecture separately from M2 image-processing work.

## Current Track
Branch: `feat/platform-control-foundation`

### Implemented in this track
- typed `PathRef`
- `PathKind`
- centralized `PathManager`
- deterministic job-root/output/evidence/log/worker-scratch resolution
- job/workspace isolation
- unsafe job-id / filename / traversal rejection
- non-ASCII Windows-compatible path coverage through automated tests
- explicit workspace ownership assertion

### Architectural rule
Application modules and workers must not invent shared runtime paths. Shared/job-owned locations are resolved through PathManager or future compatible typed resource references.

### Next work packages
1. ResourceBroker interface and atomic artifact promotion ownership
2. durable JobStore interface + SQLite implementation
3. MainBoard composition root
4. Event/command envelope + correlation identifiers
5. WorkerManager lease/attempt protocol
6. pause/stop/resume/reconciliation state integration

## Separation from M2
This platform track is intentionally separate from PR #9 so image-processing verification and control-plane infrastructure can be reviewed independently.

## Verification
Every platform component must be headless-testable. Filesystem/resource dependencies require isolated temporary-workspace tests and fault cases.

References: `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`, `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`, `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`, `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`, `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`, ADR-017 through ADR-020.
