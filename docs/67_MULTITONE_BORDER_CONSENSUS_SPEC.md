# MTKrita Multi-Tone Border Consensus Specification

## Status
SSOT Extension — Tier-B Border Consensus Contract v1.1

## Purpose
Define TB-005, discovered after TB-004 corrected Candidate B extraction boundaries. Production-like rounded sticker frames may use different green shades, antialiasing or shadow tones on different sides. A border can therefore have strong four-side geometry while failing a single global cross-side color-consensus rule.

## Problem
The current inset-border path first searches each side independently, then requires at least three side candidates to fall within one global color-consensus tolerance. Candidate B demonstrates valid frames where:
- each side individually has high visible support and high color purity;
- all four sides form the visual decorative frame;
- top/left and bottom/right may belong to different shade families;
- increasing one universal color tolerance would risk merging unrelated artwork into border evidence.

Therefore the fix must strengthen geometry evidence rather than weaken global color discrimination.

## Decision
Keep the existing single-tone consensus path unchanged.

Add a **multi-tone four-side fallback** only when the single-tone path does not establish a valid 3+ side consensus.

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
5. all four side results must survive side construction; otherwise the fallback yields no automatic border consensus;
6. the normal automatic confidence threshold remains unchanged;
7. any contact risk still requires existing REVIEW/joint-cleanup policy;
8. this fallback never authorizes global color-key deletion;
9. **constructed side thickness must be geometrically coherent**. The multi-tone fallback may not auto-authorize a crop when one or more sides resolve to only a thin partial tone while other sides resolve to a materially wider decorative band. The current conservative bound is a maximum constructed-thickness spread of **2 px** across the four sides;
10. offset asymmetry alone is not a failure because the decorative frame may be shifted within an extracted cell. Geometry coherence therefore does **not** require equal offsets or centered placement;
11. if thickness coherence fails, the fallback returns no automatic border detection and the frame remains on the non-destructive path. Future improvement may replace this fail-closed rule only with stronger evidence for complete multi-tone band ownership; it must not be achieved by widening global color tolerance.

## Integrated Corpus Defect Evidence — 2026-09-20
A read-only integrated diagnostic on PR #11 head `35775cd63e621ed60aa67af7a0fd802cc8d47387` used hash-matched owner-held Candidate A/B bytes after TB-004 refined extraction.

Candidate B frame 5 exposed a false-safe multi-tone result:
- `border_consensus_mode = multi_tone_four_side`;
- frame status became `AUTO_FIXED`;
- constructed side geometry was `left offset=3 thickness=1`, `top offset=23 thickness=5`, `right offset=22 thickness=5`, `bottom offset=6 thickness=1`;
- visual inspection showed decorative green border residue after automatic border removal;
- source bytes remained immutable;
- no safety threshold was lowered.

This is classified as an **incomplete multi-tone band ownership / geometry coherence defect**, not an extraction defect. The correct response is fail-closed REVIEW/no automatic crop until complete side geometry is supported.

The same diagnostic showed Candidate B frame 3 entering `multi_tone_four_side` with similarly incoherent constructed thickness, so both cases must be prevented from gaining automatic multi-tone authority until geometry is complete.

## Why Four Sides
The existing single-tone path can safely operate with three coherent sides because shared color provides additional consensus evidence.

When cross-side color agreement is intentionally relaxed, MTKrita requires stronger geometric evidence: four independent long side structures **and coherent constructed border-band thickness**. This prevents one or two artwork strips, shadows, partial tone rings or decorative elements from gaining border authority merely because they are near an edge.

## Evidence
Per-side evidence remains mandatory:
- side id;
- offset;
- thickness;
- representative color;
- visible support;
- color purity;
- confidence;
- contact fraction/ranges.

Border-level evidence shall additionally record the consensus mode:
- `single_tone`;
- `multi_tone_four_side`;
- `none`.

The detector must be deterministic for the same immutable input and configuration.

## Prohibited
- increasing universal cross-side color tolerance merely to fit Candidate B;
- accepting multi-tone fallback from only 1–3 sides;
- averaging all side colors into one deletion color;
- skipping contact-risk analysis;
- using border consensus to bypass metadata/joint-cleanup rules;
- interpreting extraction contamination as valid border evidence;
- accepting a four-side fallback when constructed side thickness indicates only partial/incomplete border-band ownership;
- weakening the thickness-coherence gate merely to raise the corpus automation rate.

## Required Regression Tests
1. four-side inset border with two clearly separated shade families → detected through `multi_tone_four_side`;
2. same geometry with only three differently colored side candidates → fallback does not authorize detection;
3. single-tone 3/4 or 4/4 border → existing single-tone path remains unchanged;
4. one side has insufficient visible support → multi-tone fallback rejected;
5. same-color artwork touching the inner edge of one multi-tone side → contact risk still raised;
6. deterministic repeat produces identical per-side geometry/colors/evidence;
7. frame evidence propagates border consensus mode;
8. four strong side candidates whose constructed thicknesses are materially inconsistent → multi-tone fallback rejected / `none`;
9. coherent multi-tone thickness at different side offsets remains eligible, proving that the gate does not incorrectly require centered/equal offsets.

## Tier-B Gate
After implementation and Windows CI:
- rerun Candidate A/B after TB-004 refined extraction;
- verify Candidate A does not regress;
- verify Candidate B no longer auto-crops the frame-5 partial-tone geometry;
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
