# MTKrita Decorative Border-Band Completion Specification

## Status
SSOT Extension — TB-006 Class B Border-Band Completion Contract v1.0

## Purpose
Define the next evidence-backed M2 hardening step after TB-006 Phase 1 reciprocal rounded-corner topology.

Phase 1 proves that endpoint-localized reciprocal contact can be removed from the unexplained-contact budget without lowering the contact-risk threshold. Representative Candidate A/B diagnostics also show that most remaining REVIEW cases are not explained by corner continuation: they contain long or central inner strips consistent with an incompletely owned multi-layer decorative frame, or genuine artwork contact.

Class B exists to distinguish those cases safely.

## Product Mapping
Class B directly advances:
- UC-03 — Single-Tone Transparent Border;
- UC-04 — Rounded / Multi-Tone Decorative Border;
- UC-06 — Mixed Border + Metadata Contact;
- UC-11 — LINE-Ready Export, indirectly by allowing only correctly cleaned candidates to progress.

It does not change UC-07/M3 opaque-background authority.

## Evidence Baseline
After TB-006 Phase 1 Windows CI is green, a read-only hash-matched contact-topology diagnostic over refined Candidate A/B geometry shows:
- Candidate A: all 10 frames still retain frame-level residual border-contact risk;
- Candidate B: frame 6 changes from raw frame-level contact risk to no residual frame-level contact risk through reciprocal corner explanation;
- Candidate B frames 3 and 5 remain explicit border ambiguity from TB-005 and are not Class-B candidates;
- Candidate B frames 1, 2, 4, 7, 8, 9 and 10 retain residual contact, dominated in representative cases by central or long side-parallel ranges rather than reciprocal endpoint-only geometry;
- no threshold or global color tolerance was changed.

Representative residual examples include:
- Candidate B frame 9: a long bottom-side central continuation remains residual and risky after corner explanation;
- Candidate B frame 10: a large left-side central continuation remains residual and risky;
- Candidate B frame 8: reciprocal top-corner ranges can be explained, while suspicious central right-side contact remains residual;
- Candidate A contains multiple long/central residual strips on several sides.

This evidence establishes that Class A alone cannot close M2.

## Locked Safety Rules
Class B SHALL preserve:
- `REVIEW > destructive guess`;
- immutable source input;
- existing border automatic confidence threshold;
- existing residual contact-risk threshold;
- existing global/cross-side color tolerances;
- no global color-key deletion;
- no filename, corpus identity, frame index, caption, or hard-coded representative coordinates as authority;
- no UI-owned cleanup decision;
- JointCleanupPlanner authority for metadata-owned contact;
- MainBoard / ResourceBroker / ADR-024 final publication authority;
- M3 remains blocked until M2 closes.

Class B SHALL NOT turn a long same-colored strip into deletion authority merely because it is close in color to an already detected border.

## Concept — Border Band as a Layered Near-Edge Structure
The current inset detector identifies a conservative seed side with:
- side;
- offset;
- thickness;
- representative side-local color;
- visible support;
- color purity;
- confidence;
- inner-boundary contact evidence.

For decorative sheets, that seed can represent only one ring/tone of a wider rendered frame. Class B treats the seed as a hypothesis anchor and evaluates bounded inward layers before any geometry expansion is authorized.

A completed side band is therefore:

```text
outer transparent padding
    ↓
seed border layers already owned
    ↓
zero or more proposed adjacent decorative layers
    ↓
completed inner boundary
    ↓
sticker artwork / metadata / transparency
```

Ownership must be proven geometrically across sides. Color similarity alone is insufficient.

## Class-B Planner
Introduce a non-destructive planner, conceptually:

```text
BorderBandCompletionPlanner
Input:
- immutable extracted frame
- authorized BorderDetection after Class-A topology
- raw + explained + residual contact evidence
- detector near-edge search domain

Output:
- per-side proposed completion evidence
- cross-side corroboration evidence
- status
- completed BorderDetection candidate only when SAFE_COMPLETE
```

Suggested status enum:
- `NOT_NEEDED`
- `SAFE_COMPLETE`
- `REVIEW_INSUFFICIENT_CORROBORATION`
- `REVIEW_ARTWORK_CONTACT`
- `REVIEW_GEOMETRY_CONFLICT`
- `REVIEW_SEARCH_BOUNDARY`

The planner itself performs no image mutation.

