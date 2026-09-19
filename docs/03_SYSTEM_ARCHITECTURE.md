# System Architecture

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
Alpha / Background Analyzer
  ↓
Foreground Mask Engine
  ↓
Content Analyzer
  ↓
Smart Fit Engine
  ↓
QA Engine
  ↓
Auto-Fix Engine
  ↓
Export Engine
  ↓
PNG Assets + QA Report
```

## Application Layers

```text
UI / CLI / Future API
        ↓
Application Workflow
        ↓
Sticker Domain Logic
        ↓
Image Processing Services
        ↓
OpenCV / Pillow / NumPy
        ↓
Filesystem / OS
```

ImageMagick may be used as an optional processing/export backend.

## Core Decision
MVP will **not fork Krita**. MTKrita will first be implemented as an independent automation engine. Krita becomes an optional manual-review station for frames marked `REVIEW`.

## Planned Modules

- `FileInspector`
- `SheetAnalyzer`
- `GridDetector`
- `FrameExtractor`
- `AlphaAnalyzer`
- `BackgroundAnalyzer`
- `MaskEngine`
- `ContentAnalyzer`
- `SmartFitEngine`
- `QAEngine`
- `AutoFixEngine`
- `ExportEngine`
- `JobController`

## Krita Integration Model

```text
Automation Engine
  ├─ PASS / AUTO_FIXED → Export
  └─ REVIEW → Open in Krita → Manual Fix → Re-QA
```

This separation keeps the core headless-capable and avoids editor maintenance burden during MVP development.
