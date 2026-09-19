# Joint Border + Metadata Cleanup Specification

## Status
SSOT — Joint Cleanup Safety Contract v1.2

## Decision Record — ADR-028
**Title:** Joint Border/Metadata Cleanup Is Planned Before Destructive Mutation  
**Status:** Accepted

When frame-number metadata touches or overlaps a decorative frame border, MTKrita shall not execute border removal and metadata removal as two independent destructive operations. Detection remains separable, but mutation is authorized only from one combined cleanup plan whose evidence explains the complete contact topology.

This decision extends ADR-005 (Conservative Automation), ADR-008 (Adaptive Border Removal), ADR-023 (Source Transparency Provenance), ADR-024 (Durable Commit Intent), ADR-026 (Worker Results Are Candidates) and ADR-027 (Immutable Staged Inputs).

## Architectural Rule
**Detect independently. Plan jointly. Mutate once.**

```text
Extracted frame
  ↓
Source transparency provenance capture (immutable)
  ↓
Border detection → BorderGeometry/BorderEvidence
  ↓
Metadata detection → MetadataMask/MetadataEvidence
  ↓
JointCleanupPlanner
  ├─ SAFE_PLAN
  └─ REVIEW
  ↓
Apply one approved cleanup plan
  ↓
Content QA / Smart Fit / Export candidate
```

No detector owns final destructive authority in an overlap case.

## Source Transparency Invariant
Source/background routing must be captured from source/extracted-frame alpha state before any cleanup that can create or materially alter alpha. Border/metadata detection may inspect pixels and build masks without changing routing provenance. The combined cleanup result must never be reinterpreted as source transparency evidence.

## Safe Automatic Plan Requirements
Automatic joint cleanup is permitted only when all required conditions hold.

### 1. Strong border evidence
- border has approved multi-side consensus or equivalent strong topology evidence;
- per-side offset/thickness geometry is bounded and internally consistent;
- confidence meets automatic policy;
- visible spatial support and visible-pixel color purity are measured separately for rounded/inset borders;
- transparent pixels expected at rounded corners do not count as wrong-color border pixels;
- insufficient visible support, weak color purity, inconsistent side color or inconsistent band geometry still causes `REVIEW`.

### 2. Strong metadata evidence
- exactly one dominant anchored badge candidate is selected;
- selected destructive candidate is fully bounded to the approved corner-anchor envelope;
- candidate satisfies configured area, compactness and anchor constraints;
- dominance margin meets policy;
- post-exclusion topology proves the selected candidate is isolated from remote artwork.

### 3. Contact is explainable
Every risky border-contact pixel/segment that would otherwise block automatic border cleanup must be explainable by approved metadata/corner geometry. Any unexplained contact outside that region causes `REVIEW`.

### 4. Deletion scope is bounded
- deletion set is the union of approved geometric border bands and approved metadata mask only;
- no global color-key deletion;
- no flood deletion crossing into unapproved artwork;
- planned deletion must remain within configured removal bounds.

### 5. Coordinate identity is exact
All masks/rectangles use one pre-cleanup frame coordinate space. Crop/translation cannot occur between detector outputs and plan validation. Joint-only metadata must bind to the exact approved border/exclusion mask identity.

## Rounded/Inset Border Evidence Model
Tier-B representative sheets proved that rounded transparent corners can lower raw whole-strip coverage even when the visible border pixels are strongly color-consistent.

Therefore inset-border evidence separates:
- **visible support:** fraction of the strip containing visible pixels supporting a plausible border band;
- **visible color purity:** fraction of visible samples agreeing with the selected border color model;
- **multi-side consensus:** compatible color/geometry evidence from the required number of sides;
- **band continuity:** bounded contiguous offsets/thickness;
- **contact evidence:** localized inner-edge ranges/fractions.

Automatic policy may use these dimensions to compute structural confidence, but shall not simply lower the approved automatic threshold. Transparent corner pixels are absence-of-support, not wrong-color evidence.

## Post-Exclusion Metadata Isolation Rule
Tier-B evidence also proved that the decorative border can connect a top-left badge to unrelated artwork before exclusion. Pre-exclusion raw-group membership therefore describes connectivity evidence but does not by itself define destructive ownership.

For exclusion-fragmented metadata, automatic joint cleanup may reconstruct a local candidate only when all conditions hold:
- each selected local fragment belongs to the same relevant pre-exclusion topology group or otherwise has explicitly proven local association;
- every selected local fragment is fully contained inside the approved anchor envelope;
- secondary selected fragments created by exclusion are adjacent to the approved exclusion boundary and remain spatially local to the primary candidate;
- after applying the analysis-only exclusion, the selected candidate/local group has **no non-excluded connected path outside the anchor envelope**;
- remote fragments from the same pre-exclusion raw topology may be ignored only when they are disconnected from the selected candidate by the approved exclusion mask;
- ignored/out-of-anchor fragments never enter candidate shape scoring or the metadata deletion mask;
- the reconstructed local union still passes area/fill/compactness/anchor/dominance rules;
- competing plausible anchored candidates cause `REVIEW`;
- excluded pixels are not copied into metadata mask; overlap pixels remain border-owned;
- resulting detection is marked `requires_joint_cleanup=true` and cannot be sent to standalone metadata removal.

