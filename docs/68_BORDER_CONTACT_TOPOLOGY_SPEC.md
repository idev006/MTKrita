# MTKrita Border Contact Topology and Complete Border-Band Ownership Specification

## Status
SSOT Extension — Tier-B Border Contact Topology Contract v1.0

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
1. the interval touches the low or high endpoint zone of the current side;
2. the corresponding perpendicular adjacent side is detected and independently high-confidence;
3. the perpendicular side geometry reaches the same corner in the same extracted frame;
4. the explanation envelope is derived from detected border geometry, not from a broad fixed percentage of the frame;
5. the interval does not extend beyond that bounded corner envelope into the central side region;
6. deterministic repeat produces the same explanation.

A corner explanation may reduce *unexplained* contact evidence, but it does not by itself expand the deletion/crop geometry.

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

Any non-zero unexplained contact that still satisfies existing contact-risk policy continues to require REVIEW.

## Geometry-Derived Corner Envelope
TB-006 SHALL NOT replace the current corner trimming with a broad arbitrary percentage.

The corner envelope must be derived from border evidence available on the two sides meeting at a corner. Candidate inputs include:
- each side offset;
- each side thickness;
- perpendicular side offset/thickness;
- the intersection of their bounded side bands;
- contiguous visible support around that intersection.

The first implementation should be conservative: explain only endpoint-localized ranges for which the adjacent perpendicular side demonstrably owns the corresponding corner. If exact ownership cannot be established, leave the interval unexplained.

## Complete Border-Band Ownership
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

The first implementation may support only a strict subset (for example, corner explanation without band completion). Unsupported cases must remain REVIEW rather than being forced through.

## Evidence Contract
Frame-level evidence shall eventually include deterministic fields sufficient to audit the decision, for example:
- `border_contact_total_fraction` per side (existing per-side contact remains canonical);
- `border_contact_explained_corner_ranges`;
- `border_contact_explained_band_ranges`;
- `border_contact_metadata_ranges` or equivalent JointCleanupPlanner evidence;
- `border_contact_unexplained_ranges`;
- `border_contact_unexplained_fraction`;
- `border_contact_topology_status`;
- optional band-completion geometry/status when attempted.

Names may be adjusted to fit existing models, but the semantic distinction between explained and unexplained contact is mandatory.

## Automatic Cleanup Authority
TB-006 does not independently grant cleanup authority.

Automatic border cleanup remains allowed only when:
1. border detection/consensus itself is authorized;
2. border ambiguity is false;
3. confidence remains at or above the existing automatic threshold;
4. contact is either absent or completely explained by approved topology/metadata planning;
5. any geometry completion has its own validated SAFE status;
6. no unexplained artwork contact remains.

If any condition fails, return REVIEW.

## Required Synthetic Regression Matrix
Before/with production implementation, tests SHALL cover:

1. **Rounded corner only**
   - coherent rounded/inset border;
   - inner matching contact exists only at both endpoints;
   - perpendicular sides corroborate both corners;
   - endpoint contact is classified as geometric continuation;
   - no central contact remains.

2. **Rounded corner plus central artwork contact**
   - same border/corner geometry;
   - same-colored artwork touches the inner boundary in the central region;
   - corner intervals may be explained;
   - central interval remains unexplained and frame remains REVIEW.

3. **Corner-like interval without perpendicular side**
   - endpoint contact exists;
   - adjacent side is absent/insufficient;
   - interval remains unexplained; no false corner ownership.

4. **Single long parallel continuation**
   - one side has a long inner same/near-tone strip;
   - no corroborating adjacent-side band evidence;
   - must not authorize band completion; REVIEW.

5. **Corroborated wider decorative band**
   - at least two adjacent sides contain coherent inward decorative continuation;
   - proposed completion remains within bounded near-edge domain;
   - completed inner boundary is clean;
   - only then may a future SAFE_COMPLETE path be considered.

6. **Decorative band plus artwork touch**
   - otherwise coherent completed band;
   - artwork touches the completed inner boundary;
   - contact remains REVIEW.

7. **Metadata adjacency**
   - frame-number badge explains only its approved contact through JointCleanupPlanner;
   - remote/corner/artwork pixels are not pulled into metadata ownership.

8. **No-border transparent artwork**
   - no strong border evidence;
   - TB-006 must not create false REVIEW solely from arbitrary near-edge content.

9. **Determinism**
   - repeated runs on identical immutable input produce identical topology evidence/ranges/status.

10. **Existing safety regressions**
   - TB-001 through TB-005, single-tone behavior, multi-tone ambiguity, and true artwork-contact tests remain unchanged unless SSOT explicitly supersedes them.

## Tier-B Acceptance Procedure
After a TB-006 implementation checkpoint passes Windows Ruff + pytest:
1. hash-match Candidate A/B source bytes;
2. run refined extraction + full frame pipeline read-only;
3. compare per-frame status against the previous 10 REVIEW / 10 REVIEW baseline;
4. inspect every new PASS/AUTO_FIXED frame visually for border residue, content loss, numeral residue and accidental artwork deletion;
5. record explained/unexplained contact evidence;
6. reject any change whose automation gain is obtained by threshold relaxation or unexplained deletion;
7. keep M2 gate open until representative supported cases auto-process correctly and owner acceptance is obtained.

## Non-Goals
TB-006 does not:
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
