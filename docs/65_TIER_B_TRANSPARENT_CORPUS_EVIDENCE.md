# MTKrita Tier-B Transparent Corpus Evidence

## Status
Verification Evidence — Tier-B Transparent Corpus Diagnostic v1.1

## Purpose
Record production/representative transparent-sheet evidence without committing user/source image bytes. This document captures observed behavior of the current PR #11 detector/planner contracts and the evidence-backed hardening work required before M2 acceptance can close.

## Corpus Identity
Two owner-available representative transparent Sticker Sheets were matched exactly to the hashes already recorded in Issue #12.

### Candidate A
- logical name: `Thai-Inspired Blessings Sticker Sheet.png`
- SHA-256: `4e86ac089a8342ac2c7a3ab985c7e2b41deb091601297c9b2fa55777ceb4e906`
- dimensions: 1986 × 792
- mode: RGBA
- layout: 2 rows × 5 columns
- meaningful source transparency: yes
- source bytes: not committed

### Candidate B
- logical name: `Thai Elderly Woman Blessing Sticker Sheet.png`
- SHA-256: `13e8755ef4056bf04021ee8e86c733fa883f5617bb6a6ad02bc12e74d08c84d8`
- dimensions: 1976 × 796
- mode: RGBA
- layout: 2 rows × 5 columns
- meaningful source transparency: yes
- source bytes: not committed

## Extraction Evidence
Both sheets use the known 5×2 layout but are not exactly divisible in width.

Using the current controlled proportional extraction contract:
- Candidate A frame widths: 397 / 397 / 398 / 397 / 397 px; frame height 396 px
- Candidate B frame widths: 395 / 395 / 396 / 395 / 395 px; frame height 398 px
- maximum cell-width variation: 1 px
- extraction method: `configured_scaled`
- nominal extraction confidence: 0.97

The proportional geometry is deterministic, but the second Tier-B run shows that a low cell-width variation alone does **not** prove separator alignment against the rendered decorative frame. Candidate B frames 3–4 contain evidence of neighboring-frame pixels at the right crop boundary. This is now tracked separately as TB-004 rather than being misclassified as a border-detector failure.

## Diagnostic Method
The current PR #11 border, metadata and joint-planning contracts were reproduced in an isolated read-only harness against the exact Candidate A/B bytes. No source image was mutated and no corpus image was committed to the repository.

This diagnostic is a hardening/evidence run, not owner acceptance and not a substitute for the final integrated acceptance run after the resulting defects are fixed.

## Baseline Before TB-001 / TB-002
Before the evidence refinements:

### Candidate A
- 10 frames inspected
- 8 frames stopped at `BORDER.LOW_CONFIDENCE`
- 2 frames passed the border threshold but metadata association remained unresolved
- automatic destructive joint cleanup accepted: 0 / 10

### Candidate B
- 10 frames inspected
- 2 frames stopped at `BORDER.LOW_CONFIDENCE`
- 5 frames passed border threshold but metadata association remained unresolved
- 3 frames isolated a joint-only candidate but metadata confidence was below threshold
- automatic destructive joint cleanup accepted: 0 / 10

The baseline failure mode was over-review, not silent destructive acceptance.

## Verified Hardening Checkpoints

### TB-001 — Rounded Border Evidence
Implemented and Windows-CI verified:
- visible support is separated from visible color purity;
- transparent rounded corners no longer count as wrong-color pixels;
- minimum support, multi-side consensus and contact-risk policy remain mandatory;
- automatic threshold remains unchanged;
- `visible_support` and `color_purity` are carried as evidence.

### TB-002 — Post-Exclusion Local Metadata Ownership
Implemented and Windows-CI verified:
- destructive ownership is based on post-exclusion local isolation rather than raw-group membership alone;
- anchor center remains 60% of the metadata search zone;
- local candidate extent may occupy up to 90% of the search zone while remaining locally bounded;
- remote fragments separated only by the approved border exclusion are preserved and counted as evidence;
- remote pixels never enter the metadata deletion mask;
- selected components with a non-excluded path beyond the local envelope remain REVIEW;
- `ignored_remote_fragment_count` is propagated into frame evidence.

Windows CI #324 at commit `cd63c20b8b0f8f829481dcfc92555ce5e7254246` passed Ruff + pytest.

## Second Tier-B Run After TB-001 / TB-002

