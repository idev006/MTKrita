# MTKrita Multi-Tone Border Consensus Specification

## Status
SSOT Extension — Tier-B Border Consensus Contract v1.0

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
8. this fallback never authorizes global color-key deletion.

## Why Four Sides
The existing single-tone path can safely operate with three coherent sides because shared color provides additional consensus evidence.

When cross-side color agreement is intentionally relaxed, MTKrita requires stronger geometric evidence: four independent long side structures. This prevents one or two artwork strips, text strokes or decorative elements from gaining border authority merely because they are near an edge.

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

## Prohibited
- increasing universal cross-side color tolerance merely to fit Candidate B;
- accepting multi-tone fallback from only 1–3 sides;
- averaging all side colors into one deletion color;
- skipping contact-risk analysis;
- using border consensus to bypass metadata/joint-cleanup rules;
- interpreting extraction contamination as valid border evidence.

## Required Regression Tests
1. four-side inset border with two clearly separated shade families → detected through `multi_tone_four_side`;
2. same geometry with only three differently colored side candidates → fallback does not authorize detection;
3. single-tone 3/4 or 4/4 border → existing single-tone path remains unchanged;
4. one side has insufficient visible support → multi-tone fallback rejected;
5. same-color artwork touching the inner edge of one multi-tone side → contact risk still raised;
6. deterministic repeat produces identical per-side geometry/colors/evidence;
7. frame evidence propagates border consensus mode.

## Tier-B Gate
After implementation and Windows CI:
- rerun Candidate A/B after TB-004 refined extraction;
- verify Candidate A does not regress;
- verify Candidate B border detection improves only where four-side evidence exists;
- any remaining badge/artwork ambiguity remains REVIEW;
- no threshold relaxation is permitted.

## Repository Hygiene
- representative source bytes remain outside Git history;
- regressions use synthetic fixtures when practical;
- no diagnostic PNG/log/temp output is committed;
- the fallback is part of the existing border provider path, not a duplicate production implementation.

References: `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`, `66_TIER_B_METADATA_AND_EXTRACTION_REFINEMENT_SPEC.md`, Issue #12, PR #11.
