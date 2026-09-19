# MTKrita Windows Worker Process and IPC Specification

## Status
SSOT — Worker Runtime Architecture Baseline v1.1 — Spawn/Event Runtime Verified

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

## 3. Process Adapter Boundary

The concrete runtime adapter shall satisfy the existing `WorkerHandle` contract and may extend it with transport lifecycle services.

MainBoard/domain code must not directly call `multiprocessing.Process`, `Pipe`, `Queue`, or OS process primitives.

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

The concrete factory currently uses `multiprocessing.get_context("spawn")`; that implementation detail remains confined to the adapter layer.

## 4. IPC Principle

Cross-process communication uses an explicit versioned wire schema.

Python object pickling is **not** the domain IPC contract. Domain dataclasses/classes are not sent directly as authoritative messages between processes.

Baseline wire format:
- UTF-8 JSON bytes;
- explicit wire schema version;
- explicit message kind/type;
- validated maximum message size;
- deterministic field names;
- no executable code, callable, arbitrary module path, or arbitrary Python object in payload.

This keeps the process boundary inspectable, testable and replaceable.

## 5. Channel Direction

Use logically separate channels:

```text
MainBoard → Worker : COMMAND channel
Worker → MainBoard : EVENT/RESULT channel
```

The current Windows adapter uses two unidirectional Pipe-style byte channels behind `JsonMessageSender` / `JsonMessageReceiver` and `ProcessWorkerSession`.

Separate directions reduce accidental concurrent writes and simplify ownership rules. Parent-side session ownership includes both channel endpoints; deterministic close is required.

## 6. Required Wire Envelope

Minimum fields:

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

The wire envelope maps to/from the application `MessageEnvelope`, but decoding must validate types and schema before publishing to MainBoard/EventBus.

## 7. Initial Command Types

Baseline commands:
- `WorkerInitialize`
- `ExecuteTask`
- `StopWorker`
- optional `PingWorker`

`ExecuteTask` carries an immutable task descriptor generated from durable task metadata plus PathManager/ResourceBroker-approved private references. It must never carry arbitrary shared output paths for direct mutation.

Current implementation status:
- `WorkerInitialize` implemented;
- `PingWorker` implemented;
- `StopWorker` implemented;
- `ExecuteTask` intentionally returns structured `WorkerInternalError` until the immutable task-executor/result contract is separately approved and implemented. The runtime must not pretend task execution support exists before that contract is present.

## 8. Initial Event Types

Baseline worker events:
- `WorkerReady`
- `WorkerHeartbeat`
- `TaskStarted`
- `TaskSucceededCandidate`
- `TaskReviewCandidate`
- `TaskFailed`
- `WorkerStopping`
- `WorkerStopped`
- `WorkerInternalError`

A `TaskSucceededCandidate` is **not** durable success. MainBoard must validate attempt/lease/result and use the artifact commit protocol before task success is accepted.

### 8.1 Validated Event Routing
Decoded worker events pass through `WorkerEventRouter` before WorkerManager mutation or EventBus publication.

Rules:
- event kind must be `EVENT`;
- event type must be in the approved worker-event set;
- worker identity is mandatory;
- task-related events require the exact BUSY worker `task_id` + `attempt` identity;
- BUSY heartbeat must carry the same task identity; idle heartbeat must not claim one;
- `WorkerStopping` / `WorkerStopped` require authoritative STOPPING state;
- `TaskSucceededCandidate` / `TaskReviewCandidate` / `TaskFailed` do not directly release the worker or mutate durable task success/failure state in the router.

After validation/state update, events are published to the shared EventBus so existing structured logging and application subscribers observe the same validated event stream.

## 9. Heartbeat Contract

Worker heartbeats:
- originate in worker runtime;
- include worker identity and current task/attempt when applicable;
- are converted to validated MainBoard events;
- update WorkerManager liveness only after validation;
- do not renew durable task lease automatically unless lease policy explicitly authorizes that action.

Heartbeat and task-lease renewal are related but separate decisions.

`WorkerRuntimeController.ping()` copies the authoritative active task/attempt identity from WorkerManager when pinging a BUSY worker, preventing a heartbeat from inventing ownership data.

## 10. Stop and Termination

Normal stop sequence:

```text
MainBoard/application service requests stop
  ↓
WorkerManager enters STOPPING and ProcessWorkerHandle sends StopWorker
  ↓
worker stops accepting new work
  ↓
worker emits WorkerStopping / WorkerStopped
  ↓
WorkerEventRouter validates lifecycle events
  ↓
WorkerManager enters STOPPED
  ↓
WorkerRuntimeController waits for actual process exit
  ↓
session endpoints may be closed
```

