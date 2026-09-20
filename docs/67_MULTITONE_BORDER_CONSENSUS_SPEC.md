# MTKrita Multi-Tone Border Consensus Specification

## Status
SSOT Extension — Tier-B Border Consensus Contract v1.2

## Purpose
Define TB-005, discovered after TB-004 corrected Candidate B extraction boundaries. Production-like rounded sticker frames may use different green shades, antialiasing or shadow tones on different sides. A border can therefore have strong four-side geometry while failing a single global cross-side color-consensus rule.

## Problem
The inset-border path searches each side independently and the original path requires at least three side candidates to fall within one global color-consensus tolerance. Candidate B demonstrates valid frames where side tones can differ enough that a universal tolerance increase would be unsafe.

The integrated Tier-B run also demonstrated a second distinction that must be explicit: **failure to authorize automatic border cleanup is not the same as evidence that no border exists**. If several strong border-like side candidates exist but fail the multi-tone safety contract, the frame is ambiguous and must route to REVIEW rather than proceed as if border evidence were absent.

Therefore the fix must strengthen geometry and ambiguity evidence rather than weaken global color discrimination.

## Decision
Keep the existing single-tone consensus path unchanged.

Add a **multi-tone four-side fallback** only when the single-tone path does not establish a valid 3+ side consensus.

Add an explicit **border ambiguity / requires-review** signal for strong-but-unauthorized inset evidence. `consensus_mode = none` alone must never be used to mean both “no border evidence” and “border-like evidence rejected by a safety gate.”

## Multi-Tone Fallback Requirements
Automatic multi-tone border evidence may be constructed only when **all four** side candidates exist and each side independently satisfies the configured inset-candidate rules:
- bounded near-edge search;
- minimum visible support;
- minimum long-strip color coverage;
- high visible color purity;
- bounded thickness discovery around that side's own candidate peak.

Additional rules:
1. each side retains its own representative color; no global averaged border color is created;
2. side offsets may differ because rounded-frame placement need not be symmetric in the extracted cell;
3. each side's cleanup mask is generated only from its own bounded spatial band and its own color evidence;
4. each side's inner-contact evidence is calculated against that side's own color;
5. all four side results must survive side construction; otherwise the fallback cannot gain automatic border authority;
6. the normal automatic confidence threshold remains unchanged;
7. any contact risk still requires existing REVIEW/joint-cleanup policy;
8. this fallback never authorizes global color-key deletion;
9. **constructed side thickness must be geometrically coherent**. The current conservative bound is a maximum constructed-thickness spread of **2 px** across four sides;
10. offset asymmetry alone is not a failure because the decorative frame may be shifted within an extracted cell. Geometry coherence does not require equal offsets or centered placement;
11. if thickness coherence fails, automatic cleanup is forbidden and the frame must carry explicit REVIEW-required border ambiguity;
12. if the original single-tone path fails but **three strong differently colored inset side candidates** remain, this is rejected multi-tone evidence and must route to REVIEW, not “no border”;
13. if four candidates exist but purity/support/side-construction/completeness fails, the rejected evidence must remain distinguishable from true border absence whenever the detector has enough strong structure to suspect a decorative frame.

## Border Ambiguity Contract
`BorderDetection` (or the equivalent provider result) shall expose an explicit validated signal such as:
- `requires_review: bool`;
- `review_reason: str | None`.

Required semantics:
- true absence / insufficient border-like structure → `requires_review = false`, `consensus_mode = none`;
- authorized single-tone → `requires_review = false`, `consensus_mode = single_tone`;
- authorized four-side multi-tone → `requires_review = false`, `consensus_mode = multi_tone_four_side`;
- strong three-side multi-tone evidence → `requires_review = true`, `consensus_mode = none`;
- four-side evidence rejected for incoherent constructed thickness or other fallback safety gate → `requires_review = true`, `consensus_mode = none`.

Frame-level evidence must propagate both the consensus mode and ambiguity signal/reason. `FramePipeline` must emit REVIEW before metadata removal/smart-fit/export whenever border ambiguity requires review. No destructive cleanup may occur from an ambiguous border result.

## Integrated Corpus Defect Evidence — 2026-09-20
A read-only integrated diagnostic on PR #11 head `35775cd63e621ed60aa67af7a0fd802cc8d47387` used hash-matched owner-held Candidate A/B bytes after TB-004 refined extraction.

