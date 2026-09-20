# MTKrita Tier-B Transparent Corpus Evidence

## Status
Verification Evidence — Tier-B Transparent Corpus Diagnostic v1.3

## Purpose
Record production/representative transparent-sheet evidence without committing user/source image bytes. This document captures observed behavior of PR #11 and the evidence-backed hardening required before M2 acceptance closes.

## Corpus Identity
Two owner-available representative transparent Sticker Sheets are used as Tier-B evidence.

### Candidate A
- logical name: `Thai-Inspired Blessings Sticker Sheet.png`
- SHA-256: `4e86ac089a8342ac2c7a3ab985c7e2b41deb091601297c9b2fa55777ceb4e906`
- dimensions: 1986 × 792
- mode: RGBA
- layout: 2 rows × 5 columns
- meaningful source transparency: yes
- source bytes: not committed

### Candidate B
- logical name: `Thai Elderly Woman Blessing Sticker Sheet.png`
- SHA-256: `13e8755ef4056bf04021ee8e86c733fa883f5617bb6a6ad02bc12e74d08c84d8`
- dimensions: 1976 × 796
- mode: RGBA
- layout: 2 rows × 5 columns
- meaningful source transparency: yes
- source bytes: not committed

## Safety Baseline
The initial Tier-B diagnostic routed all 20 representative frames to REVIEW before destructive cleanup. No silent automatic deletion path was observed. The dominant defect class was over-review, so the hardening strategy is to improve evidence quality/topology while preserving thresholds and REVIEW-first behavior.

## Verified Hardening Checkpoints

### TB-001 — Rounded Border Evidence
Implemented and Windows-CI verified.
- visible support is separated from visible color purity;
- transparent rounded corners do not count as wrong-color pixels;
- minimum support, multi-side consensus and contact-risk policy remain mandatory;
- automatic threshold is unchanged;
- `visible_support` and `color_purity` are evidence fields.

### TB-002 — Post-Exclusion Local Metadata Ownership
Implemented and Windows-CI verified.
- destructive ownership is based on post-exclusion local isolation rather than raw-group membership alone;
- anchor center remains 60% of the metadata search zone;
- local candidate extent may occupy up to 90% of the search zone while remaining bounded;
- remote fragments separated by the approved border exclusion are preserved and counted as evidence;
- remote pixels never enter the metadata deletion mask;
- selected components with a non-excluded path beyond the local envelope remain REVIEW;
- `ignored_remote_fragment_count` is propagated.

Windows CI #324 at commit `cd63c20b8b0f8f829481dcfc92555ce5e7254246` passed Ruff + pytest.

### TB-003 — Alpha-Visible Metadata Topology for Transparent Sources
Implemented and Windows-CI verified.
- meaningfully transparent metadata analysis uses `alpha_visible` topology as the primary raw support;
- effectively opaque input retains `rgb_background_distance` fallback behavior;
- alpha topology does not itself grant deletion authority;
- anchor/local/dominance/exclusion/joint-planner rules remain mandatory;
- `metadata_segmentation_basis` and alpha visibility threshold are propagated into frame evidence;
- no automatic threshold was lowered.

Windows CI #328 and #329 passed Ruff + pytest for behavior and evidence propagation.

Corpus effect after TB-003:
- Candidate A metadata eligibility improved further (5 / 10 frames reached the current joint-planning candidate path during isolated diagnostic);
- Candidate B remained constrained by other evidence defects, proving TB-003 should not be stretched beyond its intended responsibility.

### TB-004 — Bounded Visual Separator Refinement
Implemented and Windows-CI verified.
- configured proportional grid remains the deterministic initial hypothesis;
- refinement searches only within ±16 px of predicted internal separators;
- qualifying separators require strong transparent-gutter support;
- if the prediction already lies inside a qualifying gutter, it remains unchanged;
- absent/ambiguous separator evidence fails closed;
- crop boundaries change only; source pixels are never resampled.

Windows CI #330 at commit `76359438bbfe2af0e8f2a8da4649308db204b21e` passed Ruff + pytest.

