# MTKrita MainBoard Internal Communication Architecture

## Status
SSOT — Architecture Baseline v1.0

## Purpose
กำหนดโครงสร้างการสื่อสารภายใน MTKrita โดยใช้แนวคิด **MainBoard / Control Plane** เป็นศูนย์กลาง coordination เพื่อให้ทุก component สื่อสารกันผ่าน contract ที่ชัดเจน ลด coupling และป้องกัน worker เข้าถึง shared mutable state โดยตรง

## 1. Main Principle

> Workers execute work. MainBoard coordinates the system.

MainBoard ไม่ใช่ God Object และไม่ควรรวม implementation ของทุก service ไว้ใน class เดียว แต่เป็น composition root/control plane ที่ประกอบ service เฉพาะหน้าที่

## 2. MainBoard Components

```text
                    MainBoard / Control Plane
                              │
      ┌───────────────────────┼────────────────────────┐
      ▼                       ▼                        ▼
 JobController            Scheduler               EventBus
      │                       │                        │
      ├──────────────┬────────┴────────┬──────────────┤
      ▼              ▼                 ▼              ▼
 WorkerManager   ResourceBroker     JobStore       LogSink
      │              │                 │              │
      ▼              ▼                 ▼              ▼
   Workers       PathManager       Checkpoints    Diagnostics
```

Recommended responsibilities:

### JobController
- owns job lifecycle and allowed state transitions
- converts user requests to executable job plans
- applies pause/resume/stop/cancel policy

### Scheduler
- chooses runnable tasks
- honors dependency graph, priority and concurrency limits
- issues leases/tasks to workers

### WorkerManager
- creates/stops/restarts worker processes
- tracks worker health and heartbeat
- detects lost workers

### EventBus
- transports structured internal events
- decouples producers from consumers
- event schema is versioned

### ResourceBroker
- arbitrates shared mutable resources
- validates/publishes artifacts
- performs final shared writes through controlled operations

### JobStore
- authoritative durable state of jobs/tasks/checkpoints
- single logical writer policy preferred for MVP

### LogSink / Diagnostics
- central structured logging and event correlation
- produces diagnostic bundles

### PathManager
- sole authority for canonical runtime paths and resource locations

## 3. Commands vs Events

The internal protocol distinguishes:

**Command** — asks one component to perform an action.

Examples:
- `ExecuteTask`
- `PauseJob`
- `ResumeJob`
- `StopWorker`
- `CommitArtifact`

**Event** — records that something has happened.

Examples:
- `TaskStarted`
- `StageProgressed`
- `ArtifactProduced`
- `TaskSucceeded`
- `TaskFailed`
- `WorkerHeartbeat`
- `WorkerLost`

Commands have a target/owner. Events are observable facts.

## 4. Message Envelope

Every cross-component command/event should carry a standard envelope:

```text
message_id
schema_version
message_type
occurred_at
job_id
frame_id        optional
stage_id        optional
task_id         optional
worker_id       optional
correlation_id
causation_id
attempt
payload
```

This enables tracing a failure from final symptom back to the command/event chain that caused it.

## 5. Communication Rule

Workers never call shared persistence or final-output services directly.

Preferred flow:

```text
Scheduler → ExecuteTask → Worker
Worker → ArtifactProduced / TaskResult → MainBoard
MainBoard → ResourceBroker → validate/promote artifact
MainBoard → JobStore → persist durable state
MainBoard → EventBus/LogSink → publish evidence
```

## 6. Local MVP Transport

For the Windows desktop MVP, the architecture does not require a distributed message broker.

Initial implementation may use:
- `multiprocessing` queues/pipes
- `concurrent.futures.ProcessPoolExecutor` plus a controlled result channel
- in-process event dispatcher for control-plane services

The **message contract remains stable** so a future transport can be replaced without rewriting domain workflows.

## 7. MainBoard Single-Writer Principle

For shared job state, manifests and final artifact registry, use one logical writer in the control plane.

Workers may compute in parallel, but state commit is serialized/transactional through MainBoard-owned services.

This simplifies correctness substantially and avoids multiple workers racing to update the same job state.

## 8. Backpressure

MainBoard must control load:
- bounded task queue
- configurable worker count
- bounded pending-result queue
- resource-aware scheduling
- stop admitting new work when disk/memory/resource thresholds are exceeded

## 9. Health / Heartbeat

Workers report heartbeat and current task.

If a lease/heartbeat expires:
1. mark worker LOST
2. mark task interrupted, not completed
3. inspect committed checkpoint/artifacts
4. requeue only from last safe checkpoint
5. increment attempt counter

## 10. Failure Isolation

A worker crash must not crash MainBoard.
A provider crash inside one worker must not corrupt shared job state.
A malformed worker result must be rejected by contract validation.

## 11. MainBoard Availability

If MainBoard itself crashes, durable JobStore + artifact journal/checkpoints must allow recovery on next startup.

MainBoard startup performs reconciliation:

```text
load durable jobs
  ↓
scan incomplete attempts / temp artifacts
  ↓
validate journal/checkpoints
  ↓
mark stale workers LOST
  ↓
restore PAUSED / INTERRUPTED jobs
  ↓
allow controlled RESUME
```

## 12. Anti-patterns

Prohibited or strongly discouraged:
- direct worker → shared database writes
- direct worker → final output overwrite
- direct worker → global log-file append
- hidden global mutable singleton state
- UI directly controlling workers
- provider implementation publishing business state transitions
- workers discovering paths by themselves

## 13. Related SSOT

- `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `31_STATE_MACHINE_SPEC.md`
- `35_INTERFACE_AND_STAGE_CONTRACTS.md`
