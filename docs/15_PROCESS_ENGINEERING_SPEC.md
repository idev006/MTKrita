# Process Engineering Specification

## Production Objective
เปลี่ยน Sticker Sheet เป็น LINE-ready sticker assets ด้วย flow ที่ repeatable, measurable และลด manual touch โดยไม่แลกกับ content safety

## Canonical Process

```text
INGEST
  → INSPECT
  → SHEET ANALYSIS
  → SPLIT
  → PER-FRAME BORDER ANALYSIS
  → BORDER REMOVE / KEEP / REVIEW
  → TRANSPARENCY OR BACKGROUND PIPELINE
  → CONTENT BOUNDS
  → SMART FIT
  → QUALITY CHECK
  → AUTO-FIX (safe only)
  → RE-QA
  → EXPORT
  → MANIFEST / REPORT
```

## Process States
Job: `RECEIVED`, `PROCESSING`, `REVIEW_REQUIRED`, `COMPLETED`, `FAILED`
Frame: `PASS`, `AUTO_FIXED`, `REVIEW`, `FAIL`

## Stage Contracts
Each stage receives immutable input/reference plus config and returns:
- output artifact/reference
- measurements
- confidence
- actions performed
- findings/errors

No stage may silently mutate source data.

## Adaptive Border Removal Stage
Runs **after frame split**.

### Inputs
- extracted frame
- expected safe edge region
- optional sheet separator hints

### Outputs
- border mask
- thickness estimate per side
- representative color/range
- continuity and rectangularity measures
- artwork-contact risk
- confidence
- action: `REMOVE`, `KEEP`, `REVIEW`

### Removal Rule
Removal should target only pixels classified as structural frame border. The post-removal artifact is re-analyzed for content loss and edge anomalies before continuing.

## Transparent Mode
Prefer alpha as the strongest foreground evidence. Structural border may still exist as opaque pixels and therefore requires its own border stage.

## Opaque Mode
Background removal happens after structural border handling. A border is not automatically equivalent to background.

## Rework Loop
`REVIEW → manual correction → re-import → re-QA`. Manual correction must be associated with job/frame identity.

## Process KPIs
- first-pass yield
- auto-fix yield
- review rate
- fail rate
- false-pass rate
- manual minutes per 40 stickers
- average processing time per sheet
- rework count

## Continuous Improvement
Thresholds may be tuned only against a controlled corpus with before/after metrics. Any threshold change affecting classification behavior requires regression testing.