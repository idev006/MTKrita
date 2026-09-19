# Joint Border + Metadata Cleanup Specification

## Status
SSOT — Joint Cleanup Safety Contract v1.0

## Decision Record — ADR-028
**Title:** Joint Border/Metadata Cleanup Is Planned Before Destructive Mutation  
**Status:** Accepted

When frame-number metadata touches or overlaps a decorative frame border, MTKrita shall not execute border removal and metadata removal as two independent destructive operations. Detection remains separable, but mutation is authorized only from one combined cleanup plan whose evidence explains the complete contact topology.

This decision extends ADR-005 (Conservative Automation), ADR-008 (Adaptive Border Removal), ADR-023 (Source Transparency Provenance), ADR-024 (Durable Commit Intent), ADR-026 (Worker Results Are Candidates) and ADR-027 (Immutable Staged Inputs).

## Problem
Representative transparent Sticker Sheets can contain all of the following at once:
- transparent padding outside the visual frame;
- an inset rounded/anti-aliased decorative border;
- a frame-number badge anchored at the top-left corner;
- the badge touching or overlapping the decorative border;
- real sticker artwork and Thai text close to the border.

If border removal runs first, the badge may be partially cropped or merged into border evidence. If metadata removal runs first, alpha can be changed before routing provenance or border topology is safely understood. Lowering thresholds to force either stage through would violate `REVIEW > destructive guess`.

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
Source/background routing must be captured from source/extracted-frame alpha state before any cleanup that can create or materially alter alpha.

Border/metadata detection may inspect pixels and build masks without changing routing provenance.

The combined cleanup result must never be reinterpreted as source transparency evidence.

## Inputs to JointCleanupPlanner
Required inputs:
- immutable source transparency decision/provenance;
- border detection with per-side offset, thickness, confidence, color/range and contact evidence;
- metadata detection with bbox/mask, anchor evidence, compactness/shape evidence, candidate counts, confidence and dominance margin;
- frame geometry;
- configured metadata anchor envelope;
- configured safety margins.

Optional future inputs:
- topology graph / connected-component evidence;
- provider-specific contour evidence;
- user-approved metadata template/profile.

## Safe Automatic Plan Requirements
Automatic joint cleanup is permitted only when **all** required conditions hold:

1. **Strong border evidence**
   - border has approved multi-side consensus or equivalent strong topology evidence;
   - per-side offset/thickness geometry is bounded and internally consistent;
   - confidence meets automatic policy.

2. **Strong metadata evidence**
   - exactly one dominant anchored badge candidate is selected;
   - candidate satisfies area, compactness and anchor constraints;
   - dominance margin meets policy;
   - candidate is inside the approved metadata anchor envelope.

3. **Contact is explainable**
   - every risky border-contact pixel/segment that would otherwise block automatic border cleanup is either:
     - inside the approved metadata mask/bbox plus a small configured adjacency allowance; or
     - part of known perpendicular border corner geometry;
   - any unexplained contact outside that region causes `REVIEW`.

4. **Deletion scope is bounded**
   - the planned deletion set is the union of approved geometric border bands and approved metadata mask only;
   - no global color-key deletion is allowed;
   - no flood deletion may cross into unapproved artwork regions;
   - planned deletion must not consume the frame or violate configured maximum removal bounds.

5. **No hidden coordinate ambiguity**
   - all masks/rectangles use the same pre-cleanup frame coordinate space;
   - crop/translation is not applied between detector outputs and plan validation.

## Preferred Mutation Strategy
For overlap cases, the preferred M2 strategy is **mask-first cleanup**, not sequential crop-first cleanup:

1. build geometric border-band mask from detected offsets/thicknesses;
2. combine with approved metadata mask;
3. validate the combined deletion plan;
4. apply the combined mask to alpha once;
5. allow content analysis / smart fit to remove now-empty transparent padding later.

Why:
- avoids coordinate shifts between border and metadata stages;
- preserves provenance and evidence in one coordinate system;
- makes deletion scope inspectable before mutation;
- allows a single rollback/review boundary;
- prevents partial badge cropping.

Existing crop-based border removal remains valid for ordinary non-contact borders when current safety rules pass.

## Contact Localization Evidence
A boolean `contact_risk` is insufficient for joint cleanup authorization.

The border provider/planner path must support structured contact localization evidence, at minimum one of:
- contact pixel/segment mask in frame coordinates;
- per-side contact intervals/ranges;
- equivalent topology object that can prove all contact is contained within an approved metadata/corner region.

Until this evidence exists, overlap cases remain `REVIEW` even if badge detection confidence is high.

## Joint Cleanup Plan Model
Recommended immutable model:

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

The plan is a worker-local computation result/evidence object. It is not authority to publish final files.

## Worker / MainBoard Boundary
Workers may:
- detect border/metadata;
- build a provisional joint cleanup plan;
- apply an approved local plan to a private working copy;
- write only private scratch candidate artifacts;
- return structured evidence.

Workers may not:
- overwrite source or staged INPUT;
- choose final output paths;
- mutate durable task state directly;
- bypass MainBoard validation, ResourceBroker or ADR-024 final artifact commit.

## REVIEW Conditions
Return `REVIEW` when any of the following is true:
- border consensus is insufficient;
- metadata candidate is absent or ambiguous;
- badge anchor/shape evidence is insufficient;
- contact exists outside approved metadata/corner region;
- contact localization is unavailable for an overlap case;
- border/metadata masks use inconsistent coordinate spaces;
- planned deletion exceeds configured safety bounds;
- same/near-border-color artwork may be removed;
- source transparency provenance is missing or mutable.

## Required Regression Tests
At minimum:
1. transparent outer padding + inset border + no contact → existing safe border path remains PASS;
2. inset border + same-color artwork contact away from metadata anchor → REVIEW;
3. anchored badge touching top/left border and no other contact → joint plan may become SAFE only after contact-localization evidence is implemented;
4. anchored badge + unrelated artwork contact on another side → REVIEW;
5. two plausible anchored badges → REVIEW;
6. non-anchored artwork inside broad metadata zone → preserved;
7. badge absent → no metadata deletion;
8. cleanup-generated alpha never changes source route;
9. combined plan mask is bounded and deterministic;
10. repeated execution produces identical mask/hash for deterministic providers.

## Tier-B Gate Rule
Tier-B corpus evidence must record:
- source SHA-256 (without committing private/user image bytes unless explicitly approved);
- frame extraction evidence;
- source transparency provenance;
- border geometry/contact localization evidence;
- metadata evidence;
- joint plan status/reasons;
- final per-frame PASS/REVIEW/FAIL result.

A high REVIEW rate is acceptable while safety evidence is incomplete. It is not acceptable to weaken policy merely to improve automation rate.

## Repository Hygiene
- production/user source images are not committed by default;
- synthetic regression fixtures are generated in tests when practical;
- no runtime output/log/database/cache is committed;
- joint-cleanup experiments remain outside tracked runtime directories until accepted by SSOT/test gates;
- temporary algorithms must not coexist as duplicate production paths.

## Acceptance
ADR-028 implementation is complete only when:
- contact localization evidence exists;
- `JointCleanupPlanner` has a stable headless contract;
- safe and unsafe overlap regressions are automated;
- existing M2 regressions remain green;
- representative Tier-B cases improve without threshold relaxation;
- Windows CI passes;
- evidence is traceable through FrameResult/manifest;
- PR #11 remains free of generated/private corpus bytes.

References: `05_STICKER_SHEET_SPEC.md`, `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`, ADR-005, ADR-008, ADR-023, ADR-024, ADR-026, ADR-027, Issue #12.
