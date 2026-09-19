# Image Processing Pipeline

## Mode Selection

```text
INPUT
  ↓
Inspect channels + alpha
  ├─ meaningful alpha → TRANSPARENT pipeline
  ├─ alpha but fully opaque → OPAQUE pipeline
  └─ no alpha → OPAQUE pipeline
```

User may override `AUTO` selection.

## Transparent Pipeline
1. Load image losslessly
2. Validate alpha statistics
3. Detect/extract frame
4. Remove sheet-only borders when confidence is high
5. Build foreground mask from alpha
6. Remove tiny isolated noise components
7. Compute content bounds
8. Check edge collisions
9. Smart fit / recenter when allowed
10. Validate export profile
11. Export RGBA PNG
12. Emit QA findings

## Opaque Pipeline
1. Load RGB image
2. Extract frame
3. Classify background: uniform / near-uniform / complex
4. Build foreground mask
5. Refine mask and preserve anti-aliased edges
6. Estimate mask confidence
7. Low confidence → `REVIEW`
8. Convert foreground to RGBA
9. Compute content bounds
10. Smart fit
11. QA
12. Export transparent PNG

## Background Removal Strategy Order
Use deterministic and inexpensive methods first:
1. exact/tolerance color key
2. border-sampled background model
3. flood-fill / connected background
4. GrabCut-like segmentation
5. optional AI segmentation adapter in a later phase

## Smart Fit Rules
- preserve all foreground content
- preserve semi-transparent edges
- keep aspect ratio
- never distort
- no rotation unless configured
- scale down if needed
- scale up only when explicitly allowed
- center using geometry or visual centroid

## Failure Philosophy
**REVIEW is preferable to a destructive guess.**

If foreground/background classification is uncertain, the engine must not silently delete pixels or crop visible artwork.
