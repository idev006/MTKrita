# MTKrita Sequence Diagrams

## Status
SSOT — Sequence Baseline v1.0

## 1. Main Processing Sequence

```mermaid
sequenceDiagram
    actor U as Operator
    participant UI as UI/CLI
    participant JC as JobController
    participant FI as FileInspector
    participant SP as SheetPipeline
    participant FP as FramePipeline
    participant QA as QAEngine
    participant EX as ExportEngine
    participant MF as ManifestWriter

    U->>UI: Select Sticker Sheet
    UI->>JC: start_job(source, config)
    JC->>FI: inspect + fingerprint
    FI-->>JC: FileInspection
    JC->>SP: detect layout + split
    SP-->>JC: extracted frames
    loop each frame
        JC->>FP: process(frame)
        FP-->>JC: FrameResult + artifact
        JC->>QA: validate(frame result)
        QA-->>JC: PASS/AUTO_FIXED/REVIEW/FAIL
        alt PASS or AUTO_FIXED
            JC->>EX: export PNG
            EX-->>JC: output reference
        else REVIEW
            JC-->>UI: enqueue review
        else FAIL
            JC-->>UI: report failure
        end
    end
    JC->>MF: write manifest/evidence
    MF-->>JC: manifest path
    JC-->>UI: job summary
```

## 2. Transparent Frame Sequence

```mermaid
sequenceDiagram
    participant FP as FramePipeline
    participant BD as BorderDetector
    participant MD as MetadataDetector
    participant AR as AlphaRouter
    participant CA as ContentAnalyzer
    participant SF as SmartFit

    FP->>BD: detect border
    BD-->>FP: detection + confidence
    FP->>FP: remove only if safe
    FP->>MD: detect frame number
    MD-->>FP: metadata candidate/confidence
    FP->>FP: remove only if safe
    FP->>AR: analyze alpha
    AR-->>FP: meaningful transparency = true
    Note over FP,AR: Background removal is skipped
    FP->>CA: analyze content
    CA-->>FP: bbox/edge evidence
    FP->>SF: fit to target canvas
    SF-->>FP: fitted RGBA
```

## 3. Opaque Frame Sequence

```mermaid
sequenceDiagram
    participant FP as FramePipeline
    participant AR as AlphaRouter
    participant BC as BackgroundClassifier
    participant PS as ProviderSelector
    participant BP as BackgroundProvider
    participant QA as MaskSafetyValidator

    FP->>AR: analyze alpha
    AR-->>FP: no meaningful transparency
    FP->>BC: classify background
    BC-->>FP: uniform/near-uniform/complex + evidence
    FP->>PS: select provider
    PS-->>FP: provider
    FP->>BP: remove background
    BP-->>FP: mask + RGBA + confidence
    FP->>QA: validate mask/content safety
    alt confidence sufficient
        QA-->>FP: PASS
    else ambiguous
        QA-->>FP: REVIEW
    end
```

## 4. REVIEW Sequence

```mermaid
sequenceDiagram
    participant JC as JobController
    participant UI as Review UI
    actor U as Operator
    participant KR as Optional Krita
    participant QA as QAEngine

    JC->>UI: frame + findings + before/after/mask
    UI-->>U: show review evidence
    alt Approve safe result
        U->>UI: approve
        UI->>QA: revalidate approved artifact
    else Retry with override
        U->>UI: set permitted override
        UI->>JC: retry stage with recorded override
        JC->>QA: revalidate
    else Manual edit
        U->>UI: open in Krita
        UI->>KR: open working copy
        KR-->>UI: corrected artifact
        UI->>QA: revalidate
    else Reject
        U->>UI: reject frame
        UI->>JC: mark FAIL/REVIEW unresolved
    end
```

## 5. Resume/Recovery Sequence

```mermaid
sequenceDiagram
    actor U as Operator
    participant JC as JobController
    participant MF as ManifestStore
    participant FS as ArtifactStore

    U->>JC: resume(job_id)
    JC->>MF: load manifest
    MF-->>JC: source hash/config/version/stage states
    JC->>JC: validate source identity
    JC->>FS: validate existing artifacts
    loop incomplete or invalid stage
        JC->>JC: re-run stage from clean upstream artifact
    end
    JC->>MF: append recovery evidence
    JC-->>U: resumed job status
```

## Sequence Rule
All destructive or state-changing operations must return explicit evidence and must not be considered successful solely because no exception was raised.
