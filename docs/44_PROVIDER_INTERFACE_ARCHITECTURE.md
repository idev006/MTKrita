# MTKrita Provider Interface Architecture

## Status
SSOT — Provider Architecture v1.0

## Purpose
กำหนดรูปแบบ interface/provider ของ MTKrita เพื่อให้ Python orchestrator สามารถเปลี่ยน image-processing engine ได้โดยไม่รื้อ domain workflow

## Principle

> **Depend on contracts, compose concrete providers at the edge.**

The orchestrator and domain pipeline shall depend on MTKrita-owned interfaces and result models. OpenCV, Pillow, ImageMagick and future ML engines are implementation details behind those interfaces.

## Logical Architecture

```text
GUI / CLI / Batch
       ↓
Python Orchestrator
       ↓
Domain Pipeline
       ↓
Provider Interfaces
 ┌─────┼───────────────┐
 ↓     ↓               ↓
OpenCV Pillow   Optional/Future Providers
                  ImageMagick / ML
```

## Mandatory Provider Interfaces

### LayoutDetectionProvider
Detect/infer sheet layout and return geometry + confidence/evidence.

### BorderProcessingProvider
Detect/remove supported frame borders and return detection evidence.

### MetadataProcessingProvider
Detect/remove frame-number or template metadata under constrained rules.

### BackgroundClassificationProvider
Classify opaque background characteristics for safe provider selection.

### BackgroundRemovalProvider
Produce RGBA/mask/evidence from opaque input.

### ContentAnalysisProvider
Return content bounds, occupancy, edge contact and component evidence.

### ImageTransformProvider
Perform approved quality-preserving transforms such as smart fit/downscale.

### ExportProvider
Write/encode output according to an export profile without changing domain policy.

## Domain-Owned Services
These shall remain MTKrita-owned policy and should not be delegated wholesale to third-party providers:
- processing mode selection
- transparency routing policy
- confidence thresholds for AUTO/REVIEW decisions
- QA status policy
- job/frame state transitions
- manifest/evidence rules
- retry/recovery policy

## Request/Result Model Rule
Interfaces shall exchange MTKrita-owned request/result objects. A provider result should include, as applicable:
- provider id/version
- strategy
- image/mask artifact
- measurements
- confidence
- findings
- deterministic flag
- warnings/failure class

Third-party engine-specific objects (for example raw OpenCV matrices or model sessions) must not become public domain contracts unless explicitly wrapped.

## Dependency Injection / Composition Root
Provider selection occurs in one composition layer during job initialization:

```text
TOML effective config
       ↓
ConfigLoader + Validator
       ↓
ProviderRegistry
       ↓
Concrete provider instances
       ↓
JobController / Pipeline
```

The system shall avoid provider-specific branches scattered across processing stages.

## Capability Discovery
A provider may declare capabilities such as:
- supported image modes
- deterministic behavior
- GPU requirement
- supported strategies
- provider version

The orchestrator may reject incompatible configuration before processing starts.

## Failure Boundary
Providers return classified failures; they do not directly decide final project status.

Example:

```text
provider: LOW_CONFIDENCE_MASK
        ↓
orchestrator/domain policy
        ↓
FrameStatus.REVIEW
```

## Testing
Every provider interface requires:
1. contract tests shared across implementations where practical
2. provider-specific unit tests
3. at least one replacement/fake provider in tests to prove the orchestrator is not coupled to a concrete engine
4. regression tests for destructive-risk behavior

## Change Control
Breaking an interface requires SSOT review, ADR when architectural, migration notes, affected contract tests and traceability update.

References: `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `45_TOML_CONFIGURATION_SPEC.md`, ADR-013 and ADR-015.
