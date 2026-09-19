# System Architecture

## Architecture Principle
MTKrita is a **document-driven, Python-orchestrated, engine-agnostic sticker production automation system**.

- SSOT documents define behavior before implementation.
- Python is the orchestration/control plane.
- Open-source image-processing engines/libraries provide lower-level capabilities.
- Sticker-specific domain rules remain in MTKrita, not hard-coded irreversibly into one provider.
- Ambiguous destructive decisions route to `REVIEW`.

See `25_DOCUMENT_DRIVEN_SSOT_OPERATING_MODEL.md`.

## High-Level Flow

```text
Input
  ↓
File Inspector
  ↓
Sheet Analyzer
  ↓
Grid Detector
  ↓
Frame Extractor
  ↓
Border / Metadata Processing
  ↓
Transparency Router
  ├─ meaningful alpha → preserve / skip BG removal
  └─ opaque → Background Analyzer / Mask Engine
  ↓
Content Analyzer
  ↓
Smart Fit Engine
  ↓
QA Engine
  ↓
Auto-Fix / REVIEW Routing
  ↓
Export Engine
  ↓
PNG Assets + Manifest + QA Report
```

## Control Plane and Provider Model

```text
UI / CLI / Future API
        ↓
Python Orchestrator / Job Controller
        ↓
Sticker Domain Logic
        ↓
Provider Interfaces
   ┌────┼───────────┐
   ▼    ▼           ▼
OpenCV Pillow  Optional Providers
              ImageMagick / ML
        ↓
Filesystem / OS
```

Python determines **when, why and under what confidence** a provider is called. Providers implement the lower-level image operation.

## Engine-Agnostic Interfaces
Critical capabilities should remain replaceable behind stable interfaces where practical, including:

- `GridDetector`
- `BorderDetector`
- `MetadataDetector`
- `BackgroundRemovalProvider`
- `ContentAnalyzer`
- `SmartFitEngine`
- `QAEngine`
- `ExportProvider`

Example background provider family:

```text
BackgroundRemovalProvider
  ├─ OpenCVFloodFillProvider
  ├─ OpenCVGrabCutProvider
  └─ FutureMLProvider
```

The workflow should not require redesign merely because a better provider becomes available.

## Core Decision
MVP will **not fork Krita**. MTKrita will first be implemented as an independent automation engine. Krita becomes an optional manual-review station for frames marked `REVIEW`.

## Planned Modules

- `FileInspector`
- `SheetAnalyzer`
- `GridDetector`
- `FrameExtractor`
- `BorderDetector`
- `MetadataDetector`
- `AlphaAnalyzer`
- `TransparencyRouter`
- `BackgroundAnalyzer`
- `MaskEngine`
- `ContentAnalyzer`
- `SmartFitEngine`
- `QAEngine`
- `AutoFixEngine`
- `ExportEngine`
- `JobController`

## Stage Contract Rule
Every critical stage must define input, output, failure behavior, confidence/validation evidence where relevant, REVIEW behavior and test coverage before it is considered release-ready.

## Krita Integration Model

```text
Automation Engine
  ├─ PASS / AUTO_FIXED → Export
  └─ REVIEW → Open in Krita → Manual Fix → Re-QA
```

This separation keeps the core headless-capable and avoids editor maintenance burden during MVP development.
