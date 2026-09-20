# MTKrita Decorative Border-Band Depth Topology Specification

## Status
SSOT Extension — TB-006 Class B Depth-Topology Contract v1.2

## Purpose
Define the next Class-B refinement after v1.1 proved that non-risky authorized sides can provide valid adjacent-side corroboration but representative Candidate A/B still produce no `SAFE_COMPLETE` result.

The remaining blocker is not insufficient threshold tolerance. The representative borders are multi-layer rendered structures: an inward depth can retain strong side-parallel support while its tone distribution changes through antialiasing, shading, highlights or a second decorative ring. A whole-strip single dominant-color purity gate can therefore terminate ownership too early even when geometry remains coherent across adjacent sides.

v1.2 models border completion as a **depth-by-depth cross-side topology proof**, not as repeated single-side color matching.

## Product Mapping
This contract directly advances UC-03, UC-04 and UC-06. It exists to reduce false REVIEW for supported transparent decorative frames while preserving the false-safe target near zero.

## Representative Evidence
The v1.1 planner-only diagnostic over the same hash-matched Candidate A/B corpus produced:

- Candidate A: 10/10 `REVIEW_INSUFFICIENT_CORROBORATION`;
- Candidate B: B6 `NOT_NEEDED` after Class A; B1/B7/B8/B10 establish adjacent-side structural corroboration but remain `REVIEW_ARTWORK_CONTACT`; B2/B4/B9 remain insufficient; B3/B5 remain TB-005 ambiguity;
- no representative frame receives Class-B cleanup authority.

Examples of deeper rendered-layer evidence:

- B1 top depth 1 is a strong long layer; the next inward top strip remains long but has multiple tone families and lower whole-strip dominant-color purity. Right depth 1 is also strongly corroborated, while the next inward right strip remains structured but more fragmented in tone.
- B7 left supports multiple consecutive inward depths; top also retains a long inward continuation at the next depth even when one-color purity falls below the v1.0 layer threshold.
- B8 and B10 show similar long geometric support across adjacent sides after the first corroborated layer.

These observations do not authorize lowering `min_color_purity`. They justify a stronger topology model.

## Locked Safety Rules
v1.2 SHALL preserve:

- `REVIEW > destructive guess`;
- source immutability;
- existing seed-border automatic confidence threshold;
- existing residual contact-risk threshold;
- existing global/cross-side color tolerances;
- no global color-key deletion;
- no filename/corpus/frame-index special cases;
- no skipping inward gaps;
- no single-side ownership expansion;
- no opposite-side-only authority;
- JointCleanupPlanner ownership of metadata contact;
- TB-005 ambiguity remains ineligible;
- planner-first verification before destructive FramePipeline integration.

## Core Decision — Depth-Wise Proof
A seed border defines relative depth 0. Proposed decorative completion evaluates depth 1, depth 2, ... sequentially.

For each relative depth `d`:

1. inspect the strip at each authorized side's `seed_inner_offset + d - 1`;
2. derive **geometric support intervals** from visible side-parallel structure;
3. record tone/palette evidence but do not require one global color family;
4. authorize depth `d` for a side only when the same physical layer is corroborated by an adjacent trigger/proven side or by a coherent four-side ring;
5. advance to depth `d + 1` only if the current depth is proven;
6. stop at the first unproven depth; never jump over a gap;
7. proposed ownership ends at the deepest consecutively proven depth;
8. recompute completed-inner-boundary contact after the final proven depth.

This creates monotonic evidence: deeper ownership cannot exist unless every preceding depth was independently proven.

## Geometric Support Model
A depth strip may contain several rendered tones. Therefore geometric layer support SHALL be represented separately from tone purity.

At minimum record:
- visible support fraction;
- longitudinal visible/support ranges;
- longest contiguous side-parallel run fraction;
- count of meaningful runs;
- endpoint-low / endpoint-high participation;
- alpha continuity / transparent gaps;
- local tone clusters or palette summary;
- dominant-tone purity as evidence, not sole authority;
- relative depth.

A valid support run must be spatially contiguous within bounded antialias micro-gaps. Broad morphology or gap filling is prohibited.

## Tone Evidence
Tone evidence prevents arbitrary visible artwork from being interpreted as border continuation.

Allowed evidence can include:
- bounded number of local color clusters;
- adjacent-depth color transition consistency;
- corner-neighbor tone compatibility;
- similarity to one or more already proven side-local decorative tones.

Prohibited:
- lowering the existing v1.0 one-color purity threshold and calling the same algorithm safe;
- global palette averaging across the frame;
- accepting arbitrary visible support independent of color/tone structure.

v1.2 may introduce a separate multi-tone layer evidence policy only when it has explicit regression coverage and remains side/depth local.

## Adjacent-Side Depth Proof
For an adjacent pair at depth `d`, proof requires:

1. at least one side descends from a Class-B trigger chain;
2. both sides have geometric support at the same relative depth within the conservative depth-spread rule;
3. both supports participate in the same physical corner envelope;
4. both are contiguous from the preceding proven depth (or the seed band for depth 1);
5. neither side skipped a transparent/content gap;
6. tone evidence is compatible with a decorative transition and not arbitrary artwork;
7. the pair remains within existing `max_search`.

When proven, both sides may advance one depth.

## Four-Side Depth Proof
A four-side ring at depth `d` requires all four sides to satisfy the depth evidence and geometry coherence rules. A weak/missing side prevents four-side authority at that depth.

## Chain / Branch Rule
Different adjacent pairs may stop at different depths. Proposed per-side completion may therefore be asymmetric, but:

- each proposed side must have a continuous proof chain from seed to its deepest owned depth;
- a side cannot be advanced by a remote pair that does not include it;
- a deeper pair cannot retroactively authorize a missing shallower layer;
- geometry must remain internally consistent at corners.

## Completed Boundary Recheck
After deepest proven depths are selected:

1. construct proposed per-side inner offsets;
2. measure raw completed-boundary contact;
3. reapply Class-A reciprocal corner explanation;
4. preserve raw/explained/residual ranges and fractions;
5. apply the unchanged residual contact-risk threshold;
6. if residual contact remains risky, attempt only existing approved metadata joint ownership where applicable;
7. otherwise REVIEW.

The planner must not repeatedly consume deeper layers merely because the newly measured boundary is risky. Deeper growth requires its own depth proof before contact is considered.

## Planner Output Additions
The non-destructive plan should expose:

```text
BorderBandCompletionPlan
- status
- trigger_sides[]
- depth_evidence{side -> depth -> evidence}
- proven_depths{side -> deepest_depth}
- proven_pairs{depth -> corner pairs}
- proposed_inner_offsets{}
- completed_inner_contact{}
- reasons[]
```

FramePipeline integration remains prohibited until representative planner evidence is accepted.

## Required Synthetic Regression Matrix
Before destructive integration, tests SHALL include:

1. **Two-depth adjacent multi-tone frame**
   - depth 1 and depth 2 use distinct tones;
   - both top/left preserve side-parallel geometry and shared-corner proof;
   - both depths are proven without lowering single-tone purity policy.

2. **Depth gap refusal**
   - depth 1 proven;
   - depth 2 absent/transparent;
   - depth 3 border-colored support exists;
   - planner stops after depth 1 and never jumps to depth 3.

3. **One-side deeper artwork refusal**
   - top/left depth 1 proven;
   - top depth 2 has long artwork-like strip but left depth 2 absent;
   - top cannot advance alone.

4. **Opposite-side-only depth refusal**
   - top/bottom show depth 2, no adjacent proof;
   - no authority.

5. **Four-side two-depth ring**
   - all four sides prove two coherent depths;
   - completed boundary clean.

6. **Asymmetric pair depth**
   - top-left proves depth 2;
   - top-right proves only depth 1;
   - per-side proposed geometry remains deterministic and corner-consistent.

7. **Multi-tone layer with bounded palette**
   - whole-strip dominant-color purity would fail v1.0;
   - bounded local tone clusters + geometric proof pass v1.2.

8. **Chaotic artwork palette refusal**
   - long visible strip but excessive/unstable local tone structure;
   - REVIEW.

9. **Completed boundary artwork contact**
   - all proposed depths structurally proven;
   - real artwork remains at final inner boundary;
   - REVIEW_ARTWORK_CONTACT.

10. **Completed reciprocal corner only**
    - final contact exists only as reciprocal rounded-corner continuation;
    - Class A explanation clears it.

11. **Metadata boundary**
    - final risky contact overlaps anchored frame metadata;
    - only JointCleanupPlanner may own it.

12. **Determinism / previous regressions**
    - repeat-identical evidence;
    - TB-001 through TB-006 v1.1 remain green.

## Tier-B Acceptance Procedure
After v1.2 planner passes Windows Ruff + pytest:

1. rerun hash-matched Candidate A/B planner-only diagnostics;
2. record depth evidence and proposed deepest ownership by frame/side;
3. inspect all `SAFE_COMPLETE` proposals visually against original refined frames;
4. reject any proposed ownership that intersects character/text/artwork;
5. require no known false-safe planner proposal before FramePipeline integration;
6. then add integrated mutation tests and rerun full representative pipeline;
7. M2 remains open until useful automatic behavior exists and every newly automatic output passes visual QA.

## Non-Goals
v1.2 does not implement M3, UI logic, arbitrary semantic segmentation, global color deletion or corpus-specific heuristics.

## Repository Hygiene
Representative source bytes and diagnostic outputs remain outside Git history. Only SSOT, implementation, synthetic regressions and summarized evidence are versioned.

References: `68_BORDER_CONTACT_TOPOLOGY_SPEC.md`, `69_USE_CASE_ACCEPTANCE_MATRIX.md`, `70_BORDER_BAND_COMPLETION_SPEC.md`, `71_BORDER_BAND_CORROBORATION_REFINEMENT_SPEC.md`, Issue #12, PR #11.