If the selected post-exclusion component itself extends outside the anchor envelope without crossing the approved exclusion mask, the case remains `REVIEW`.

## Exclusion-Aware Metadata Shape Confidence
An approved spatial border mask used as analysis exclusion may remove pixels physically belonging to the badge/border overlap and lower apparent fill ratio. Shape evidence may be reconstructed only under these restrictions:
- overlap evidence is limited to approved exclusion pixels associated with the selected isolated local candidate;
- only overlap pixels inside the candidate bbox may contribute to analysis fill/shape confidence;
- overlap pixels never enter metadata deletion mask;
- overlap pixels remain owned by the exact border mask checked by `JointCleanupPlanner`;
- automatic metadata confidence threshold is not lowered;
- evidence records overlap-pixel count used only for shape scoring.

## Enclosed Interior Completion
A compact badge may contain visible interior pixels whose RGB resembles the background, such as dark digits inside a light badge. Such pixels may be added to metadata mask only when they are topologically fully enclosed by the approved badge support within its bounded local component. Open regions connected to exterior are never filled. Broad bounding-box fill, convex hull fill or morphology-based guessing is prohibited.

## Preferred Mutation Strategy
For overlap cases use mask-first cleanup, not sequential crop-first cleanup:
1. build geometric border-band mask;
2. build approved isolated metadata mask;
3. validate combined deletion plan;
4. apply combined mask to alpha once for transparent route;
5. allow content analysis/smart fit later.

For opaque route, the same approved masks remain plan/evidence only until M3 composes background removal and metadata cleanup into final alpha.

## Contact Localization Evidence
A boolean `contact_risk` is insufficient. Border provider/planner path must expose contact pixel/segment mask, per-side contact intervals/ranges, or equivalent topology evidence. Until complete contact localization exists, overlap cases remain `REVIEW`.

## Joint Cleanup Plan Model
```text
JointCleanupPlan
- status: SAFE_PLAN | REVIEW
- border_mask_ref / border_geometry
- metadata_mask_ref / metadata_bbox
- combined_mask_ref
- source_transparency_provenance
- explained_contact_fraction
- unexplained_contact_fraction
- planned_removed_pixel_count
- planned_removed_bbox
- confidence
- reasons[]
- evidence{}
```

The plan is worker-local computation/evidence, not final publication authority.

## Worker / MainBoard Boundary
Workers may detect, plan, apply an approved local plan to private working copy, write private scratch candidate artifacts and return structured evidence. Workers may not overwrite source/staged INPUT, select final output paths, mutate durable task state directly, or bypass MainBoard/ResourceBroker/ADR-024 final commit.

## REVIEW Conditions
Return `REVIEW` for insufficient border consensus/support/purity, ambiguous metadata, weak shape evidence, selected metadata escaping anchor via non-excluded connectivity, unexplained contact, mismatched coordinate/mask identity, excessive deletion, possible same-color artwork loss, missing provenance, or any unresolved local association.

## Prohibited Shortcuts
- lowering global thresholds merely to improve automation rate;
- global color-key deletion;
- deleting whole anchor/search boxes;
- convex hull / bounding-box fill;
- broad morphology to reconnect badge fragments;
- treating all fragments of one raw pre-exclusion topology as metadata;
- using cleanup-generated alpha to redefine source route.

## Required Regression Tests
At minimum:
1. transparent outer padding + inset rounded border + no contact;
2. rounded border with transparent corners and high visible color purity;
3. insufficient visible support despite high color purity → REVIEW;
4. same-color artwork contact away from metadata anchor → REVIEW;
5. anchored badge touching top/left border with all contact explained;
6. badge and remote artwork share pre-exclusion topology only through border mask; post-exclusion badge isolated and remote artwork preserved;
7. selected anchored component has non-excluded path outside anchor → REVIEW;
8. multiple competing anchored candidates → REVIEW;
9. non-anchored artwork inside broad metadata search zone is preserved;
10. badge absent → no metadata deletion;
11. enclosed numeral/detail completion does not fill exterior regions;
12. cleanup-generated alpha never changes source route;
13. combined plan mask is bounded and deterministic;
14. repeated execution produces identical mask/hash;
15. exclusion-aware shape confidence does not expand deletion mask or lower policy threshold.

## Tier-B Gate Rule
Tier-B corpus evidence records source hash, extraction evidence, source-transparency provenance, border geometry/support/purity/contact evidence, metadata/isolation evidence, joint-plan status/reasons, and per-frame result. High REVIEW rate is acceptable while evidence is incomplete; weakening policy merely to improve automation rate is not acceptable.

Current representative findings are captured in `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`.

## Repository Hygiene
- production/user source images are not committed by default;
- synthetic regression fixtures are generated in tests where practical;
- no runtime output/log/database/cache is committed;
- temporary diagnostic harnesses stay outside tracked source/runtime directories;
- duplicate experimental production paths are prohibited.

## Acceptance
ADR-028 implementation is complete only when contact localization, stable headless planning, safe/unsafe overlap regressions, representative Tier-B improvement, Windows CI, FrameResult/manifest evidence and repository hygiene are all verified. Owner acceptance remains a separate gate.

References: `05_STICKER_SHEET_SPEC.md`, `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`, `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`, ADR-005, ADR-008, ADR-023, ADR-024, ADR-026, ADR-027, Issue #12.