Hard process termination is an escalation path for lost/unresponsive workers only. A killed worker's active task becomes interrupted/recoverable; it is never marked successful solely because the process exited.

## 11. Worker Resource Rules

Worker may access:
- immutable input references explicitly supplied to the task;
- its PathManager-allocated private scratch directory;
- provider-local memory/resources;
- its IPC endpoints.

Worker must not directly access/mutate:
- JobStore;
- final output namespace;
- artifact commit journal;
- shared JSONL log file;
- scheduler internals;
- another worker's scratch directory;
- UI objects.

## 12. Message Validation

Decoder rejects:
- unsupported schema version;
- unknown required message kind;
- missing identity fields required by message type;
- oversized messages;
- malformed UTF-8/JSON;
- invalid attempt/frame/task types;
- inconsistent worker identity;
- payload structures outside the expected JSON-compatible contract.

Malformed worker messages become structured transport/contract errors, not raw exceptions leaked into UI.

`ProcessWorkerSession` additionally enforces command/event channel direction and validates event worker identity on receive.

## 13. Backpressure

IPC transport must not become an unbounded hidden queue.

Requirements:
- scheduler limits remain the primary task admission control;
- transport send/receive behavior must have bounded or observable buffering;
- MainBoard shall not dispatch additional work to BUSY/LOST/STOPPING workers;
- result/event draining must continue while orderly stop is in progress where safe;
- parent-side event receive supports explicit timeout rather than indefinite hidden blocking in control-plane orchestration.

## 14. Testability

Required automated tests:
- wire encode/decode round trip;
- unsupported schema rejection;
- malformed JSON/type rejection;
- message-size limit rejection;
- fake process-handle/session lifecycle;
- command/event direction contract;
- heartbeat event validation;
- graceful stop behavior;
- worker crash maps to LOST/INTERRUPTED through existing watchdog policy;
- real Windows spawn smoke test before release candidate;
- frozen/packaged executable worker bootstrap test before production release.

Verified in current platform track:
- JSON wire contract tests;
- fake WorkerManager/runtime lifecycle tests;
- event identity/state validation tests;
- real Windows runner spawn → initialize → ready → ping/heartbeat → graceful stop → process exit smoke test.

Unit/component tests do not require real child processes unless the behavior specifically concerns OS process semantics.

## 15. Security and Safety

- do not deserialize arbitrary pickle from a worker or external source as the authoritative IPC format;
- no eval/exec/dynamic callable import from message payload;
- reject arbitrary shared filesystem destinations;
- validate all task/worker/attempt identities against durable MainBoard authority before commit;
- treat worker process as fallible/untrusted relative to authoritative state;
- candidate result events do not constitute authoritative completion.

## 16. Packaging Constraints

The concrete worker entrypoint is top-level/importable and designed for Windows spawn semantics. The selected standalone packager must preserve this bootstrap contract.

Process spawn/bootstrap tests must be run against the packaged runtime before G3/G4 release gates. Source-tree CI success is necessary but not sufficient evidence for frozen executable behavior.

## 17. Implementation Sequence

Completed in current track:
1. JSON wire codec behind explicit byte-channel protocols;
2. in-memory/fake transport and lifecycle contract tests;
3. Windows spawn `ProcessWorkerHandle` / `WindowsSpawnWorkerFactory` / `ProcessWorkerSession`;
4. decoded event validation into WorkerManager + EventBus via `WorkerEventRouter`;
5. real-process Windows source-tree CI smoke test;
6. application-level `WorkerRuntimeController` for start/pump/ping/stop/close lifecycle.

Next:
1. define immutable `ExecuteTask` payload and worker task-executor interface;
2. define/validate candidate result payloads and connect them to existing durable result/artifact-commit services;
3. add dispatched-task → child process → candidate → authoritative commit integration test;
4. add packaged/frozen executable worker bootstrap smoke test during distribution milestone.

## 18. Related SSOT

- `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`
- `60_PLATFORM_FOUNDATION_IMPLEMENTATION_STATUS.md`
- ADR-018, ADR-019, ADR-020, ADR-022, ADR-025

## 19. Verification Evidence

Current Windows source-tree CI verifies that the spawned child process imports the top-level worker entrypoint and communicates only through the explicit JSON message layer for runtime commands/events. The worker process does not open JobStore, commit final artifacts, write the shared log, or mutate scheduler state.

The platform shall retain PR #10 as draft until the ExecuteTask/result-candidate path is implemented or explicitly split into a later reviewed milestone.
