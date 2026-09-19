# MTKrita Windows Worker Process and IPC Specification

## Status
SSOT — Worker Runtime Architecture Baseline v1.2 — Spawn / ExecuteTask Transport Verified

## Purpose
Define the concrete Windows worker-process boundary without coupling domain/pipeline logic to Python `multiprocessing`, UI technology, or a particular future transport.

## 1. Core Principle

> Worker processes compute; MainBoard owns authority.

A worker process is an isolated execution adapter. It never becomes an authority for job/task state, scheduler state, final artifact publication, shared logs, or recovery policy.

## 2. Windows Process Model

The production desktop runtime shall use explicit **spawn semantics** on Windows.

Rules:
- no dependency on inherited mutable process state;
- worker bootstrap inputs must be explicit and serializable;
- import-time side effects are prohibited in worker modules;
- worker entrypoints must be top-level/importable functions suitable for frozen Windows applications;
- process creation remains behind a factory/adapter interface so tests can use fake handles.

Implemented layers:

```text
MainBoard / WorkerManager / WorkerRuntimeController
        ↓
WorkerProcessFactory protocol
        ↓
WindowsSpawnWorkerFactory
        ↓
ProcessWorkerHandle + ProcessWorkerSession
        ↓
spawned worker_process_entrypoint
```

The concrete factory uses `multiprocessing.get_context("spawn")`; that implementation detail remains confined to the adapter layer.

## 3. IPC Principle

Cross-process communication uses an explicit versioned wire schema.

Python object pickling is **not** the domain IPC contract. Domain dataclasses/classes are not sent directly as authoritative messages between processes.

Baseline wire format:
- UTF-8 JSON bytes;
- explicit wire schema version;
- explicit message kind/type;
- validated maximum message size;
- deterministic field names;
- no executable code, callable, arbitrary module path, or arbitrary Python object in payload.

## 4. Channel Direction

Use logically separate channels:

```text
MainBoard → Worker : COMMAND channel
Worker → MainBoard : EVENT/RESULT channel
```

The current Windows adapter uses two unidirectional Pipe-style byte channels behind `JsonMessageSender` / `JsonMessageReceiver` and `ProcessWorkerSession`.

Parent-side session ownership includes both channel endpoints; deterministic close is required.

## 5. Wire Envelope

Minimum envelope fields:

```text
schema_version
message_id
kind
message_type
occurred_at
job_id
correlation_id
causation_id?
frame_id?
stage_id?
task_id?
worker_id?
attempt?
payload
```

The wire envelope maps to/from `MessageEnvelope`, but decoding validates types/schema before MainBoard/EventBus publication.

## 6. Command Types

Baseline commands:
- `WorkerInitialize`
- `ExecuteTask`
- `StopWorker`
- `PingWorker`

`ExecuteTask` is governed by ADR-026 and `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md`.

Current implementation:
- `WorkerInitialize` → `WorkerReady`;
- `PingWorker` → `WorkerHeartbeat`;
- `StopWorker` → `WorkerStopping` / `WorkerStopped`;
- `ExecuteTask` payload is strictly parsed and identity/schema checked;
- valid ExecuteTask emits `TaskStarted`;
- until a concrete production `TaskExecutor` is injected, the baseline child emits structured `TaskFailed` with error code `WORKER.EXECUTOR_NOT_CONFIGURED` rather than pretending task success exists;
- malformed ExecuteTask contracts emit structured `WorkerInternalError` and do not execute.

The ExecuteTask command never carries an authoritative final-output destination.

## 7. Candidate Result Events

Baseline task events:
- `TaskStarted`
- `TaskSucceededCandidate`
- `TaskReviewCandidate`
- `TaskFailed`

Other runtime events:
- `WorkerReady`
- `WorkerHeartbeat`
- `WorkerStopping`
- `WorkerStopped`
- `WorkerInternalError`

A `TaskSucceededCandidate` is **not** durable success. Candidate result payloads are versioned and validated through the task-result contract. Final success requires the MainBoard-owned candidate coordinator and ADR-024 artifact-commit protocol.

## 8. Validated Event Routing

Decoded worker events pass through `WorkerEventRouter` before WorkerManager mutation or EventBus publication.

Rules:
- event kind must be `EVENT`;
- event type must be approved;
- worker identity is mandatory;
- task-related events require the exact BUSY worker `task_id` + `attempt` identity;
- BUSY heartbeat must carry the same task identity; idle heartbeat must not claim one;
- `WorkerStopping` / `WorkerStopped` require authoritative STOPPING state;
- task candidate events do not directly release the worker or mutate durable task outcome in the router.

After validation/state update, events are published to the shared EventBus for structured logging and application observers.

## 9. Heartbeat Contract

Worker heartbeats:
- originate in worker runtime;
- include worker identity and current task/attempt when applicable;
- update WorkerManager liveness only after validation;
- do not renew durable task lease automatically unless explicit lease policy authorizes renewal.

