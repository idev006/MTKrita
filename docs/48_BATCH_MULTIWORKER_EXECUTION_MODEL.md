# MTKrita Batch and Multi-Worker Execution Model

## Status
SSOT — Execution Architecture Baseline v1.2

## Purpose
กำหนดวิธีประมวลผลแบบ batch และ parallel multi-worker ให้มี throughput สูงโดยไม่แลกกับความถูกต้อง ความสามารถในการ recover หรือความปลอดภัยของ shared resources

## 1. Execution Principle

> Parallelize computation; serialize shared-state commitment.

งานคำนวณของ frame สามารถทำพร้อมกันหลาย worker ได้ แต่การ commit shared state/final artifacts ต้องผ่าน MainBoard-owned services

## 2. Unit of Parallelism

MVP ใช้ **frame task** เป็นหน่วยหลักของ parallelism หลังจาก sheet-level stages ที่ต้องทำก่อน เช่น file inspection และ layout detection/frame extraction

Typical flow:

```text
Sheet Job
  ↓
Inspect + Detect Layout + Split
  ↓
FrameTask[01] ─┐
FrameTask[02] ─┤
FrameTask[03] ─┤ → Worker Pool
...            │
FrameTask[10] ─┘
  ↓
central commit / QA aggregation / export manifest
```

สำหรับ 4 sheets / 40 stickers สามารถ schedule frame tasks ข้าม sheet ได้เมื่อ dependency พร้อม

## 3. Worker Model

Prefer process workers on Windows for isolation and CPU-bound/image-provider compatibility.

Worker properties:
- isolated process
- immutable task descriptor
- private scratch space
- provider registry initialized per process
- no direct access to shared mutable job state
- structured result returned to MainBoard
- heartbeat and attempt identity

## 4. Task Descriptor

A task should contain only the information needed to execute safely:

```text
task_id
job_id
frame_id
stage_plan
input ArtifactRef(s)
EffectiveConfig snapshot/hash
provider selection
attempt
lease deadline
private scratch allocation
correlation_id
```

No arbitrary shared path or mutable global object is passed to a worker.

The control plane must also persist the scheduling/execution meaning required to reconstruct a task after restart. See ADR-025.

## 5. Task Result

Worker returns:

```text
task_id
attempt
worker_id
status
stage results
findings
actions
measurements
produced artifact descriptors/hashes
error descriptor if any
processing timings
```

MainBoard validates the result before any durable commit.

## 6. Worker Count

Worker count must be configurable through TOML and may be AUTO-derived from:
- logical CPU count
- memory budget
- provider characteristics
- image size
- optional GPU/scarce-resource slots

More workers is not automatically better. The scheduler must enforce resource budgets and avoid memory/disk thrashing.

Example:

```toml
[execution]
mode = "parallel"
workers = 4
max_inflight_tasks = 8
worker_heartbeat_seconds = 5
task_lease_seconds = 120
```

## 7. Shared Resource Isolation

Workers shall not directly mutate:
- final export directory
- manifest/database
- global log sink
- shared job state
- another worker's scratch directory

Workers may produce provisional artifacts only in private scratch allocated by the control plane.

## 8. Resource Broker Commit

```text
Worker completes task
  ↓
returns Result + ArtifactDescriptor
  ↓
MainBoard validates attempt/lease/result schema
  ↓
ResourceBroker validates hash/file/type
  ↓
atomic promote to artifact/final namespace
  ↓
JobStore transaction records commit
  ↓
publish TaskCommitted event
```

Late results from an expired/superseded attempt must not overwrite the accepted result.

## 9. Leases and Attempts

Each scheduled task has:
- `attempt` number
- worker ownership
- lease expiry

If a worker disappears, the lease expires and the task may be rescheduled. A result from an old attempt is rejected once a newer attempt is authoritative.

This prevents duplicate workers from racing to commit the same frame.

## 10. Pause Semantics

`PAUSE` means:
1. stop scheduling new tasks
2. allow configurable policy for current tasks: finish safe stage or cooperatively checkpoint
3. commit completed safe work
4. enter durable `PAUSED` state

