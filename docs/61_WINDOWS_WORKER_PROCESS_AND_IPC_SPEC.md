# MTKrita Windows Worker Process and IPC Specification

## Status
SSOT — Worker Runtime Architecture Baseline v1.0

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

Preferred layers:

```text
MainBoard / WorkerManager
        ↓
WorkerProcessFactory protocol
        ↓
WindowsSpawnWorkerFactory
        ↓
ProcessWorkerHandle + IPC endpoint
        ↓
spawned worker entrypoint
```

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

For the initial Windows adapter, two unidirectional `multiprocessing.Connection`/Pipe-style byte channels are acceptable behind the transport interface.

Separate directions reduce accidental concurrent writes and simplify ownership rules.

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

## 9. Heartbeat Contract

Worker heartbeats:
- originate in worker runtime;
- include worker identity and current task/attempt when applicable;
- are converted to validated MainBoard events;
- update WorkerManager liveness only after validation;
- do not renew durable task lease automatically unless lease policy explicitly authorizes that action.

Heartbeat and task-lease renewal are related but separate decisions.

## 10. Stop and Termination

Normal stop sequence:

```text
MainBoard sends StopWorker
  ↓
worker stops accepting new work
  ↓
worker reaches safe cooperative boundary
  ↓
worker emits WorkerStopping / WorkerStopped
  ↓
process exits
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

## 13. Backpressure

IPC transport must not become an unbounded hidden queue.

Requirements:
- scheduler limits remain the primary task admission control;
- transport send/receive behavior must have bounded or observable buffering;
- MainBoard shall not dispatch additional work to BUSY/LOST/STOPPING workers;
- result/event draining must continue while orderly stop is in progress where safe.

## 14. Testability

Required automated tests:
- wire encode/decode round trip;
- unsupported schema rejection;
- malformed JSON/type rejection;
- message-size limit rejection;
- fake process-handle lifecycle;
- command/event direction contract;
- heartbeat event validation;
- graceful stop behavior;
- worker crash maps to LOST/INTERRUPTED through existing watchdog policy;
- real Windows spawn smoke test before release candidate;
- frozen/packaged executable worker bootstrap test before production release.

Unit/component tests should not require real child processes unless the behavior specifically concerns OS process semantics.

## 15. Security and Safety

- do not deserialize arbitrary pickle from a worker or external source as the authoritative IPC format;
- no eval/exec/dynamic callable import from message payload;
- reject arbitrary shared filesystem destinations;
- validate all task/worker/attempt identities against durable MainBoard authority before commit;
- treat worker process as fallible/untrusted relative to authoritative state.

## 16. Packaging Constraints

The concrete worker entrypoint must remain compatible with the selected Windows standalone packager. Process spawn/bootstrap tests must be run against the packaged runtime before G3/G4 release gates.

## 17. Implementation Sequence

1. implement JSON wire codec behind protocol;
2. implement in-memory/fake transport contract tests;
3. implement Windows spawn `ProcessWorkerHandle` / factory;
4. connect decoded events to EventBus/WorkerManager;
5. connect task commands to immutable task executor boundary;
6. add real-process Windows CI smoke test;
7. add packaged-runtime smoke test during distribution milestone.

## 18. Related SSOT

- `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`
- ADR-018, ADR-019, ADR-020, ADR-022, ADR-025
