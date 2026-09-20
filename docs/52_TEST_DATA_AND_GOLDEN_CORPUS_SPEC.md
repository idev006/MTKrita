# MTKrita Test Data and Golden Corpus Specification

## Status
SSOT — Verification Corpus Baseline v1.1

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

## Evidence Tiers

### Tier A — Synthetic Deterministic Gate
Generated fixtures may prove deterministic contracts, stage order, provenance, export lineage and regression behavior without storing user artwork.

M2 includes an automated synthetic 10-frame end-to-end gate covering:
- 2×5 deterministic split
- border removal
- frame-metadata removal
- pre-metadata source transparency provenance
- smart fit / validation
- atomic PNG export + SHA-256
- manifest population
- source immutability

Synthetic evidence is mandatory automated CI evidence, but it does **not** replace production-image acceptance.

### Tier B — Approved Production/Representative Corpus
Representative real-world or owner-approved artifacts prove that algorithms generalize to production characteristics. These cases require reviewer approval and stable case metadata/hashes.

A milestone requiring an "approved corpus" is not fully closed solely because Tier A passes when Tier B is explicitly required by its exit criteria.

## Golden Case Record
Each production/representative case must include:
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
- cleanup-generated alpha does not redefine source transparency routing
- same/near-border-color artwork contact prevents destructive auto-crop

## Regression Rule
Every Critical/High defect fixed must add a regression case before closure.

## Corpus Versioning
Corpus metadata must be version-controlled. Large binary fixtures may be stored in a dedicated test-data location, but hashes and case manifests remain in repository SSOT/evidence.

## M2 Minimum Corpus
Tier A automated synthetic 5×2 gate plus Tier B approved transparent cases covering border variants, metadata variants, alpha routing and edge-contact safety.

## M3 Minimum Corpus
Opaque black archetype, white/color backgrounds, near-uniform backgrounds, dark foreground preservation, ambiguous masks, mixed transparent/opaque batch.

References: `23_SUPPORTED_INPUT_ARCHETYPES.md`, `40_ACCEPTANCE_TEST_MATRIX.md`, `14_SOFTWARE_TEST_STRATEGY.md`, ADR-023.