Representative evidence:
- Candidate A: proportional separators are already close; one internal x separator refines by approximately -1 px, horizontal separator unchanged;
- Candidate B: problematic x separators refine from approximately `1186 → 1174` and `1581 → 1576`; horizontal separator remains `398`;
- the prior neighboring-frame contamination at Candidate B frame boundaries is therefore classified and addressed as extraction geometry rather than a border-detector defect.

### TB-005 — Conservative Four-Side Multi-Tone Border Consensus
Implemented and Windows-CI verified.
- existing edge and single-tone inset paths remain primary;
- multi-tone fallback is allowed only when all four sides independently provide strong near-edge border evidence;
- each side keeps its own observed border color; no global color tolerance is widened;
- three-side multi-tone evidence cannot authorize the fallback;
- insufficient per-side visible support cannot authorize the fallback;
- per-side contact-risk detection remains mandatory and can still force REVIEW;
- repeated detection over identical input is regression-tested for deterministic evidence;
- `BorderDetection.consensus_mode` records `edge`, `single_tone`, `multi_tone_four_side`, or `none` at provider level;
- frame-level evidence now propagates the explicit `border_consensus_mode` field.

Windows CI #333 at commit `d86862d05cf9ae4ddbbc4243c3d0eac657484535` passed Ruff + pytest for the initial TB-005 behavior checkpoint.

Windows CI #340 at commit `55749b2f378dcd703f6e2baa907eaae144efb093` passed Ruff + pytest after completing the TB-005 evidence/regression contract, including:
- four-side multi-tone success;
- three-side refusal;
- insufficient-side-support refusal;
- contact-risk preservation;
- explicit single-tone-mode regression;
- deterministic repeat evidence;
- frame evidence propagation of `border_consensus_mode`.

No detection threshold or global color tolerance was relaxed for this completion checkpoint.

Representative diagnostic after refined extraction:
- Candidate B frames requiring different side tones can now enter `multi_tone_four_side` rather than being rejected solely by cross-side color disagreement;
- frames whose colors still satisfy the original consensus continue to use `single_tone`;
- the fallback therefore supplements rather than replaces the original path.

## Remaining Tier-B Work
M2 is substantially hardened but the Tier-B acceptance gate is not yet closed. Remaining work is now concentrated in final integrated corpus acceptance and any defects exposed by that run.

Required closure run:
1. obtain the owner-held Candidate A/B bytes and verify their SHA-256 values before execution;
2. execute the current integrated PR #11 head against those hash-matched bytes using the approved refined extraction path;
3. record per-frame extraction, border consensus mode, metadata evidence, joint-cleanup evidence and PASS/REVIEW/FAIL;
4. inspect outputs for silent content loss, edge damage, numeral residue, border residue and accidental artwork deletion;
5. fix only evidence-backed defects and preserve REVIEW-first policy;
6. obtain owner acceptance for the representative corpus result.

A previous diagnostic or hash-only record is not a substitute for this final integrated rerun. If the source bytes are not available in the execution environment, the acceptance gate remains open rather than being inferred from synthetic CI.

## Gate Status
**M2 Tier-B: NOT YET ACCEPTED, but TB-001 through TB-005 implementation/regression hardening is complete at the current checkpoint.**

The remaining blocker is the final integrated Tier-B acceptance/evidence pass on the hash-matched Candidate A/B source bytes, not a known unbounded destructive path.

## Repository Safety
- candidate source bytes remain outside Git history;
- only hashes, dimensions, aggregate measurements and defect evidence are versioned by default;
- temporary diagnostic outputs remain outside tracked runtime/source directories;
- no production threshold is changed without SSOT + regression evidence;
- corpus diagnostics are read-only;
- no generated PNG/ZIP/database/log/cache/temp/build artifacts are intentionally committed.

References: `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `66_TIER_B_METADATA_AND_EXTRACTION_REFINEMENT_SPEC.md`, `67_MULTITONE_BORDER_CONSENSUS_SPEC.md`, ADR-023, ADR-028, Issue #12, PR #11.