## Eligibility
A side may enter Class-B completion analysis only when:
1. the original border detection is authorized and `requires_review == false`;
2. consensus mode is an approved inset mode (`single_tone` or `multi_tone_four_side`);
3. border confidence already satisfies automatic policy;
4. residual contact exists at the current inner boundary;
5. the candidate continuation lies fully inside the existing bounded near-edge search domain;
6. the candidate continuation is side-parallel and spatially adjacent to the current owned band.

TB-005 ambiguity cases are not repaired by Class B. A frame with unauthorized border consensus remains REVIEW.

## Layer Evidence
For every inward layer considered on a side, record at minimum:
- side id;
- absolute inward offset;
- visible support fraction;
- representative side-local color;
- color purity against its own layer model;
- longitudinal support ranges;
- longest supported run fraction;
- number of disjoint support runs;
- whether support reaches an endpoint envelope;
- relationship to the immediately outer owned layer;
- whether the layer would move the completed inner boundary.

The planner must preserve original seed geometry and report proposed geometry separately.

## Side-Local Color Rule
Decorative bands may change shade inward. Therefore:
- each side/layer retains its own representative color;
- colors may evolve gradually across adjacent layers;
- no global averaged border color is created;
- no layer is accepted merely because it falls inside a newly widened universal tolerance;
- cleanup masks remain spatially bounded to approved layers and side-local evidence.

## Corroboration Requirement
A long/central continuation on one side is insufficient.

Automatic completion requires structural corroboration beyond the side being expanded. Phase-1 Class B shall require at least one of the following conservative proofs:

### Pattern B1 — Adjacent-Side Layer Corroboration
The proposed inward layer on one side has a compatible inward decorative layer on at least one perpendicular adjacent side, and the two layers form a coherent physical corner/continuation within the bounded search domain.

### Pattern B2 — Four-Side Ring Corroboration
Equivalent inward layer depth is supported on all four authorized sides, with bounded thickness/depth spread and no side-specific geometry conflict.

Opposite-side-only similarity is not sufficient because artwork can independently create long parallel strips.

## Geometry Coherence
A SAFE completion must demonstrate:
- completed inward depth remains within detector `max_search` domain;
- completed side thickness/depth spread is bounded by an explicit conservative limit specified before implementation tests are accepted;
- side offsets may remain asymmetric;
- proposed layers are contiguous or have only explicitly allowed antialias/shadow micro-gaps;
- no layer skips across transparent/content gaps to absorb remote same-colored artwork;
- corner relationships are geometrically consistent.

The first implementation SHALL derive bounds from existing detector geometry where possible rather than inventing a large new percentage envelope.

## Completed Inner-Boundary Recheck
This is mandatory.

Even after a decorative band is structurally corroborated, automatic cleanup is forbidden until contact is recomputed at the **proposed completed inner boundary**.

The completed boundary is safe only when:
- Class-A reciprocal corner explanation is reapplied where appropriate;
- remaining residual contact is below the unchanged contact-risk threshold; or
- remaining contact is subsequently fully explained by approved metadata through JointCleanupPlanner.

If new inner-boundary contact indicates artwork, the result is `REVIEW_ARTWORK_CONTACT`.

Class B therefore cannot hide artwork contact by simply growing the border until contact disappears from the current measurement location.

## Metadata Rule
Class B does not own frame-number badges.

If completed border geometry intersects metadata evidence:
- metadata detection receives the exact completed border mask only as approved analysis exclusion;
- exclusion identity remains bound by hash/coordinate space;
- local metadata ownership and fragment association rules remain unchanged;
- JointCleanupPlanner must account for metadata-owned residual contact;
- broad border completion cannot absorb the badge deletion mask.

## Cleanup Authority
Only `SAFE_COMPLETE` may replace the seed BorderDetection for downstream planning/removal.

Even then, normal gates still apply:
1. authorized border consensus;
2. confidence at existing threshold;
3. completed geometry coherent;
4. completed-inner-boundary residual contact safe or jointly explained;
5. bounded deletion mask;
6. transparent/opaque routing rules unchanged.

For transparent route, mutation remains downstream and spatially bounded.
For opaque route, Class-B result remains plan/evidence only until M3.

## Required Evidence Model
Suggested immutable evidence:

```text
BorderBandCompletionPlan
- status
- original_geometry{}
- proposed_geometry{}
- side_layers{}
- corroboration_pattern
- corroborating_sides[]
- completed_inner_contact{}
- residual_contact_fraction
- residual_contact_ranges
- confidence
- reasons[]
```

