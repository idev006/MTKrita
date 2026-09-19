# MTKrita Task Execution and Candidate Result Commit Specification

## Status
SSOT — Task Execution / Result Authority Baseline v1.0

## Purpose
Define the control-plane boundary from an authoritative RUNNING task assignment through `ExecuteTask`, worker candidate events, and final durable outcome without allowing a worker or transport adapter to become a second source of truth.

## 1. Governing Principle

> Worker results are evidence candidates; only MainBoard-owned services can accept a durable outcome.

This specification implements ADR-026 and reuses ADR-024 for successful artifact commitment.

## 2. ExecuteTask Authority

`ExecuteTask` may be built only when all of the following are true:
- the durable JobStore task is `RUNNING`;
- `worker_id` and positive `attempt` are present in that durable record;
- the durable task descriptor belongs to the same `job_id` / `task_id`;
- the descriptor is reconstructable and has a supported positive descriptor version;
- worker scratch is allocated/resolved through PathManager.

The worker command shall not contain an authoritative final-output destination.

## 3. Worker Task Executor Boundary

Workers access task execution behind a replaceable `TaskExecutor` protocol.

Input is an immutable `ExecuteTaskRequest` containing:
- job/task/worker/attempt identity;
- descriptor schema version;
- immutable descriptor snapshot;
- control-plane supplied worker-private scratch path.

The executor must not receive JobStore, scheduler, UI, artifact journal, final-output namespace authority, or arbitrary callable/module execution instructions.

## 4. Candidate Result Types

Worker task outcomes are candidates:
- `TaskSucceededCandidate`
- `TaskReviewCandidate`
- `TaskFailed`

Every candidate must carry the exact `job_id`, `task_id`, `worker_id`, and `attempt` of the assigned task.

A candidate payload has an explicit schema version and may contain:
- provisional artifact descriptors;
- findings/evidence;
- failure code/message where applicable.

## 5. Provisional Artifact Contract

A provisional artifact may name only a safe single-component filename in the assigned worker scratch directory, plus:
- lowercase SHA-256;
- byte size.

It must not carry:
- final output path;
- another worker's scratch path;
- arbitrary absolute destination;
- mutable shared resource identifier that bypasses PathManager/ResourceBroker.

MainBoard reconstructs the source `PathRef` using `PathManager.worker_file(job_id, worker_id, filename)`.

## 6. MVP Success Cardinality

For the current artifact-commit protocol, a successful task candidate shall contain **exactly one primary provisional artifact**.

Reason:
- `ArtifactCommitCoordinator.commit_task_artifact()` finalizes the durable task after one artifact commitment;
- silently looping over multiple artifacts could leave partial multi-artifact publication after the task is already final;
- multi-artifact atomic/group commitment therefore requires a separate design/ADR before support is added.

Zero or more-than-one artifacts in a success candidate are rejected as a contract error and do not change durable task success.

## 7. Final Target Resolution

The worker never chooses the final target.

A MainBoard-owned `CandidateTargetResolver` (or equivalent domain service) resolves the final `PathRef` from trusted durable context such as:
- durable task descriptor;
- export/profile rules;
- stable frame/task identity.

Resolver output must be a PathManager-owned OUTPUT or EVIDENCE `PathRef` for the same job.

The result coordinator rejects any cross-job, worker-scratch, arbitrary external, or otherwise unsupported target.

## 8. Candidate Validation Order

Before accepting any candidate outcome, the control plane validates in this order:
1. parse candidate payload/schema;
2. load durable task;
3. require durable state `RUNNING` and exact job/worker/attempt identity;
4. require WorkerManager BUSY ownership for the same task/attempt;
5. require active runtime lease for that same worker/attempt;
6. for success, require exactly one provisional artifact;
7. reconstruct worker scratch source through PathManager;
8. ResourceBroker validates source existence, SHA-256, and byte size against candidate evidence;
9. final target is resolved by the trusted resolver;
10. ADR-024 artifact commit protocol validates/promotes/finalizes success;
11. only after durable outcome is accepted are runtime lease, worker BUSY ownership, and scheduler inflight ownership released.

A validation failure before durable outcome acceptance must not mark the task SUCCEEDED.

## 9. Success Candidate

`TaskSucceededCandidate` processing:
- candidate parse/identity/lease/ownership validation;
- exactly one artifact required;
- worker-private artifact hash + byte size verified;
- control-plane target resolved;
- `ArtifactCommitCoordinator` called with current durable RUNNING task;
- commit intent → atomic promote → durable finalize per ADR-024;
- task is considered SUCCEEDED only after durable finalization;
- runtime ownership is then released.

Final file existence alone is never success evidence.

## 10. Review Candidate

`TaskReviewCandidate` processing:
- exact authority validation as above;
- no final artifact publication is implied by REVIEW;
- durable task transitions to `REVIEW` through JobStore CAS using exact worker/attempt/generation;
- candidate findings remain evidence for review workflows;
- runtime ownership is released only after durable REVIEW transition succeeds.

Any future review-preview artifact publication requires an explicit evidence-target contract and must not be confused with final export success.

## 11. Failed Candidate

`TaskFailed` processing:
- exact authority validation as above;
- a structured failure code is mandatory;
- durable task transitions to `FAILED` using exact worker/attempt/generation;
- no provisional artifact is promoted as final output;
- runtime ownership is released only after durable FAILED transition succeeds.

Retry policy is a separate control-plane decision; worker failure does not automatically resubmit itself.

## 12. Runtime Finalization

After an accepted durable task outcome, the control plane shall release, for that exact task/worker/attempt:
- TaskLeaseRegistry lease;
- WorkerManager BUSY ownership → READY where appropriate;
- scheduler inflight slot.

Cleanup must never authorize a stale attempt. If runtime cleanup encounters already-reconciled state, it must not rewrite durable history.

## 13. Rejection and Error Safety

The following must never produce durable success:
- stale/superseded attempt;
- candidate from wrong worker;
- candidate for non-RUNNING task;
- missing/expired runtime lease at acceptance time;
- worker not BUSY on the exact task;
- malformed candidate schema;
- path traversal filename;
- missing source file;
- SHA-256 mismatch;
- byte-size mismatch;
- zero or multiple success artifacts;
- final target outside trusted PathManager namespace;
- final target selected by worker payload.

Rejected candidates may produce structured diagnostic/log evidence but must not silently mutate final artifacts or authoritative success state.

## 14. Test Requirements

Required automated regression coverage:
- valid one-artifact success commits through ADR-024 and only then reaches SUCCEEDED;
- worker payload cannot select final target;
- stale attempt and wrong worker rejected;
- hash and byte-size mismatch rejected without success;
- path traversal provisional filename rejected;
- zero/multiple success artifacts rejected;
- REVIEW and FAILED transition durably before runtime cleanup;
- runtime lease/worker/inflight released after accepted terminal/review outcome;
- malformed candidate leaves durable RUNNING task unchanged;
- candidate target resolver cannot return cross-job or worker-scratch target;
- crash during success promotion remains recoverable through existing artifact-commit reconciliation.

## 15. Related SSOT

- `35_INTERFACE_AND_STAGE_CONTRACTS.md`
- `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`
- `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `61_WINDOWS_WORKER_PROCESS_AND_IPC_SPEC.md`
- ADR-019, ADR-020, ADR-024, ADR-025, ADR-026
