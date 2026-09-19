# MTKrita M2/M3 Implementation Plan

## Status
SSOT — Near-Term Engineering Plan v1.0

## Purpose
กำหนดลำดับการพัฒนา M2 และ M3 ให้ทีมสามารถทำงานต่อเนื่องโดยไม่ข้าม dependency หรือ quality gate

## M2 Target
Deliver the transparent-processing baseline from sheet input through PNG output with traceable evidence and safe metadata/border handling.

## M2 Recommended Order
1. stabilize exact + hybrid grid extraction
2. harden border detection/removal
3. harden frame-number metadata removal
4. finalize transparency router
5. implement `FramePipeline` orchestration
6. integrate content analysis + smart fit
7. integrate QA findings / `FrameResult`
8. integrate manifest/output lineage
9. run acceptance matrix on transparent corpus
10. pass CI and M2 gate

## M2 Integration Contract
```text
SheetInput
 -> inspect
 -> detect/split
 -> FramePipeline(frame)
      -> border
      -> metadata
      -> transparency route
      -> [skip background]
      -> content
      -> fit
      -> QA
      -> export
 -> manifest
```

## M2 Exit Evidence
- AT-SPLIT suite
- AT-BORDER suite
- AT-META suite
- AT-ROUTE suite
- core AT-QUAL
- AT-EVID lineage
- CI green
- no unresolved Critical defects

---

## M3 Target
Add safe opaque-background conversion to transparent RGBA without unsafe foreground deletion.

## M3 Recommended Order
1. define `BackgroundRemovalProvider` interface
2. implement background classifier
3. implement edge-sampling model
4. implement edge-connected / flood-fill provider
5. add mask refinement
6. add confidence + REVIEW policy
7. optional GrabCut-style fallback behind provider interface
8. integrate with transparency router/orchestrator
9. run opaque archetype corpus
10. run mixed transparent/opaque E2E
11. pass M3 gate

## M3 Processing Strategy Order
Deterministic strategies are attempted before complex fallback:
```text
opaque frame
  -> classify background
  -> high-confidence uniform/near-uniform
      -> edge-connected deterministic removal
  -> insufficient confidence
      -> supported advanced provider if configured
  -> still ambiguous
      -> REVIEW
```

## M3 Safety Invariants
- never globally delete black just because background is black
- preserve disconnected dark hair/text/props
- preserve white/semitransparent sticker outline
- no segmentation when meaningful transparency already exists unless explicit override
- ambiguous mask = REVIEW

## Parallel Work Allowed
While image-processing implementation proceeds, independent work may continue on:
- golden corpus curation
- manifest schema/evidence tooling
- Windows packaging experiments
- UI wireframes/prototypes that do not redefine domain behavior
- documentation/audit readiness

## Parallel Work Not Allowed Without Coordination
- changing `FrameResult` schema while pipeline integration is active
- changing stage order outside approved SSOT
- changing provider contracts independently on multiple branches
- changing export profile rules without requirement/traceability update

## Integration Checkpoints
### CP-1 Geometry Stable
Grid split behavior + tests stable.

### CP-2 Destructive Cleanup Stable
Border + metadata removal safety tests stable.

### CP-3 Transparent E2E Stable
FramePipeline + manifest + export pass transparent corpus.

### CP-4 Opaque Provider Stable
Background removal provider passes isolated opaque tests.

### CP-5 Mixed E2E Stable
Transparent and opaque sheets route correctly in one build.

## Branch / PR Recommendation
- keep one coherent work package per PR where practical
- avoid mega-PRs combining architecture, algorithm, GUI and packaging
- every PR references WP ids + requirement ids + acceptance test ids

## Completion Rule
M2/M3 are complete only when implementation + automated evidence + traceability + SSOT synchronization all agree.
