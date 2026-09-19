# MTKrita Tier-B Transparent Corpus Evidence

## Status
Verification Evidence — Tier-B Transparent Corpus Diagnostic v1.0

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
- extraction confidence: 0.97

This remains within the current deterministic scaled-grid safety contract.

## Diagnostic Method
The current PR #11 border, metadata and joint-planning contracts were reproduced in an isolated read-only harness against the exact Candidate A/B bytes. No source image was mutated and no corpus image was committed to the repository.

This diagnostic is a hardening/evidence run, not owner acceptance and not a substitute for the final integrated acceptance run after the resulting defects are fixed.

## Current-Head Result
The current contract safely routes all 20 representative frames to REVIEW before destructive cleanup.

### Candidate A
- 10 frames inspected
- 8 frames stop at `BORDER.LOW_CONFIDENCE`
- 2 frames pass the border threshold but stop because metadata association remains unresolved after approved border exclusion
- automatic destructive joint cleanup accepted: 0 / 10

### Candidate B
- 10 frames inspected
- 2 frames stop at `BORDER.LOW_CONFIDENCE`
- 5 frames pass border threshold but metadata association remains unresolved after exclusion
- 3 frames isolate a joint-only anchored metadata candidate, but metadata confidence remains below the automatic threshold
- automatic destructive joint cleanup accepted: 0 / 10

## Safety Finding
The current implementation is conservative: no evidence from this diagnostic indicates a silent automatic deletion path. The dominant failure mode is over-review, not unsafe auto-acceptance.

Therefore the correct response is to improve evidence quality and topology modeling, not lower automatic safety thresholds.

## Tier-B Finding TB-001 — Rounded Border Confidence Distortion
The current inset-border candidate coverage divides matching border-color pixels by the entire strip length. Transparent pixels expected at rounded corners therefore reduce the same value later used as confidence, even though transparent-corner support and visible-pixel color purity are different evidence dimensions.

Required refinement:
- retain a minimum visible-support requirement;
- calculate visible border-color purity against visible samples rather than all strip positions;
- keep multi-side color/geometry consensus and contiguous band evidence mandatory;
- do not lower the existing automatic policy threshold merely to pass the corpus;
- record visible-support and visible-color-purity as separate measurements.

## Tier-B Finding TB-002 — Pre-Exclusion Raw Topology Is Too Broad
The current raw metadata candidate topology can include badge, decorative border and unrelated sticker artwork in one connected component before border exclusion. Requiring every fragment from that pre-exclusion raw group to remain inside the corner anchor causes valid badge candidates to be rejected even when the approved border exclusion cleanly isolates them from remote artwork.

Required refinement:
- destructive ownership is determined from post-exclusion isolation, not raw-group membership alone;
- a selected metadata component or reconstructed local group must be fully contained within the approved anchor envelope;
- if an anchored selected component has any non-excluded path outside the anchor envelope, route REVIEW;
- remote fragments from the same pre-exclusion topology may be ignored only when the approved exclusion mask separates them from the selected candidate;
- ignored/out-of-anchor fragments never enter the metadata mask;
- every associated local secondary fragment must remain bounded, adjacent to the approved exclusion boundary and satisfy reconstructed shape constraints;
- competing anchored local candidates remain REVIEW;
- excluded overlap pixels remain border-owned and are never copied into the metadata deletion mask.

This changes the safety proof from “every raw-group fragment must be metadata” to “the destructive candidate must be demonstrably isolated after approved exclusion.”

## Tier-B Finding TB-003 — Candidate Union Can Inflate Shape Bounds
When remote post-exclusion fragments are incorrectly unioned into a metadata candidate, the candidate bbox can approach the entire metadata search zone, reducing compactness/fill confidence and making a small badge appear structurally weak.

Required refinement:
- shape confidence is computed from the selected isolated local candidate/reconstruction only;
- unrelated remote fragments are retained as evidence but excluded from candidate shape scoring and deletion scope;
- exclusion-overlap pixels may contribute only to analysis-only shape evidence under ADR-028 rules;
- automatic confidence thresholds remain unchanged.

## Mandatory New Regression Cases
Before production behavior changes:
1. rounded inset border with transparent corner pixels and high visible color purity;
2. rounded inset border with insufficient visible support → REVIEW;
3. badge and remote artwork share one pre-exclusion raw topology only through the approved border mask; post-exclusion badge is isolated → remote artwork preserved;
4. selected anchored fragment still has a non-excluded path outside anchor → REVIEW;
5. multiple isolated anchored fragments that form competing plausible badges → REVIEW;
6. post-exclusion local reconstruction must not copy excluded border pixels into metadata mask;
7. no threshold reduction from the currently approved policy.

## Gate Status
**M2 Tier-B: NOT YET ACCEPTED.**

Reason: the implementation is safe but over-conservative on the representative corpus. Evidence-backed refinements TB-001 through TB-003 must be implemented with synthetic regression coverage, Windows CI must remain green, and Candidate A/B must be rerun on the integrated head.

## Repository Safety
- candidate source bytes remain outside Git history;
- only hashes, dimensions, aggregate measurements and defect evidence may be versioned by default;
- temporary diagnostic outputs remain outside tracked runtime/source directories;
- no production threshold is changed without SSOT + regression evidence.

References: `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, ADR-023, ADR-028, Issue #12, PR #11.
