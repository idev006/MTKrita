# MTKrita Border Contact Topology and Complete Border-Band Ownership Specification

## Status
SSOT Extension — Tier-B Border Contact Topology Contract v1.1

## Purpose
Define TB-006: the evidence contract required to distinguish decorative-border continuation from real artwork contact after TB-005 has established conservative border geometry.

TB-006 exists because the final integrated Candidate A/B run after Windows CI #351 is safe but over-conservative: all 20 representative frames route to REVIEW. The next step must improve ownership evidence without reducing the existing contact-risk threshold, widening global color tolerance, or guessing destructively.

## Evidence Baseline
The current detector constructs per-side border geometry, then samples the strip immediately inside each detected side. Pixels sufficiently close to the detected side color are recorded as inner contact ranges/fraction.

Representative integrated evidence includes:
- Candidate B frame 1: right inner contact ≈ `0.905`, bottom ≈ `0.809`;
- Candidate B frame 7: left inner contact ≈ `0.921`;
- Candidate B frame 6: top ranges approximately `(34,47)` and `(367,380)`, right approximately `(15,28)` and `(351,364)`;
- Candidate B frame 4: left approximately `(34,46)` and `(363,380)`, right approximately `(34,46)` and `(367,380)`;
- Candidate B frame 9: multiple short ranges near both ends of side strips;
- Candidate A also contains long inner-strip matches on selected sides, including bottom-side contact substantially above the current automatic contact-risk threshold.

These observations identify at least two structurally different phenomena:
1. short endpoint-localized contact consistent with rounded-corner continuation;
2. long parallel contact consistent with an adjacent decorative tone/band that the current side construction has not fully owned.

Neither phenomenon may be treated as safe merely because its color resembles the detected border.

## Locked Safety Rules
TB-006 SHALL preserve all of the following:
- `REVIEW > destructive guess`;
- source image immutability;
- existing automatic border confidence threshold;
- existing contact-risk threshold;
- no increase to universal/global cross-side color tolerance;
- no global color-key deletion;
- no use of corpus identity, filename, frame index, or hardcoded production coordinates as authority;
- no cleanup authorization from one side in isolation when ownership depends on a larger border topology;
- JointCleanupPlanner remains the authority for metadata-owned contact;
- ambiguous/unexplained contact remains REVIEW.

## Contact Classification Model
Each detected border side may expose contact intervals. TB-006 classifies those intervals into explanation classes without deleting pixels by classification alone.

### Class A — Rounded-Corner Geometric Continuation
A contact interval may be explained as rounded-corner continuation only when all conditions hold:
1. the interval is fully contained in the bounded endpoint corner envelope of the current side;
2. the corresponding perpendicular adjacent side is detected;
3. that perpendicular side contains a reciprocal contact interval fully contained in its endpoint envelope for the same physical corner;
4. both intervals come from already-authorized border sides in the same extracted frame;
5. neither interval extends from the endpoint envelope into the central side region;
6. deterministic repeat produces the same explanation.

A corner explanation may reduce *unexplained* contact evidence, but it does not expand crop geometry, side thickness, color tolerance, or the border deletion mask.

### Class B — Adjacent Decorative Border-Band Continuation
A long matching inner interval may indicate that the detected side captured only one tone/ring of a wider decorative border.

Such contact may be explained as decorative-band continuation only when all conditions hold:
1. support is long and parallel to the already detected side;
2. equivalent inward continuation is corroborated by at least one additional non-opposite side, or by a four-side band-completeness model;
3. the inward continuation is spatially bounded to the same near-edge search domain used by border detection;
4. candidate colors remain side-local; no global averaged deletion color is created;
5. the proposed completion produces coherent side-band geometry rather than an isolated strip;
6. real artwork touching the inner edge is not absorbed into the completion envelope;
7. the completed geometry must still pass contact analysis at its new inner boundary;
8. any residual unexplained contact remains REVIEW.

A single long inner strip on one side is **insufficient** to authorize completion or deletion.