Heartbeat and task-lease renewal remain separate decisions.

`WorkerRuntimeController.ping()` copies the authoritative active task/attempt identity from WorkerManager when pinging a BUSY worker.

## 10. Stop and Termination

Normal stop sequence:

```text
MainBoard/application service requests stop
  ↓
WorkerManager enters STOPPING and ProcessWorkerHandle sends StopWorker
  ↓
worker reaches cooperative boundary
  ↓
worker emits WorkerStopping / WorkerStopped
  ↓
WorkerEventRouter validates lifecycle events
  ↓
WorkerManager enters STOPPED
  ↓
WorkerRuntimeController waits for actual process exit
  ↓
session endpoints close
```

Hard termination is an escalation path for lost/unresponsive workers only. Process exit alone never implies task success.

## 11. Worker Resource Rules

Worker may access:
- immutable input/resource references explicitly supplied by the approved task contract;
- its PathManager-allocated private scratch directory;
- provider-local memory/resources;
- its IPC endpoints.

Worker must not directly mutate/access as authority:
- JobStore;
- final output namespace;
- artifact commit journal;
- shared JSONL log file;
- scheduler internals;
- another worker's scratch directory;
- UI objects.

Provisional result artifacts remain in worker-private scratch and are described by safe filename + SHA-256 + byte-size evidence only.

## 12. Message Validation

Decoder/contract parser rejects:
- unsupported schema version;
- unknown required message kind/type;
- missing identity fields required by message type;
- oversized messages;
- malformed UTF-8/JSON;
- invalid attempt/frame/task types;
- inconsistent worker identity;
- unexpected ExecuteTask/result payload fields;
- unsafe provisional artifact names or invalid hashes/sizes.

Malformed worker messages become structured transport/contract errors, not raw exceptions exposed to UI.

## 13. Backpressure

IPC transport must not become an unbounded hidden queue.

Requirements:
- scheduler limits remain primary task admission control;
- MainBoard does not dispatch additional work to BUSY/LOST/STOPPING workers;
- event draining continues while orderly stop is in progress where safe;
- parent-side receive has explicit timeout rather than hidden indefinite blocking.

## 14. Testability and Current Evidence

Automated coverage includes:
- JSON wire round trip / UTF-8 / malformed JSON/type / unsupported schema / message-size limit;
- fake process-handle/session lifecycle;
- command/event direction contract;
- heartbeat identity validation;
- graceful stop behavior;
- worker loss through existing watchdog policy;
- real Windows spawn smoke;
- real Windows `ExecuteTask` transport smoke validating `TaskStarted → TaskFailed(WORKER.EXECUTOR_NOT_CONFIGURED)` while no concrete production executor exists;
- ExecuteTask command builder and strict parser;
- candidate result schema, provisional artifact safety and candidate authority tests;
- platform integration test showing candidate success remains RUNNING until ADR-024 commit finalizes it.

Frozen/packaged executable worker bootstrap remains required before production release.

## 15. Security and Safety

- no arbitrary pickle as authoritative IPC format;
- no eval/exec/dynamic callable import from message payload;
- no worker-selected final output destination;
- all task/worker/attempt identities are validated against durable/control-plane authority before acceptance;
- worker process is fallible/untrusted relative to authoritative state;
- candidate result events do not constitute authoritative completion.

## 16. Packaging Constraints

The worker entrypoint is top-level/importable and designed for Windows spawn semantics. The selected standalone packager must preserve this bootstrap contract.

Source-tree CI success is necessary but not sufficient; packaged-runtime spawn/bootstrap smoke testing remains mandatory before G3/G4.

## 17. Implementation Status / Next Boundary

Completed:
1. JSON wire codec and byte-channel contracts;
2. fake transport/lifecycle tests;
3. Windows spawn process/session adapter;
4. WorkerEventRouter + WorkerRuntimeController;
5. real-process Windows runtime smoke;
6. immutable ExecuteTask command/result candidate schema per ADR-026;
7. durable candidate result coordinator using existing ADR-024 commit path;
8. component end-to-end authority-chain test.

Next:
1. connect a real MTKrita image-processing `TaskExecutor` implementation to the worker boundary;
2. define the production durable task descriptor fields consumed by that executor without introducing arbitrary path/callable semantics;
3. add real-process success integration once the M2 executor exists;
4. add packaged/frozen executable worker bootstrap smoke test during distribution milestone.

## 18. Related SSOT

- `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`
- `60_PLATFORM_FOUNDATION_IMPLEMENTATION_STATUS.md`
- `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md`
- ADR-018, ADR-019, ADR-020, ADR-022, ADR-024, ADR-025, ADR-026

## 19. Verification Rule

PR #10 remains draft until the platform foundation is reviewed against this runtime contract. A future image-processing executor may plug into `TaskExecutor`, but it may not bypass WorkerEventRouter, CandidateResultCoordinator, ResourceBroker, JobStore or ADR-024 artifact commitment.
