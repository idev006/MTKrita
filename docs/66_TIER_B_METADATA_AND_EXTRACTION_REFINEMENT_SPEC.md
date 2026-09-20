# MTKrita Tier-B Metadata and Extraction Refinement Specification

## Status
SSOT Extension — Tier-B Refinement Contract v1.0

## Purpose
Define the evidence-backed refinements discovered by Tier-B Candidate A/B after TB-001 and TB-002. This document extends the S-03 extraction and S-06 metadata contracts without weakening existing safety thresholds.

## Scope
This specification covers:
- TB-003 — transparency-aware metadata candidate segmentation;
- TB-004 — bounded visual separator refinement for configured 5×2 sheets.

It does **not** change:
- ADR-023 source-transparency provenance;
- ADR-028 joint cleanup authority;
- `REVIEW > destructive guess`;
- automatic border/metadata thresholds;
- MainBoard / worker / final-commit authority.

# TB-003 — Transparency-Aware Metadata Candidate Segmentation

## Problem
Meaningfully transparent Sticker Sheets already encode foreground/background separation in alpha. The current metadata detector can nevertheless infer RGB background color from visible frame-edge pixels. If those visible pixels belong to a decorative border, the border color becomes the inferred RGB background and valid frame-number badge support can be merged, suppressed or scored incorrectly.

## Contract
For an extracted frame with meaningful source transparency:
1. metadata raw candidate support shall use visible-alpha topology as the primary foreground signal;
2. a pixel is raw visible support when alpha exceeds the configured visibility threshold;
3. approved spatial border masks may be removed from this raw topology for analysis only;
4. deletion authority still requires anchor/local-envelope, area, compactness, dominance and completeness evidence;
5. non-anchored alpha-visible artwork remains preserved;
6. excluded border-overlap pixels remain border-owned and are not copied into metadata deletion masks;
7. source transparency provenance is captured before destructive cleanup and is never re-derived from cleanup output.

For an effectively opaque frame:
- conservative RGB/background-distance segmentation remains the fallback candidate source until M3 supplies a stronger provider;
- metadata planning may be retained as evidence but must not create alpha before opaque background removal.

## Detection Evidence
Metadata evidence shall record the segmentation basis:
- `metadata_segmentation_basis = alpha_visible | rgb_background_distance`;
- alpha visibility threshold when `alpha_visible` is used;
- existing exclusion/fragment/association evidence;
- selected bbox, area/fill/compactness, anchor distance, dominance margin and confidence.

## Prohibited
- treating every alpha-visible component in the broad metadata zone as metadata;
- lowering metadata auto threshold because alpha topology is available;
- filling the full anchor/search box;
- copying excluded border pixels into metadata mask;
- using cleanup-generated alpha to choose the source route.

## Required Regression Tests
1. transparent frame with border-colored visible edges and a valid top-left badge → badge remains detectable;
2. transparent frame with non-anchored artwork in search zone → artwork is preserved;
3. transparent badge separated from remote artwork only by approved border exclusion → local ownership rules still apply;
4. opaque input retains RGB fallback segmentation;
5. segmentation-basis evidence is deterministic and propagated to `FrameResult`.

# TB-004 — Bounded Visual Separator Refinement

## Problem
A 5×2 sheet can satisfy proportional cell-width variation ≤1 px while rendered frame borders/gutters are not aligned exactly with proportional boundaries. Candidate B demonstrates neighboring-frame pixels entering some extracted cells even though the current configured-scaled geometry reports confidence 0.97.

## Contract
Configured proportional geometry remains the initial deterministic hypothesis. When a known visual frame structure exists, final extraction confidence shall include bounded separator evidence.

A refinement provider/service may:
1. search only within a configured small window around predicted internal row/column separators;
2. score transparent gutter evidence, border-line valleys/peaks or equivalent deterministic separator signals;
3. require agreement across multiple rows/columns when applicable;
4. choose the best separator only when its dominance over alternatives meets policy;
5. crop directly from source pixels using the refined integer boundaries;
6. preserve source bytes and avoid resampling.

If separator evidence is absent or ambiguous:
- retain the original prediction only if the profile explicitly permits geometry-only extraction for that archetype;
- otherwise route REVIEW;
- never silently widen a frame into neighboring artwork.

## Extraction Evidence
Record at minimum:
- predicted separator positions;
- refined separator positions when changed;
- per-separator offset from prediction;
- search-window size;
- separator score and dominance/confidence;
- extraction method identifier;
- final source rectangles.

## Required Regression Tests
1. exact divisible 5×2 sheet → no refinement change;
2. uniformly scaled sheet with separator aligned to proportional prediction → deterministic current behavior retained;
3. visual separator shifted within bounded window → refined boundary selected;
4. neighboring-frame contamination is removed by refinement;
5. competing/weak separator candidates → REVIEW;
6. no resampling introduced;
7. repeated execution produces identical rectangles/evidence.

# Gate Rules
TB-003 and TB-004 are independent checkpoints.

TB-003 may be merged/verified before TB-004 if:
- regression suite remains green;
- Tier-B diagnostics improve without threshold relaxation;
- no new destructive acceptance appears without evidence.

M2 Tier-B cannot close until:
- Candidate A/B are rerun on the integrated head after both refinements;
- no Critical silent-content-loss defect exists;
- supported frames clean decorative border/metadata as intended;
- ambiguous frames remain REVIEW;
- owner acceptance evidence is recorded.

## Repository Hygiene
- production/user Candidate A/B bytes remain outside Git history;
- synthetic fixtures are preferred for regressions;
- only hashes/measurements/evidence may be committed by default;
- experimental scripts/results remain outside tracked source/runtime paths;
- no duplicate production detector path is retained after a refinement is accepted.

References: `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`, ADR-023, ADR-028, Issue #12, PR #11.