### Class C — Metadata-Owned Contact
Contact that overlaps or is immediately adjacent to approved frame-number metadata remains governed by `JointCleanupPlanner` / ADR-028.

TB-006 SHALL NOT bypass metadata detection, exclusion-mask identity binding, local ownership, or SAFE_PLAN requirements.

### Class D — Artwork / Unexplained Contact
Any interval that is not fully explained by Classes A–C remains unexplained contact.

Examples include:
- central inner-edge artwork contact;
- side-local long support without corroborating border-band topology;
- contact extending beyond a derived corner envelope;
- conflicting geometric evidence;
- mixed contact where only part of the interval is explained.

Any unexplained contact whose fraction still meets the existing contact-risk threshold continues to require REVIEW.

## Geometry-Derived Corner Envelope — Phase 1 Locked Rule
TB-006 SHALL NOT replace the current contact-risk threshold or add a new broad frame-percentage trim.

For Phase 1, the corner envelope uses the border detector's **existing bounded inset search depth** (`max_search`) as its only spatial bound. This is already derived from the existing `max_fraction` border-search contract and therefore does not introduce a wider search domain.

For a side of longitudinal length `L`:
- low-end envelope: `[0, max_search)`;
- high-end envelope: `[L - max_search, L)`.

A raw contact interval is eligible for corner explanation only when it is fully contained in one of those envelopes.

Reciprocal-corner requirement:
- top-low ↔ left-low;
- top-high ↔ right-low;
- bottom-low ↔ left-high;
- bottom-high ↔ right-high.

The interval on the current side and at least one raw contact interval on the reciprocal perpendicular side must both be fully contained in their corresponding endpoint envelopes for the same corner. One-sided endpoint evidence is not enough.

Phase 1 SHALL preserve the raw contact evidence and separately record:
- raw contact fraction/ranges;
- corner-explained ranges;
- residual/unexplained ranges;
- residual/unexplained fraction.

The existing contact-risk threshold is then applied to the **residual unexplained fraction**, not lowered or replaced. This permits proven corner geometry to stop contributing false risk while central or long unexplained contact still gates REVIEW.

Phase 1 explicitly does **not** implement Class B band completion. Long strips that leave the endpoint envelope remain unexplained regardless of color similarity.

## Complete Border-Band Ownership — Deferred Beyond Phase 1
TB-006 may extend side thickness only through a dedicated band-completion planner. The current detected side is a seed, not permission to absorb arbitrary same-colored content.

The planner must produce evidence before a wider band can be used:
- original side offset/thickness;
- proposed completed offset/thickness;
- per-layer visible support;
- per-layer side-local color purity;
- cross-side geometric corroboration count;
- whether completion changes the inner boundary;
- contact evidence at the completed inner boundary;
- deterministic reason/status.

Suggested statuses:
- `NOT_NEEDED`;
- `SAFE_COMPLETE`;
- `REVIEW_INSUFFICIENT_CORROBORATION`;
- `REVIEW_ARTWORK_CONTACT`;
- `REVIEW_GEOMETRY_CONFLICT`.

Unsupported Class B cases remain REVIEW.

## Evidence Contract
For each authorized inset border side, Phase 1 evidence shall preserve or expose:
- `raw_contact_fraction`;
- `raw_contact_ranges`;
- `explained_corner_ranges`;
- residual `contact_fraction` / `contact_ranges` as the canonical unexplained contact consumed by existing safety gates;
- `contact_risk` computed from residual contact using the unchanged threshold.

Frame evidence shall propagate these fields inside existing per-side border evidence. Existing JointCleanupPlanner logic continues to consume residual `contact_fraction` / `contact_ranges`, so corner geometry cannot be double-counted as metadata ownership.

Future band-completion evidence may add:
- `border_contact_explained_band_ranges`;
- `border_contact_topology_status`;
- proposed/completed side-band geometry.

## Automatic Cleanup Authority
TB-006 does not independently grant cleanup authority.

