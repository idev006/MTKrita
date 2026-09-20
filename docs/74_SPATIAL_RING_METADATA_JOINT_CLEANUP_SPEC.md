# MTKrita Spatial Ring + Metadata Joint Cleanup Specification

## Status
SSOT Extension — TB-007 Joint Spatial Cleanup Contract v1.0

## Purpose
Define how a verified `ClosedRingPlan` can participate in transparent M2 cleanup when its completed inner boundary still has localized contact, especially a frame-number badge touching the decorative ring.

The existing ADR-028 `JointCleanupPlanner` rebuilds a border mask from side color evidence. TB-007 already produces a stronger exact spatial ring mask and hash. Reconstructing a different mask would lose identity and reintroduce incomplete multi-tone ownership. This contract therefore accepts the exact verified ring mask as border ownership evidence.

## Core Rule
**Detect ring spatially. Detect metadata with the exact ring mask excluded for analysis. Plan the combined deletion from those exact masks. Mutate once.**

No step may substitute a recolored/reconstructed approximation of the accepted ring mask.

## Eligibility
Spatial ring joint cleanup is eligible only when:
- source route is meaningfully transparent;
- `ClosedRingPlan` is `RING_WITH_CONTACT` or `SAFE_RING`;
- ring mask exists and its SHA-256 is present;
- four-side ring geometry already passed TB-007 support/thickness/palette gates;
- border consensus is not unresolved TB-005 ambiguity;
- metadata detection is performed in the same pre-cleanup coordinate space using the exact ring mask as analysis exclusion.

## Metadata Contract
Metadata detection remains governed by the existing S-06 / ADR-028 rules:
- one dominant anchored local candidate;
- bounded anchor/local envelope;
- post-exclusion isolation;
- remote artwork preservation;
- enclosed-visible-hole rules;
- confidence threshold unchanged;
- exclusion pixels remain ring-owned and are never copied into metadata deletion ownership.

When metadata reports `requires_joint_cleanup`, its `analysis_exclusion_sha256` MUST equal the accepted ring mask SHA-256.

## Contact Accounting
TB-007 side evidence exposes residual contact ranges after reciprocal corner explanation.

For each side with `contact_risk=true`:
- localize each residual range;
- map it to the metadata bbox projection using the existing bounded adjacency rule;
- contact within approved metadata adjacency may be explained by metadata ownership;
- contact outside approved metadata adjacency remains unexplained;
- any unexplained residual contact causes REVIEW.

A ring may be structurally valid while joint cleanup is refused because contact is real artwork.

## Combined Mask
When all residual ring contact is explained:

```text
combined_mask = exact_ring_mask OR approved_metadata_mask
```

Rules:
- both masks must match frame size and coordinate space;
- no global color-key deletion;
- no bbox fill;
- no morphology-based expansion;
- combined removal ratio must remain below the existing conservative joint-cleanup bound;
- mask hash is deterministic and recorded.

## Output Plan
The planner returns the existing joint-plan semantics or an equivalent compatible model:
- `SAFE_PLAN | REVIEW`;
- exact ring mask/hash;
- metadata mask/bbox;
- combined mask/hash;
- explained/unexplained contact fractions;
- planned removed pixel count/ratio;
- confidence;
- reasons.

The plan remains worker-local evidence. Final artifact authority remains MainBoard / ResourceBroker / ADR-024.

## Transparent Mutation
For `SAFE_PLAN` on a source-transparent frame:
- set alpha to zero only where the combined mask is nonzero;
- preserve RGB/source pixels elsewhere;
- do not crop the source frame at this stage;
- subsequent content analysis / smart fit may reposition the surviving sticker content.

## Opaque Route
TB-007 joint spatial cleanup MUST NOT create alpha on an opaque-source frame. Opaque handling remains M3-owned.

## Required Regression Tests
1. safe four-side ring + top-left badge contact fully explained → SAFE_PLAN;
2. ring contact on opposite/remote side outside badge projection → REVIEW;
3. metadata absent/ambiguous → REVIEW when ring contact exists;
4. metadata confidence below threshold → REVIEW;
5. mismatched exclusion hash → REVIEW;
6. exact exclusion hash + resolved fragmented metadata → eligible;
7. combined mask exceeds removal-ratio bound → REVIEW;
8. deterministic combined mask/hash;
9. applying SAFE_PLAN removes ring + badge once and preserves central artwork;
10. opaque route never applies alpha mutation;
11. source image remains immutable;
12. existing ADR-028 tests remain green.

## Representative Gate
After Windows CI:
- run B6 refined frame through closed-ring plan → metadata detection with exact ring mask → spatial joint planner;
- inspect planned contact accounting;
- if SAFE_PLAN, render a private preview and visually verify ring/badge removal with no character/text loss;
- only after B6 visual acceptance may FramePipeline route eligible representative frames through this path;
- rerun full Candidate A/B and inspect every new automatic output.

## Product Acceptance
This contract advances UC-04, UC-05 and UC-06. It is successful only if it converts supported representative REVIEW cases into visually accepted automatic outputs without opening a false-safe path.

References: `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `69_USE_CASE_ACCEPTANCE_MATRIX.md`, `73_CLOSED_RING_BORDER_TOPOLOGY_SPEC.md`, ADR-028, Issue #12, PR #11.