FrameResult evidence should expose enough of this model to explain why geometry did or did not expand without requiring logs/UI text.

## Required Synthetic Regression Matrix
Implementation SHALL include at least:

1. **Corroborated two-side decorative layer**
   - long inner continuation on top plus coherent perpendicular continuation on left;
   - within existing search domain;
   - completed inner boundary clean;
   - SAFE_COMPLETE eligible.

2. **Single-side long strip refusal**
   - long side-parallel support on only one side;
   - no perpendicular corroboration;
   - REVIEW_INSUFFICIENT_CORROBORATION.

3. **Opposite-side-only refusal**
   - top/bottom similar long strips but no adjacent-side proof;
   - not sufficient for automatic ownership.

4. **Four-side coherent ring**
   - inward decorative ring on all four sides;
   - bounded coherent depth;
   - completed boundary clean;
   - SAFE_COMPLETE eligible.

5. **Geometry conflict**
   - one proposed side requires materially different/deeper ownership than others;
   - REVIEW_GEOMETRY_CONFLICT.

6. **Search-boundary refusal**
   - proposed completion would extend beyond existing bounded inset search domain;
   - REVIEW_SEARCH_BOUNDARY.

7. **Decorative band plus central artwork touch**
   - corroborated decorative layers exist;
   - true artwork touches completed inner boundary;
   - REVIEW_ARTWORK_CONTACT.

8. **Same-color remote artwork**
   - remote artwork has border-like color but is separated from adjacent band by gap;
   - never absorbed into completed geometry.

9. **Rounded corner + band continuation**
   - Class A endpoint evidence is explained first;
   - Class B evaluates only remaining long/central continuation;
   - no double-counting.

10. **Metadata overlap**
    - completed border reaches an anchored badge;
    - badge remains JointCleanupPlanner-owned;
    - exact mask identity enforced.

11. **No-border artwork**
    - arbitrary near-edge artwork must not create Class-B authority.

12. **Determinism**
    - repeated identical input/config yields identical status, proposed geometry, evidence and mask identity.

13. **TB-001 through TB-006 Class-A regression**
    - all previous safety tests remain green.

## Tier-B Acceptance Procedure
After Class-B implementation passes Windows Ruff + pytest:
1. verify Candidate A/B source hashes before execution;
2. run exact refined extraction + full FramePipeline read-only;
3. compare against the pre-Class-B representative baseline;
4. record original/proposed geometry and completed-inner-boundary contact evidence;
5. inspect every newly automatic frame visually for:
   - decorative border residue;
   - crop loss;
   - badge/numeral residue;
   - accidental artwork deletion;
   - halo/edge damage introduced by cleanup;
6. verify source SHA-256 unchanged after execution;
7. compute `auto_process_rate`, `review_rate`, `false_safe_rate` and visual acceptance for the representative run;
8. reject any automation gain caused by threshold/tolerance relaxation;
9. keep M2 open if supported automatic behavior is still not practically useful or any known false-safe remains.

## Phase-1 Class-A Result Boundary
The Class-A diagnostic is evidence of partial progress, not M2 acceptance.

At the current checkpoint:
- Candidate A frame-level residual risk clears on 0/10 frames;
- Candidate B frame-level residual risk clears on one authorized single-tone frame (frame 6);
- Candidate B frames 3 and 5 remain TB-005 ambiguity REVIEW;
- the remaining supported Candidate B cases still expose central/long residual contact requiring Class B or metadata evidence.

A full exact-current-source FramePipeline rerun is still required before any Candidate B frame is claimed PASS/AUTO_FIXED.

## Non-Goals
Class B does not:
- lower contact-risk thresholds;
- widen global color tolerance;
- solve TB-005 ambiguous border consensus;
- delete arbitrary same-colored artwork;
- replace metadata ownership;
- implement opaque-background removal;
- move business rules into UI;
- change worker/final-publication authority.

## Repository Hygiene
- Candidate A/B source bytes remain outside Git history;
- synthetic fixtures are generated in tests where practical;
- local diagnostics/results are not committed as runtime artifacts;
- only SSOT, code, regression tests and summarized evidence belong in the repository.

References: `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`, `67_MULTITONE_BORDER_CONSENSUS_SPEC.md`, `68_BORDER_CONTACT_TOPOLOGY_SPEC.md`, `69_USE_CASE_ACCEPTANCE_MATRIX.md`, ADR-023, ADR-028, Issue #12, PR #11.