Automatic border cleanup remains allowed only when:
1. border detection/consensus itself is authorized;
2. border ambiguity is false;
3. confidence remains at or above the existing automatic threshold;
4. residual contact is absent/below existing risk threshold or is subsequently fully explained through approved metadata joint planning;
5. any future geometry completion has its own validated SAFE status;
6. no unexplained artwork contact remains.

If any condition fails, return REVIEW.

## Required Synthetic Regression Matrix
Before/with production implementation, tests SHALL cover:

1. **Reciprocal rounded-corner contact**
   - coherent inset border;
   - raw inner contact exists only in endpoint envelopes on two perpendicular sides for the same corner;
   - both reciprocal ranges are classified as corner continuation;
   - raw evidence remains preserved;
   - residual risk is recomputed with unchanged threshold.

2. **Rounded corner plus central artwork contact**
   - reciprocal corner contact is present;
   - same-colored artwork touches the inner boundary in the central region;
   - endpoint ranges may be explained;
   - central interval remains residual and frame remains REVIEW.

3. **Corner-like interval without reciprocal perpendicular contact**
   - endpoint contact exists on one side only;
   - interval remains unexplained; no false corner ownership.

4. **Endpoint interval crossing the search-domain boundary**
   - contact begins in endpoint envelope but extends into central region;
   - entire interval remains unexplained rather than being partially clipped/explained.

5. **Single long parallel continuation**
   - one side has a long inner same/near-tone strip;
   - even if it includes an endpoint, it leaves the endpoint envelope;
   - Phase 1 must not authorize band completion; REVIEW.

6. **Metadata adjacency**
   - corner explanation removes only proven reciprocal endpoint intervals;
   - frame-number badge ownership still requires JointCleanupPlanner;
   - remote/corner/artwork pixels are not pulled into metadata ownership.

7. **No-border transparent artwork**
   - no strong border evidence;
   - TB-006 must not create false REVIEW solely from arbitrary near-edge content.

8. **Determinism**
   - repeated runs on identical immutable input produce identical raw/explained/residual ranges and risk state.

9. **Existing safety regressions**
   - TB-001 through TB-005, single-tone behavior, multi-tone ambiguity, and true artwork-contact tests remain unchanged unless SSOT explicitly supersedes them.

10. **Future Class B tests (required before band completion is implemented)**
   - corroborated wider decorative band;
   - single-side long strip refusal;
   - decorative band plus artwork touch refusal;
   - completed inner boundary must be clean before SAFE_COMPLETE.

## Tier-B Acceptance Procedure
After a TB-006 implementation checkpoint passes Windows Ruff + pytest:
1. hash-match Candidate A/B source bytes;
2. run refined extraction + full frame pipeline read-only;
3. compare per-frame status against the previous 10 REVIEW / 10 REVIEW baseline;
4. inspect every new PASS/AUTO_FIXED frame visually for border residue, content loss, numeral residue and accidental artwork deletion;
5. record raw/explained/residual contact evidence;
6. reject any change whose automation gain is obtained by threshold relaxation or unexplained deletion;
7. keep M2 gate open until representative supported cases auto-process correctly and owner acceptance is obtained.

## Non-Goals
TB-006 Phase 1 does not:
- implement decorative-band completion;
- implement M3 opaque-background removal;
- redesign metadata ownership;
- alter worker/MainBoard authority;
- relax LINE export rules;
- permit UI-driven business logic;
- optimize automation rate at the expense of safety.

## Repository Hygiene
- Candidate A/B bytes remain outside Git history;
- synthetic fixtures are generated in tests rather than committed production PNGs where practical;
- diagnostic images/evidence files remain untracked runtime artifacts;
- no ZIP/log/DB/cache/temp artifacts are committed.

References: `43_CURRENT_IMPLEMENTATION_STATUS_AND_KNOWN_GAPS.md`, `60_PLATFORM_FOUNDATION_IMPLEMENTATION_STATUS.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`, `67_MULTITONE_BORDER_CONSENSUS_SPEC.md`, ADR-023, ADR-028, Issue #12, PR #11.
