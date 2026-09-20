# MTKrita Closed-Ring Border Topology Specification

## Status
SSOT Extension — TB-007 Closed Decorative Ring Contract v1.0

## Purpose
Define a topology-first fallback for transparent sticker sheets whose decorative frame is a closed rounded ring around the artwork.

Representative Candidate B shows that several remaining M2 REVIEW cases are not fundamentally color-classification problems. The border is a closed geometric structure with multiple tones, highlights, shadows and antialiasing. Repeated side-strip color ownership becomes unnecessarily complex and can confuse inner artwork with deeper border layers.

TB-007 therefore models the frame as an **enclosing closed ring in alpha topology**, with color retained as evidence but not as the primary ownership proof.

## Product Mapping
TB-007 advances UC-03, UC-04, UC-05 and UC-06 by providing a safer general solution for transparent rounded/multi-tone decorative frames.

## Representative Observation
Candidate B frames such as B1 and B7 visibly contain:
- transparent source outside the frame;
- a rounded rectangular decorative ring close to all four frame edges;
- an enclosed interior region containing character/text/artwork;
- multiple border tones that change by side and depth;
- a top-left frame-number badge that may touch or overlap the ring.

This topology is stronger evidence than one-color strip purity.

## Locked Safety Rules
TB-007 SHALL preserve:
- `REVIEW > destructive guess`;
- source immutability;
- existing bounded near-edge search domain derived from `max_fraction` / `max_search`;
- no global color-key deletion;
- no widening of global color tolerance;
- no corpus/frame-index special cases;
- no removal of arbitrary perimeter-connected artwork;
- metadata remains JointCleanupPlanner-owned;
- TB-005 ambiguous consensus remains REVIEW unless TB-007 independently proves a complete ring under this contract;
- planner-first representative validation before FramePipeline mutation authority.

## Core Model
A closed decorative border candidate consists of:

1. an outer visible contour close to the frame perimeter;
2. a corresponding inner hole/enclosed contour;
3. a ring region between those contours;
4. four-side near-edge support;
5. bounded ring thickness/geometry;
6. a central enclosed region large enough to plausibly contain sticker artwork;
7. no unexplained inward branch that violates ring ownership policy.

The candidate is geometric/topological. It may contain multiple colors.

## Transparent-Source Scope
Phase 1 applies only to meaningfully transparent source frames where alpha provides reliable foreground topology.

Opaque frames remain M3-owned.

## Contour / Hierarchy Evidence
A provider may use OpenCV contour hierarchy or an equivalent deterministic topology method.

Candidate discovery should use the alpha-visible mask (`alpha > existing visibility threshold`) and `RETR_TREE` / equivalent hierarchy so a closed border ring can be represented by an outer contour and an inner hole.

Required evidence includes:
- outer contour bbox/area/perimeter;
- inner contour bbox/area/perimeter;
- hierarchy relationship;
- distance of outer bbox from each frame edge;
- distance of inner bbox from each frame edge;
- ring pixel count / area ratio;
- ring thickness samples by side;
- four-side support;
- contour closure status;
- inward-branch / irregularity evidence;
- deterministic mask hash when a candidate mask is built.

## Near-Edge Eligibility
The outer contour must be a perimeter-scale structure:
- its bbox must approach all four frame edges within the existing `max_search` domain;
- it must span a large fraction of both frame width and frame height;
- it must not be a small corner badge or isolated artwork component.

Exact acceptance bounds SHALL be explicit in implementation/tests and remain conservative.

## Inner-Hole Eligibility
A valid ring requires an enclosed inner region:
- inner contour is a hierarchy child/hole of the outer ring topology;
- inner bbox lies inside the outer bbox;
- inner area is materially larger than metadata badges/noise;
- inner region covers the main artwork zone rather than a small decorative hole;
- inner contour is not fragmented into multiple competing large holes without a deterministic dominant candidate.

Multiple plausible enclosing holes cause REVIEW.

## Ring Mask Rule
The ring cleanup mask is the spatial region between the approved outer and inner contours, intersected with visible source pixels.

Important:
- do not delete the entire connected component;
- do not fill the entire outer bbox;
- do not global-key any ring color;
- pixels inside the approved inner contour are preserved even if connected to the ring elsewhere;
- pixels outside the outer contour remain unchanged;
- mask construction must be deterministic.

This spatial rule is designed to avoid absorbing a touching frame-number badge or interior artwork merely because it shares connectivity/color with the ring.

