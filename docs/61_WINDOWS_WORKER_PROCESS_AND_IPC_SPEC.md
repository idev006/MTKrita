# MTKrita Windows Worker Process and IPC Specification

## Status
SSOT — Worker Runtime Architecture Baseline v1.3 — ExecuteTask v2 / Immutable Input Boundary Verified

## Purpose
Define the concrete Windows worker-process boundary without coupling domain/pipeline logic to Python `multiprocessing`, UI technology, or a particular future transport.

## 1. Core Principle

> Worker processes compute; MainBoard owns authority.

A worker process is an isolated execution adapter. It never becomes an authority for job/task state, scheduler state, immutable input staging, final artifact publication, shared logs, or recovery policy.

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

`ExecuteTask` is governed by ADR-026, ADR-027, `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md`, and `63_IMMUTABLE_TASK_INPUT_AND_M2_EXECUTOR_MAPPING_SPEC.md`.

### 6.1 ExecuteTask Payload Version 2
Current ExecuteTask schema version is 2. It carries:
- durable descriptor version + immutable descriptor snapshot;
- explicit `inputs[]` approved by MainBoard;
- worker-private scratch path;
- envelope job/task/worker/attempt identity.

Each input contains:
- safe logical input name;
- PathManager-resolved staged INPUT path;
- SHA-256;
- byte size.

The worker does not derive input authority from an arbitrary path embedded in the durable descriptor. `ExecuteTaskCommandBuilder` reconstructs input from `PathManager.input(job_id, input_name)` and verifies staged bytes through ResourceBroker before command creation.

Tasks that require no file input use `inputs=[]`; this does not authorize arbitrary descriptor paths.

The ExecuteTask command never carries an authoritative final-output destination.

### 6.2 Current Child Behavior
- `WorkerInitialize` → `WorkerReady`;
- `PingWorker` → `WorkerHeartbeat`;
- `StopWorker` → `WorkerStopping` / `WorkerStopped`;
- ExecuteTask v2 is strictly parsed and identity/schema checked;
- valid ExecuteTask emits `TaskStarted`;
- until a concrete production executor is installed in the child bootstrap, baseline runtime emits structured `TaskFailed(WORKER.EXECUTOR_NOT_CONFIGURED)` instead of false success;
- malformed ExecuteTask contracts emit structured `WorkerInternalError` and do not execute.

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

A `TaskSucceededCandidate` is **not** durable success. Candidate payloads are versioned and validated through the task-result contract. Final success requires MainBoard-owned candidate coordination and ADR-024 artifact commitment.

## 8. Validated Event Routing

Decoded worker events pass through `WorkerEventRouter` before WorkerManager mutation or EventBus publication.

Rules:
- event kind must be `EVENT`;
- event type must be approved;
- worker identity is mandatory;
- task-related events require exact BUSY worker `task_id` + `attempt` identity;
- BUSY heartbeat must carry the same task identity; idle heartbeat must not claim one;
- `WorkerStopping` / `WorkerStopped` require authoritative STOPPING state;
- task candidate events do not directly release worker ownership or mutate durable task outcome in the router.

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
- immutable staged INPUT references explicitly supplied by ExecuteTask;
- its PathManager-allocated private scratch directory;
- provider-local memory/resources;
- IPC endpoints.

Worker must not directly mutate/access as authority:
- original external source;
- staged INPUT files;
- JobStore;
- final output namespace;
- artifact commit journal;
- shared JSONL log file;
- scheduler internals;
- another worker's scratch directory;
- UI objects.

For M2, worker independently verifies staged input existence/hash/size immediately before processing. Provisional result artifacts remain in worker-private scratch and are described by safe filename + SHA-256 + byte-size evidence only.

## 12. M2 Executor Adapter Boundary

The verified platform adapter `M2FrameTaskExecutor` is dependency-injected and does not duplicate M2 image algorithms.

It accepts injected:
- headless frame processor (`process_frame` in the M2 implementation);
- pipeline-config factory;
- PNG writer;
- optional image loader.

Adapter responsibilities:
- validate strict M2 descriptor;
- require exactly one approved immutable input;
- verify input identity/hash/size;
- call the injected headless frame pipeline;
- serialize findings/actions/evidence to JSON-compatible candidate evidence;
- map PASS/AUTO_FIXED → one scratch PNG success candidate;
- map REVIEW → review candidate without success artifact;
- map FAIL → structured failed candidate;
- never publish final output.