Resume uses existing committed artifacts/checkpoints; it must not start from source unnecessarily.

## 11. Stop / Cancel Semantics

Distinguish:
- **Pause** — resumable
- **Stop** — orderly termination, resumability depends on policy
- **Cancel** — user declares job no longer needed; preserve diagnostic/history according to retention rules
- **Kill worker** — infrastructure action; task becomes interrupted, not successful

## 12. Idempotency

Task identity must be derived from stable inputs such as:

```text
job_id + frame_id + stage_plan_version + effective_config_hash + source/artifact_hash
```

A task repeated with identical identity should either:
- reuse a verified committed result, or
- deterministically recompute without corrupting existing output

## 13. Ordering

Parallel execution does not change logical sticker ordering. Final result order derives from frame identity/index, not completion time.

Worker 10 may finish before worker 1; export remains `01.png ... 10.png`.

## 14. Backpressure and Fairness

Scheduler requirements:
- bounded inflight tasks
- bounded queued tasks
- per-job fairness when multiple jobs exist
- priority support
- resource-aware admission
- avoid starvation of REVIEW/retry work

### 14.1 Scheduler Foundation Contract
The MVP scheduler is an admission/dispatch policy component, not the durable authority.

Required behavior:
- queue capacity and inflight capacity are explicit hard bounds;
- duplicate task identity is rejected;
- tasks at the same priority are dispatched round-robin across jobs;
- a job-dispatchability callback gates PAUSED/STOPPING/otherwise blocked jobs without embedding lifecycle rules inside the scheduler;
- blocked tasks remain queued and are not silently dropped;
- priority is supported, but a configurable priority burst limit must allow lower-priority ready work to make progress;
- task completion releases an inflight slot;
- durable task assignment, attempt identity, leases and final state remain owned by JobStore/MainBoard services.

The scheduler may be replaced later without changing JobStore, worker-result validation or artifact-commit contracts.

### 14.2 Durable Scheduler Reconstruction
Scheduler queues are disposable process memory. Recovery reconstructs them from JobStore durable task descriptors.

Required behavior:
- new reconstructable tasks persist priority, descriptor payload and descriptor schema version in the same durable task-creation transaction;
- JobStore schema v3 introduces durable task descriptors without changing the existing task-state record contract;
- legacy v2 tasks receive an explicit non-reconstructable marker during migration rather than invented execution meaning;
- only PENDING and eligible INTERRUPTED tasks may enter a reconstructed queue;
- RUNNING tasks must first pass startup reconciliation; terminal/review states are not reconstructed;
- unsupported descriptor versions or priority values fail before partial enqueue;
- equal-priority reconstruction uses stable task identity ordering so restart does not introduce completion-time ordering;
- queue capacity remains authoritative at runtime; tasks that cannot fit are reported as deferred, not discarded;
- reconstruction changes only disposable scheduler state and never mutates durable task state.

## 15. Worker Failure Policy

Classify failures:
- transient/retryable
- provider-specific
- deterministic input failure
- resource exhaustion
- infrastructure/worker crash

Retry only when policy says it is safe. Deterministic invalid input should not loop retries.

## 16. Batch Job Aggregation

A batch may contain multiple sheets/jobs under a batch identifier.

Batch-level state is derived from child jobs:
- RUNNING
- PAUSED
- PARTIAL
- COMPLETED
- COMPLETED_WITH_REVIEW
- FAILED
- CANCELLED

One bad frame should not necessarily discard successful independent frames.

## 17. Performance Evidence

Performance tests should capture:
- throughput frames/minute
- p50/p95 frame time
- max resident memory
- CPU utilization
- queue wait time
- retries
- worker crashes
- disk write volume

Performance optimization may not bypass safety contracts.

## 18. Related SSOT

- `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`
- `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `33_ERROR_RECOVERY_AND_IDEMPOTENCY_SPEC.md`
- `31_STATE_MACHINE_SPEC.md`
- ADR-025
