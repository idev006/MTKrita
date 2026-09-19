# Pipeline Engineering Guide

## Engineering Objective
สร้าง pipeline ที่ headless-capable, deterministic, restartable และ batch-ready โดยแยก image algorithms ออกจาก orchestration และ UI

## Logical Modules
- `FileInspector`
- `SheetAnalyzer`
- `GridDetector`
- `FrameExtractor`
- `BorderDetector`
- `BorderRemovalEngine`
- `AlphaAnalyzer`
- `BackgroundAnalyzer`
- `MaskEngine`
- `ContentAnalyzer`
- `SmartFitEngine`
- `QAEngine`
- `AutoFixEngine`
- `ExportEngine`
- `ManifestWriter`
- `JobController`

## Pipeline Contract
Every processing function should favor explicit input/output models over hidden global state.

Example conceptual signature:
```text
StageResult = stage(ImageArtifact, StageConfig, Context)
```

`StageResult` contains artifact, measurements, findings, confidence, actions, timing and error details.

## Idempotency
A completed job re-run with identical input hash, config hash and engine version should produce equivalent deterministic artifacts for deterministic stages.

## Checkpointing
For batch jobs, preserve stage outputs/metadata sufficiently to resume without repeating expensive earlier stages where safe.

## Error Taxonomy
- input/format error
- geometry detection error
- ambiguous border
- segmentation uncertainty
- quality policy violation
- export/profile violation
- system/dependency error

Errors must be machine-readable and mapped to user-facing messages.

## Observability
Per job/frame capture:
- stage name
- start/end timestamps
- duration
- algorithm/strategy selected
- parameters/profile version
- confidence
- warnings/errors
- input/output hashes where applicable

## Performance Principles
- CPU-first MVP
- avoid unnecessary image copies
- vectorized NumPy/OpenCV operations
- parallelism at independent frame/job level only after determinism and memory use are validated
- never trade foreground safety for throughput

## External Editor Boundary
Krita integration is an adapter, not a dependency of core execution. Core CLI and tests must run without Krita installed.

## Dependency Isolation
Third-party engines must sit behind adapters so they can be upgraded/replaced without changing domain rules.

## Future AI Adapter
AI segmentation/review must implement the same mask/confidence contract and remain optional. AI output never bypasses QA.