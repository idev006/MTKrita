# MTKrita Test Data and Golden Corpus Specification

## Status
SSOT — Verification Corpus Baseline v1.0

## Purpose
กำหนดชุดข้อมูลทดสอบอ้างอิงที่ใช้พิสูจน์ correctness, safety และ regression ของ pipeline

## Corpus Classes
1. Transparent sheets — meaningful alpha, no background removal
2. Opaque uniform sheets — black/white/color backgrounds
3. Near-uniform/gradient sheets
4. Border variants — color, thickness, AA, rounded, interrupted
5. Metadata variants — frame number present/absent/ambiguous
6. Content-risk cases — black hair/text/shadow, white outline, edge contact
7. Geometry variants — exact 5x2, resized/non-divisible, margins/gaps
8. Failure inputs — corrupt PNG, unsupported mode, incomplete files
9. Reliability cases — interrupted jobs, stale attempts, retry/resume

## Golden Case Record
Each case must include:
- case_id
- source artifact hash
- archetype
- expected frame count/order
- expected route per frame
- expected status/findings
- protected content notes
- expected output constraints
- approved reviewer/date

## Golden Output Policy
Pixel-perfect comparison is required only where deterministic and stable. For segmentation/AA-sensitive stages use measurable invariants and approved masks/bounds/tolerances.

## Mandatory Safety Assertions
- source unchanged
- no unexpected foreground deletion
- no global black deletion
- frame number removal does not erase artwork numbers
- transparent inputs bypass background segmentation
- no default upscale
- final output traceable to source/config/provider versions

## Regression Rule
Every Critical/High defect fixed must add a regression case before closure.

## Corpus Versioning
Corpus metadata must be version-controlled. Large binary fixtures may be stored in a dedicated test-data location, but hashes and case manifests remain in repository SSOT/evidence.

## M2 Minimum Corpus
Transparent 5x2, border variants, metadata variants, alpha routing, edge-contact cases.

## M3 Minimum Corpus
Opaque black archetype, white/color backgrounds, near-uniform backgrounds, dark foreground preservation, ambiguous masks, mixed transparent/opaque batch.

References: `23_SUPPORTED_INPUT_ARCHETYPES.md`, `40_ACCEPTANCE_TEST_MATRIX.md`, `14_SOFTWARE_TEST_STRATEGY.md`.