PR #9 remains the source of the actual image-processing algorithms. The platform adapter does not silently copy or redefine those algorithms.

## 13. Message Validation

Decoder/contract parser rejects:
- unsupported schema version;
- unknown required message kind/type;
- missing identity fields required by message type;
- oversized messages;
- malformed UTF-8/JSON;
- invalid attempt/frame/task types;
- inconsistent worker identity;
- unexpected ExecuteTask/result payload fields;
- unsafe input/provisional artifact names or invalid hashes/sizes;
- unsupported strict M2 descriptor fields/geometry/config.

Malformed worker messages become structured transport/contract errors, not raw exceptions exposed to UI.

## 14. Backpressure

IPC transport must not become an unbounded hidden queue.

Requirements:
- scheduler limits remain primary task admission control;
- MainBoard does not dispatch additional work to BUSY/LOST/STOPPING workers;
- event draining continues while orderly stop is in progress where safe;
- parent-side receive has explicit timeout rather than hidden indefinite blocking.

## 15. Testability and Current Evidence

Automated coverage includes:
- JSON wire round trip / UTF-8 / malformed JSON/type / unsupported schema / message-size limit;
- fake process-handle/session lifecycle;
- command/event direction contract;
- heartbeat identity validation;
- graceful stop behavior;
- worker loss through existing watchdog policy;
- real Windows spawn smoke;
- real Windows ExecuteTask transport smoke validating `TaskStarted → TaskFailed(WORKER.EXECUTOR_NOT_CONFIGURED)` while no production executor is installed;
- ExecuteTask v2 builder/parser and immutable input references;
- immutable input staging/source-preservation/hash/size tests;
- strict M2 descriptor and target resolver tests;
- M2 executor adapter PASS/AUTO_FIXED/REVIEW/FAIL/tampered-input tests;
- candidate result schema and candidate authority tests;
- platform integration test showing candidate success remains RUNNING until ADR-024 commit finalizes it.

Frozen/packaged executable worker bootstrap remains required before production release.

## 16. Security and Safety

- no arbitrary pickle as authoritative IPC format;
- no eval/exec/dynamic callable import from message payload;
- no arbitrary external path becomes worker input authority;
- no worker-selected final output destination;
- all task/worker/attempt identities are validated against durable/control-plane authority before acceptance;
- staged input is hash-bound and read-only by policy;
- worker process is fallible/untrusted relative to authoritative state;
- candidate result events do not constitute authoritative completion.

## 17. Packaging Constraints

The worker entrypoint is top-level/importable and designed for Windows spawn semantics. The selected standalone packager must preserve this bootstrap contract.

Source-tree CI success is necessary but not sufficient; packaged-runtime spawn/bootstrap smoke testing remains mandatory before G3/G4.

## 18. Implementation Status / Next Boundary

Completed:
1. JSON wire codec and byte-channel contracts;
2. fake transport/lifecycle tests;
3. Windows spawn process/session adapter;
4. WorkerEventRouter + WorkerRuntimeController;
5. real-process Windows runtime smoke;
6. immutable ExecuteTask v2 / candidate schema per ADR-026/027;
7. durable candidate result coordinator using ADR-024;
8. immutable INPUT staging and verification;
9. strict M2 task descriptor + MainBoard target resolver;
10. injectable M2 frame executor adapter;
11. component authority-chain test.

Next:
1. on a controlled integration branch, wire PR #9 `process_frame`, `FramePipelineConfig`, and `export_png_atomic` into `M2FrameTaskExecutor`;
2. install that built-in known executor into the child bootstrap without dynamic callable/module paths in payload;
3. add real-process successful M2 execution and authoritative commit test;
4. add packaged/frozen executable worker bootstrap smoke test during distribution milestone.

## 19. Related SSOT

- `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`
- `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`
- `60_PLATFORM_FOUNDATION_IMPLEMENTATION_STATUS.md`
- `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md`
- `63_IMMUTABLE_TASK_INPUT_AND_M2_EXECUTOR_MAPPING_SPEC.md`
- ADR-018, ADR-019, ADR-020, ADR-022, ADR-024, ADR-025, ADR-026, ADR-027

## 20. Verification Rule

PR #10 remains draft until the platform foundation is reviewed against this runtime contract. M2 algorithms may plug into the verified `TaskExecutor` adapter on an integration branch, but may not bypass immutable input staging, WorkerEventRouter, CandidateResultCoordinator, ResourceBroker, JobStore or ADR-024 artifact commitment.