Candidate B frame 5 exposed the first false-safe result:
- `border_consensus_mode = multi_tone_four_side`;
- frame status became `AUTO_FIXED`;
- constructed side geometry was `left offset=3 thickness=1`, `top offset=23 thickness=5`, `right offset=22 thickness=5`, `bottom offset=6 thickness=1`;
- visual inspection showed decorative green border residue after automatic border removal.

The v1.1 thickness-coherence gate correctly revoked multi-tone authority for this geometry. A follow-up read-only rerun then exposed a second false-safe state:
- Candidate B frames 3 and 5 returned `border_consensus_mode = none` because incoherent multi-tone geometry was rejected;
- `FramePipeline` interpreted `none` as absence and produced `AUTO_FIXED` through `SMART_FIT` while the decorative border remained;
- source bytes remained immutable in both diagnostics.

This establishes that rejected border-like evidence must route to explicit REVIEW. Merely returning an empty detection is not sufficient.

## Why Four Sides
The existing single-tone path can safely operate with three coherent sides because shared color provides additional consensus evidence.

When cross-side color agreement is intentionally relaxed, MTKrita requires stronger geometric evidence: four independent long side structures and coherent constructed border-band thickness. Three strong differently colored sides are enough to suspect a frame but not enough to authorize deletion; therefore they are a REVIEW condition.

## Evidence
Per-side evidence remains mandatory for authorized sides:
- side id;
- offset;
- thickness;
- representative color;
- visible support;
- color purity;
- confidence;
- contact fraction/ranges.

Border-level evidence shall record:
- consensus mode (`single_tone`, `multi_tone_four_side`, or `none`);
- `border_requires_review`;
- `border_review_reason` when applicable.

The detector must be deterministic for the same immutable input and configuration.

## Prohibited
- increasing universal cross-side color tolerance merely to fit Candidate B;
- accepting multi-tone fallback from only 1–3 sides;
- averaging all side colors into one deletion color;
- skipping contact-risk analysis;
- using border consensus to bypass metadata/joint-cleanup rules;
- interpreting extraction contamination as valid border evidence;
- accepting a four-side fallback when constructed side thickness indicates partial/incomplete border-band ownership;
- weakening the thickness-coherence gate merely to raise corpus automation rate;
- collapsing rejected strong border evidence into ordinary absence and then continuing destructive/automatic processing.

## Required Regression Tests
1. four-side inset border with two clearly separated shade families → detected through `multi_tone_four_side`;
2. same geometry with only three differently colored side candidates → no automatic detection **and REVIEW-required ambiguity**;
3. single-tone 3/4 or 4/4 border → existing single-tone path remains unchanged;
4. one side has insufficient visible support → multi-tone fallback rejected conservatively;
5. same-color artwork touching the inner edge of one multi-tone side → contact risk still raised;
6. deterministic repeat produces identical per-side geometry/colors/evidence;
7. frame evidence propagates border consensus mode;
8. four strong side candidates whose constructed thicknesses are materially inconsistent → no automatic detection and REVIEW-required ambiguity;
9. coherent multi-tone thickness at different side offsets remains eligible, proving the gate does not incorrectly require centered/equal offsets;
10. FramePipeline given REVIEW-required border ambiguity → `FrameStatus.REVIEW`, no `REMOVE_BORDER`, no `SMART_FIT`, no destructive metadata action;
11. true no-border transparent artwork remains able to continue through normal pipeline behavior and is not incorrectly forced to border REVIEW.

## Tier-B Gate
After implementation and Windows CI:
- rerun Candidate A/B after TB-004 refined extraction;
- verify Candidate A does not regress;
- verify Candidate B frame 5 no longer auto-crops partial-tone geometry;
- verify rejected Candidate B frame 3/5 border-like evidence becomes REVIEW rather than AUTO_FIXED-with-residue;
- verify Candidate B border detection improves only where complete four-side evidence exists;
- any remaining badge/artwork/border-band ambiguity remains REVIEW;
- inspect every AUTO_FIXED output for decorative-border residue and silent content loss;
- no threshold relaxation is permitted.

## Repository Hygiene
- representative source bytes remain outside Git history;
- regressions use synthetic fixtures when practical;
- no diagnostic PNG/log/temp output is committed;
- the fallback is part of the existing border provider path, not a duplicate production implementation.

References: `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`, `66_TIER_B_METADATA_AND_EXTRACTION_REFINEMENT_SPEC.md`, Issue #12, PR #11.
