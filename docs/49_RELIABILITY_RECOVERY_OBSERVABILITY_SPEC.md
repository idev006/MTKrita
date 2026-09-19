# MTKrita Reliability, Recovery and Observability Specification

## Status
SSOT — Reliability Baseline v1.0

## Purpose
กำหนดคุณสมบัติด้านความคงทน ความเชื่อถือได้ ความสามารถในการหยุด/พัก/ทำต่อ การกู้คืน การบันทึก และการวินิจฉัยข้อผิดพลาดของ MTKrita

## 1. Reliability Principles

MTKrita shall be designed to be:
- durable
- recoverable
- observable
- diagnosable
- restartable
- idempotent where practical
- fail-safe rather than silently destructive

## 2. Durable Job State

Job state, task state, accepted artifacts and checkpoints must have a durable representation independent of worker process memory.

For desktop MVP, a local durable store such as SQLite is appropriate, with one logical writer owned by MainBoard.

Critical state transitions should be transactional.

## 3. Crash Consistency

A crash must not create a false COMPLETED state.

Safe commit sequence:

```text
produce provisional output
  ↓
validate
  ↓
hash
  ↓
commit/promote artifact atomically
  ↓
commit durable state transaction
  ↓
publish completion event
```

If the process crashes before durable commit, startup reconciliation treats the work as incomplete.

## 4. Checkpoints

Checkpoint boundaries should be placed after expensive and safely reusable stages, for example:
- source inspected/fingerprinted
- layout accepted
- frames extracted
- border/metadata cleanup accepted
- background removal accepted
- final QA candidate produced
- export committed

A checkpoint records at least:
- job/frame/stage
- input artifact hash
- output artifact hash/reference
- effective config hash
- provider/version
- stage contract version
- completion timestamp

## 5. Pause / Resume

Pause is a first-class state, not process termination disguised as pause.

Requirements:
- stop admission of new work
- current work reaches a safe cooperative boundary when possible
- durable checkpoints/state are flushed
- job transitions to PAUSED
- resume reconstructs scheduler state from durable JobStore
- committed stages are reused when still valid

Config/profile/provider change after pause may invalidate checkpoints according to hash/version rules.

## 6. Stop

Orderly stop:
- stop scheduling new work
- request worker cooperative stop
- collect/validate safe results
- mark interrupted tasks accurately
- persist job state
- terminate worker pool

The system must not label interrupted work as FAIL unless failure semantics apply.

## 7. Application Restart Recovery

Startup recovery flow:

```text
open JobStore
  ↓
validate schema/version
  ↓
find RUNNING/STOPPING tasks from previous process
  ↓
mark old workers LOST
  ↓
reconcile provisional artifacts
  ↓
verify committed artifact hashes
  ↓
restore jobs as INTERRUPTED / PAUSED / READY_TO_RESUME
  ↓
allow controlled resume
```

## 8. Retry Policy

Retries are policy-driven.

Retryable examples:
- worker crash
- transient file lock
- temporary resource shortage

Non-retryable without changed input/config:
- corrupt unsupported input
- deterministic contract violation
- unsafe ambiguity that requires REVIEW

Retry count and backoff are configurable in TOML.

## 9. Structured Logging

Logs must be structured, preferably JSON Lines or equivalent machine-readable events.

Every relevant log/event includes:
- timestamp
- severity
- component
- message/event code
- job_id
- frame_id if relevant
- stage_id if relevant
- task_id
- worker_id
- correlation_id
- attempt
- provider
- measurements/error fields when relevant

Do not rely on unstructured console text as the only operational record.

## 10. Log Architecture

Workers send structured log/events to the central LogSink/EventBus. Workers do not append directly to one shared log file.

This prevents interleaved/corrupted log writes and preserves centralized ordering/correlation metadata.

## 11. Error Model

Use stable error codes/categories, e.g.:

```text
INPUT.INVALID_FILE
INPUT.UNSUPPORTED_MODE
LAYOUT.AMBIGUOUS
BORDER.LOW_CONFIDENCE
METADATA.AMBIGUOUS
BACKGROUND.LOW_CONFIDENCE
RESOURCE.OUT_OF_MEMORY
RESOURCE.DISK_FULL
WORKER.LOST
PROVIDER.FAILURE
EXPORT.ATOMIC_COMMIT_FAILED
CONFIG.INVALID
INTERNAL.CONTRACT_VIOLATION
```

An error descriptor contains:
- code
- human-readable summary
- technical detail
- retryable flag
- affected stage
- causal exception class/message
- optional stack trace reference
- remediation hint where practical

## 12. Diagnostic Bundle

The application should be able to export a diagnostic bundle for a job, containing safe non-secret information such as:
- job manifest
- effective config with sensitive fields redacted
- engine/provider/dependency versions
- structured logs
- state-transition history
- error descriptors
- environment summary
- artifact hashes/metadata
- selected QA previews if policy allows

Original private images should not be included automatically unless the user explicitly chooses to include them.

## 13. Metrics

Minimum operational metrics:
- jobs started/completed/failed/reviewed
- frames processed
- stage duration
- queue wait duration
- worker utilization
- retry count
- worker loss count
- REVIEW rate
- failure rate by code/provider
- background-removal confidence distribution
- export failures

## 14. Event Journal

Important state-changing events should be recorded in an append-oriented audit/event journal or equivalent durable history.

This supports diagnosis of “what happened before failure?” without relying solely on final state.

## 15. Watchdog

MainBoard monitors:
- worker heartbeats
- task lease expiration
- stuck task duration
- queue growth
- disk free space
- optional memory thresholds

Watchdog actions are conservative and logged.

## 16. Resource Exhaustion

Before disk/memory exhaustion causes corruption:
- apply backpressure
- stop scheduling new tasks
- complete/flush safe work
- emit WARNING/ERROR
- transition job to controlled paused/interrupted state if necessary

## 17. Data Integrity

- hash critical source and committed artifacts
- verify before reusing checkpoint
- atomic promotion for final artifacts
- never silently overwrite mismatched artifact identity
- config hash included in provenance

## 18. Version Compatibility

Persisted job/checkpoint/manifest schema has an explicit version.

On startup:
- compatible versions migrate or load
- incompatible versions are not guessed
- migration is logged and tested

## 19. Testing Required

Reliability acceptance suite includes:
- kill worker mid-frame
- kill application mid-write
- resume after restart
- pause/resume with queued and active tasks
- expired lease and late stale result
- disk-full simulation
- corrupted checkpoint/artifact
- duplicate retry attempt
- provider exception
- invalid config
- concurrent 40-frame batch
- diagnostic bundle generation

## 20. Definition of Reliable Completion

A job is complete only when:
- all accepted outputs are durably committed
- output hashes are recorded
- manifest/job state is committed
- no required frame remains RUNNING/PENDING
- REVIEW/FAIL frames are explicitly represented
- diagnostics/evidence are internally consistent

## 21. Related SSOT

- `33_ERROR_RECOVERY_AND_IDEMPOTENCY_SPEC.md`
- `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`
- `31_STATE_MACHINE_SPEC.md`