### Candidate A
- border automatic-confidence gate: 10 / 10 frames pass
- border contact risk localized: 10 / 10 frames
- metadata candidate reaches current joint-planning eligibility: 4 / 10 frames
- remaining metadata outcomes: unresolved local association and one ambiguity case
- no threshold relaxation used
- no silent destructive bypass observed

### Candidate B
- border automatic-confidence gate: 8 / 10 frames pass
- the two border failures correspond to extraction-boundary contamination rather than proven border-evidence weakness
- metadata candidates ready for current joint auto path: 0 / 10
- several frames report no plausible metadata candidate with confidence around 0.60–0.64
- remaining frames report unresolved local association
- no threshold relaxation used
- no silent destructive bypass observed

## Safety Finding
The current implementation continues to fail closed. Ambiguous or incomplete evidence routes REVIEW. The observed blocker is now evidence quality and extraction fidelity, not an unsafe automatic-deletion path.

## Tier-B Finding TB-003 — Transparent Metadata Segmentation Uses the Wrong Primary Background Evidence
On a meaningfully transparent extracted frame, the current metadata detector still derives an RGB background reference from visible bottom/right edge pixels. In representative sheets those visible edge pixels can belong to the decorative green frame. That makes the border color behave like the inferred “background” and can merge or suppress the actual frame-number badge candidate even though alpha already provides direct foreground/background evidence.

Required refinement:
- when meaningful transparency exists in the metadata analysis region/frame, visible alpha topology (`alpha > configured visibility threshold`) is the primary raw candidate support;
- the approved border mask may still be excluded for connectivity analysis;
- RGB distance-to-background remains a fallback for effectively opaque inputs, not the primary transparent-source segmentation mechanism;
- source transparency provenance remains immutable and is captured before destructive cleanup;
- alpha-visible segmentation does not grant deletion authority by itself; anchor, local extent, compactness, dominance, exclusion identity and joint-planner rules still apply;
- automatic thresholds are not lowered.

Required regression cases:
1. transparent frame + inset green border + top-left badge while edge RGB is dominated by the border → badge remains detectable from alpha topology;
2. transparent frame + non-anchored artwork in the broad zone → artwork is preserved and cannot become metadata merely because it is alpha-visible;
3. opaque frame behavior continues to use conservative RGB/background evidence;
4. analysis exclusion may separate border from badge, but excluded pixels remain border-owned.

## Tier-B Finding TB-004 — Proportional Cell Geometry Does Not Prove Visual Separator Alignment
Candidate B frames 3–4 show neighboring-frame pixels at the right crop edge even though proportional cell widths vary by only 1 px and satisfy the current deterministic scaled-grid check.

Required refinement:
- deterministic configured-scaled geometry remains an initial hypothesis, not sufficient final separator proof for production-like sheets;
- extraction confidence must include separator/border alignment evidence when a visual frame structure exists;
- a bounded refinement stage may search near the predicted separator for consistent transparent gutters / frame-border valleys / multi-row agreement;
- refinement must remain deterministic and bounded around the configured prediction;
- failure to establish separator alignment routes REVIEW rather than silently ingesting neighboring-frame pixels;
- no source resampling is introduced by separator refinement.

TB-004 must be implemented separately from metadata segmentation so extraction and metadata defects remain independently testable.

## Mandatory New Regression Cases
Before the next production behavior changes:
1. transparent alpha-visible badge remains selectable even when visible edge RGB is border-colored;
2. non-anchored alpha-visible artwork is never deleted as metadata;
3. opaque metadata segmentation retains its conservative RGB fallback behavior;
4. scaled 5×2 grid with visual separator shifted from proportional prediction is refined within a bounded search window;
5. ambiguous separator evidence routes REVIEW;
6. no threshold reduction from approved policy.

## Gate Status
**M2 Tier-B: NOT YET ACCEPTED.**

Reason: TB-001 and TB-002 are verified and materially improve Candidate A, but TB-003 metadata segmentation and TB-004 extraction alignment remain evidence-backed blockers. After those fixes, Candidate A/B must be rerun and owner acceptance evidence recorded.

## Repository Safety
- candidate source bytes remain outside Git history;
- only hashes, dimensions, aggregate measurements and defect evidence are versioned by default;
- temporary diagnostic outputs remain outside tracked runtime/source directories;
- no production threshold is changed without SSOT + regression evidence;
- corpus diagnostics are read-only.

References: `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, ADR-023, ADR-028, Issue #12, PR #11.
