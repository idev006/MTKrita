# MTKrita Reference Implementation Blueprint

## Status
SSOT — Engineering Blueprint v1.0

## Purpose
กำหนดโครงสร้าง implementation อ้างอิงให้ทีมพัฒนาวาง module ได้สอดคล้องกัน โดยไม่บังคับรายละเอียดภายในเกินความจำเป็น

## Package Shape
```text
src/mtkrita/
  app/
    mainboard.py
    job_controller.py
    scheduler.py
    worker_manager.py
    resource_broker.py
  domain/
    models.py
    states.py
    findings.py
    errors.py
  contracts/
    providers.py
    stages.py
    resources.py
  providers/
    opencv/
    pillow/
    optional/
  pipeline/
    sheet_pipeline.py
    frame_pipeline.py
    stages/
  infra/
    path_manager.py
    job_store.py
    artifact_store.py
    event_bus.py
    logging.py
    diagnostics.py
    config.py
  ui/
  cli.py
```

## Dependency Direction
`UI/CLI -> app -> domain/contracts -> providers/infra`

Forbidden:
- provider imports app/orchestrator
- worker writes shared JobStore directly
- arbitrary module builds filesystem paths manually
- UI owns processing policy

## MainBoard Composition
MainBoard composes Scheduler, WorkerManager, ResourceBroker, EventBus, JobStore, Diagnostics and provider registry. MainBoard coordinates but should delegate work to specialized services to avoid God Object design.

## Worker Contract
Worker receives immutable task envelope and resource references, works in private scratch space, returns structured result/evidence. Shared-state commit is performed centrally after result validation.

## Task Envelope Minimum
- job_id
- task_id
- frame_id/index
- stage
- attempt
- lease_id / lease expiry
- effective_config_hash
- input ArtifactRef/SourceRef
- correlation_id

## Commit Model
worker result -> validate attempt/lease -> validate artifact/hash -> atomic artifact commit -> JobStore transaction -> emit event

## Provider Selection
Provider registry/factory maps TOML-selected provider IDs to interface implementations. Domain code never branches on concrete library types.

## Configuration
Load TOML -> validate typed model -> compute effective config -> hash -> freeze for job execution.

## Reliability Baseline
- persistent state before dispatch where needed
- idempotent/replay-safe stage boundaries
- stale-attempt rejection
- atomic final commit
- structured logs/events
- deterministic error codes
- diagnostic bundle generation

References: `44_PROVIDER_INTERFACE_ARCHITECTURE.md`, `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`, `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`, `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`, `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`.
