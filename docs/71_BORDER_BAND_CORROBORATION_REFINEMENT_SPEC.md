# MTKrita Border-Band Corroboration Refinement Specification

## Status
SSOT Extension — TB-006 Class B Corroboration Contract v1.1

## Purpose
Refine `70_BORDER_BAND_COMPLETION_SPEC.md` from representative read-only Candidate A/B diagnostics after the initial Class-B planner was implemented.

The first planner version inspected only border sides whose residual `contact_risk` was already true. Representative evidence shows this is too restrictive: a perpendicular side can have no residual seed-color contact risk after Class A while still containing a strong side-parallel decorative layer of another side-local tone immediately inward of the seed band. Excluding that side discards valid structural corroboration and causes systematic over-review.

This refinement changes evidence collection, not safety thresholds.

## Representative Evidence
Read-only diagnostics over the same hash-matched Candidate A/B corpus found:

- Candidate B frame 1: `right` remains residual-risky and contains a long candidate layer at its current inner offset with longest-run support about 0.81. `top` is not residual-risky, but independently contains a long immediate inward decorative layer with longest-run support about 0.81. The two layers occupy compatible relative depth and meet at the same physical top-right corner.
- Candidate B frame 7: `left` remains residual-risky and contains long immediate inward layers with longest-run support about 0.85–0.86. `top` is not residual-risky, but contains a strong immediate inward layer with longest-run support about 0.81.
- Candidate B frame 8 and frame 10 show the same defect class: non-risky authorized sides still contain strong near-edge layer evidence that can corroborate a risky perpendicular side.
- Candidate A remains substantially noisier and does not gain automatic authority merely from this refinement.

No source bytes were changed and no contact threshold/global color tolerance was relaxed.

## Decision
Class-B analysis SHALL distinguish:

1. **Trigger sides** — authorized border sides whose residual `contact_risk` is true after Class A. At least one trigger side is required before Class B runs.
2. **Evidence sides** — every authorized detected side in the same inset-border consensus, regardless of residual contact-risk state.
3. **Proposed ownership sides** — only evidence sides whose inward layers participate in an accepted adjacent-side or four-side corroboration proof.

A non-risky evidence side may corroborate a risky trigger side and may itself enter proposed completion geometry only when its own inward layer is part of the same proven physical decorative structure and its completed inner boundary independently passes the unchanged contact-risk rule.

A non-risky side never gains deletion authority merely because another side is risky.

## Locked Safety Rules
This refinement SHALL NOT:
- lower the existing residual contact-risk threshold;
- lower border automatic confidence;
- widen global/cross-side color tolerance;
- infer ownership from filename, frame index or corpus identity;
- treat opposite-side-only similarity as corroboration;
- absorb a non-risky side without its own contiguous layer evidence;
- bypass completed-boundary contact recheck;
- bypass JointCleanupPlanner metadata authority;
- repair TB-005 `requires_review` ambiguity;
- mutate the image inside the planner.

`REVIEW > destructive guess` remains mandatory.

## Evidence Collection Rule
When Class B is triggered:

- collect bounded contiguous inward-layer candidates from **all authorized sides**;
- preserve whether each side was a trigger side;
- keep layer colors side/layer-local;
- stop candidate collection at the first unproven gap or failed contiguous layer;
- preserve layer support/purity/range evidence even when that side is not residual-risky.

If there are no trigger sides, status remains `NOT_NEEDED` even if decorative-looking layers are visible.

## Adjacent-Side Proof v1.1
Pattern B1 is satisfied only when:

1. at least one member of the pair is a trigger side;
2. the two sides are perpendicular and share one physical corner;
3. both sides have contiguous candidate layers inside the existing `max_search` domain;
4. at least one candidate-layer pair is coherent in relative inward depth within the existing conservative depth-spread bound;
5. each layer reaches the corresponding shared-corner endpoint envelope;
6. no transparent/content gap is skipped to create the pair.

When B1 is proven, only the sides in the proven pair(s) are eligible for proposed completion geometry.

## Multi-Pair Rule
A side may participate in two valid adjacent-side pairs, for example `top-left` and `top-right`. The proposal may include the union of those proven sides only when every included side independently has contiguous candidate-layer evidence and completed-boundary validation.

Do not infer a four-side ring merely because two unrelated adjacent pairs exist.

## Four-Side Proof v1.1
Pattern B2 still requires all four authorized sides to expose coherent contiguous inward-layer evidence. Maximum relative-depth spread remains conservative and explicit. A missing/weak side prevents four-side authority.

## Completed Boundary Rule
After proposed geometry is formed:

- compute a new inner-boundary contact measurement for every proposed ownership side;
- use the unchanged contact-risk threshold;
- preserve localized ranges;
- reapply Class-A reciprocal-corner explanation where applicable before final residual classification;
- if any proposed side retains unexplained residual contact at/above threshold, the plan is not `SAFE_COMPLETE`;
- contact potentially owned by anchored frame metadata must remain available to JointCleanupPlanner rather than being silently declared artwork or silently deleted.

The planner may return `REVIEW_ARTWORK_CONTACT` / equivalent pending-joint-cleanup evidence; it must not grow repeatedly inward until contact disappears.

## Required Regression Additions
In addition to the v1.0 matrix:

1. risky top + non-risky left with coherent immediate decorative layers → left is valid corroboration evidence and both layers are proposed only if completed boundaries are safe;
2. risky side + non-risky perpendicular side with no layer → insufficient corroboration;
3. risky side + non-risky opposite side with layer → insufficient corroboration;
4. non-risky layer not connected to shared-corner endpoint → cannot corroborate;
5. no trigger sides + decorative layers → `NOT_NEEDED`;
6. corroborating non-risky side with unsafe completed inner boundary → REVIEW;
7. two adjacent pairs sharing one side remain deterministic and include only proven sides;
8. Candidate-like long layers with low purity/gaps remain REVIEW without threshold relaxation.

## Tier-B Gate
After implementation passes Windows Ruff + pytest:

1. rerun planner-only diagnostics on hash-matched Candidate A/B;
2. compare proposed pairs and completed-boundary evidence against this representative finding;
3. do not connect Class B to destructive FramePipeline authority until every proposed representative completion has been visually inspected and no false-safe geometry is observed;
4. only then add downstream integration regressions and rerun full pipeline;
5. M2 remains open until useful automatic behavior exists on representative supported frames and every automatic output passes visual QA.

## Product Mapping
This refinement advances UC-03, UC-04 and UC-06 by reducing false REVIEW through stronger structural evidence rather than weaker policy. It does not alter UC-07/M3 authority.

References: `68_BORDER_CONTACT_TOPOLOGY_SPEC.md`, `69_USE_CASE_ACCEPTANCE_MATRIX.md`, `70_BORDER_BAND_COMPLETION_SPEC.md`, Issue #12, PR #11.