## Metadata Overlap
If a frame-number badge overlaps the ring:
- TB-007 ring mask remains border-owned only;
- metadata detection may use the exact ring mask as analysis exclusion;
- excluded ring pixels are not copied into metadata deletion ownership;
- JointCleanupPlanner retains exact mask identity and final overlap authority;
- badge pixels inside the inner contour remain available to metadata detection/removal.

## Inward Branch / Artwork Contact Safety
A closed component can still have artwork attached to it. Therefore a closed contour alone is insufficient.

Automatic ring authority requires bounded geometry evidence showing that the proposed ring region remains a perimeter band rather than extending deeply into the enclosed artwork region.

At minimum:
- side thickness samples stay within a conservative spread;
- ring mask has no large inward protrusion beyond the approved inner contour geometry;
- inner contour remains a coherent enclosing boundary;
- suspicious branches/protrusions outside the ring envelope cause REVIEW.

Phase 1 may use a robust per-side thickness statistic and maximum-deviation bound. Bounds must be regression-driven and must not be weakened to force corpus acceptance.

## Candidate Selection
If multiple closed-ring candidates exist:
- rank only by deterministic topology criteria;
- require a dominance margin between plausible perimeter-scale rings;
- otherwise REVIEW;
- never select based on filename/frame index/corpus identity.

## Cleanup Authority
Phase 1 implementation SHALL initially be planner-only and return:

```text
ClosedRingPlan
- status: NO_RING | SAFE_RING | REVIEW
- outer_bbox
- inner_bbox
- outer_contour_area
- inner_contour_area
- ring_mask_ref/hash
- ring_pixel_count
- side_thickness_samples
- thickness_spread
- four_side_support
- hierarchy_evidence
- reasons[]
```

Only after representative planner acceptance may `SAFE_RING` become a BorderDetection/cleanup authority for transparent FramePipeline.

## Required Synthetic Regression Matrix
Before integrated mutation:

1. rounded closed single-tone ring → SAFE_RING;
2. rounded closed multi-tone ring → SAFE_RING without global color tolerance widening;
3. closed ring with transparent outer padding → SAFE_RING;
4. broken/open border → REVIEW/NO_RING;
5. near-edge artwork without closed inner hole → NO_RING/REVIEW;
6. small corner badge with hole → not perimeter-scale ring;
7. two competing perimeter-scale rings → REVIEW unless deterministic dominance is proven;
8. ring plus badge touching top-left → ring mask excludes badge interior ownership;
9. ring plus deep artwork branch crossing inner boundary → REVIEW;
10. highly incoherent thickness/protrusion → REVIEW;
11. deterministic repeat produces identical contour choice and mask hash;
12. source pixels remain immutable;
13. TB-001 through TB-006 regressions remain green.

## Tier-B Acceptance Procedure
After Windows Ruff + pytest:
1. run planner-only against hash-matched Candidate A/B refined frames;
2. record SAFE/REVIEW/NO_RING by frame;
3. visualize/inspect every SAFE ring mask overlay;
4. verify mask removes decorative ring but preserves character/text/badge/artwork;
5. reject any false-safe ring candidate;
6. only then integrate SAFE_RING into transparent FramePipeline;
7. rerun full A/B pipeline and visually inspect every new automatic output;
8. compute auto-process/review/false-safe/visual-acceptance KPIs;
9. keep M2 open until representative behavior is practically useful.

## Relationship to TB-006 Class B
TB-006 Class-B side/depth planners remain useful diagnostic evidence but SHALL NOT automatically become production authority if TB-007 provides a simpler, safer closed-ring proof for the same archetype.

After TB-007 representative acceptance, redundant experimental production paths should be removed or retained only as explicitly non-production diagnostic modules to keep the repository clean.

## Non-Goals
TB-007 does not implement opaque-background removal, general semantic segmentation, UI business logic or arbitrary contour deletion.

## Repository Hygiene
Representative source images and generated masks/overlays remain outside Git history. Only SSOT, provider code, synthetic tests and summarized evidence are versioned.

References: `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `68_BORDER_CONTACT_TOPOLOGY_SPEC.md`, `69_USE_CASE_ACCEPTANCE_MATRIX.md`, `70_BORDER_BAND_COMPLETION_SPEC.md`, `71_BORDER_BAND_CORROBORATION_REFINEMENT_SPEC.md`, `72_BORDER_BAND_DEPTH_TOPOLOGY_SPEC.md`, ADR-028, Issue #12, PR #11.
