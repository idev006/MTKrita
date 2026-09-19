# MTKrita UML System Model

## Status
SSOT — UML Architecture Baseline v1.0

## 1. System Context

```mermaid
flowchart LR
    Operator[Operator] --> App[MTKrita]
    App --> FS[Windows Filesystem]
    App --> CV[OpenCV Provider]
    App --> PIL[Pillow Provider]
    App --> OPT[Optional Providers]
    App --> Krita[Optional Krita Review]
    App --> Out[PNG / Manifest / Reports]
```

## 2. Component Diagram

```mermaid
flowchart TD
    UI[Desktop UI] --> APP[Application / JobController]
    CLI[CLI] --> APP
    API[Future API] --> APP

    APP --> DOMAIN[Sticker Domain Services]
    DOMAIN --> LAYOUT[Layout / Split]
    DOMAIN --> BORDER[Border Detection]
    DOMAIN --> META[Metadata Removal]
    DOMAIN --> ROUTE[Transparency Router]
    DOMAIN --> BG[Background Removal]
    DOMAIN --> CONTENT[Content Analysis]
    DOMAIN --> FIT[Smart Fit]
    DOMAIN --> QA[QA Engine]
    DOMAIN --> EXP[Export Engine]

    LAYOUT --> PROVIDERS[Image Processing Provider Layer]
    BORDER --> PROVIDERS
    META --> PROVIDERS
    BG --> PROVIDERS
    FIT --> PROVIDERS
    EXP --> PROVIDERS

    PROVIDERS --> OPENCV[OpenCV]
    PROVIDERS --> PILLOW[Pillow]
    PROVIDERS --> OPTIONAL[Optional Provider]

    APP --> MANIFEST[Manifest / Evidence]
```

## 3. Core Domain Class Model

```mermaid
classDiagram
    class JobManifest {
      +job_id: str
      +input_file: str
      +input_hash: str
      +engine_version: str
      +config_hash: str
      +frames: List~FrameResult~
    }

    class FrameResult {
      +index: int
      +row: int
      +column: int
      +status: FrameStatus
      +processing_mode: ProcessingMode
      +content_bbox
      +findings: List~Finding~
      +actions: List~str~
      +output_file: str
    }

    class Finding {
      +code: str
      +severity: str
      +message: str
      +measurements: dict
    }

    class JobController {
      +run()
      +resume()
      +finalize()
    }

    class FramePipeline {
      +process(frame)
    }

    class Provider {
      <<interface>>
      +execute()
    }

    JobManifest "1" o-- "many" FrameResult
    FrameResult "1" o-- "many" Finding
    JobController --> JobManifest
    JobController --> FramePipeline
    FramePipeline --> Provider
```

## 4. Provider Interface Model

```mermaid
classDiagram
    class BackgroundRemovalProvider {
      <<interface>>
      +remove(image, context) MaskResult
    }
    class FloodFillProvider
    class GrabCutProvider
    class MLProvider

    BackgroundRemovalProvider <|.. FloodFillProvider
    BackgroundRemovalProvider <|.. GrabCutProvider
    BackgroundRemovalProvider <|.. MLProvider
```

The same replaceable-provider principle applies to layout, metadata, export and other engine-backed operations where practical.

## 5. Package Dependency Rule

```mermaid
flowchart TD
    UI[ui/] --> APP[application/]
    CLI[cli] --> APP
    APP --> DOMAIN[domain/]
    DOMAIN --> SERVICES[services/]
    SERVICES --> PROVIDERS[providers/]
    PROVIDERS --> LIBS[OpenCV / Pillow / optional libs]
    APP --> INFRA[infrastructure/]
    INFRA --> FS[filesystem / config / logging]
```

### Dependency constraints
- UI must not contain sticker-processing business rules.
- Domain must not depend on UI.
- Provider-specific APIs must not leak through domain contracts unless explicitly documented.
- Core pipeline must remain headless-capable.
- Krita must remain optional for MVP/core runtime.

## 6. Responsibility Boundaries
- **JobController** owns job-level orchestration and evidence.
- **FramePipeline** owns frame-level stage sequencing.
- **Domain services** own sticker-specific decisions.
- **Providers** own low-level image operations.
- **QAEngine** owns rule evaluation, not image modification.
- **AutoFixEngine** may modify only operations explicitly classified as safe.
- **ExportEngine** owns output profile validation and deterministic serialization.

## 7. Architecture Invariant

> Domain intent controls providers; providers must not redefine domain behavior.

References: `03_SYSTEM_ARCHITECTURE.md`, `25_DOCUMENT_DRIVEN_SSOT_OPERATING_MODEL.md`, `DECISIONS.md`.
