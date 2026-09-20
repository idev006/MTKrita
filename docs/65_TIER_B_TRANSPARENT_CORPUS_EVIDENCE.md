# MTKrita Tier-B Transparent Corpus Evidence

## Status
Verification Evidence — Tier-B Transparent Corpus Diagnostic v1.4

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
The initial Tier-B diagnostic routed all 20 representative frames to REVIEW before destructive cleanup. The dominant defect class is over-review. Hardening must improve evidence quality/topology while preserving thresholds and REVIEW-first behavior.

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
- remote fragments separated by approved border exclusion remain preserved;
- remote pixels never enter the metadata deletion mask;
- ambiguous non-excluded connectivity remains REVIEW;
- `ignored_remote_fragment_count` is propagated.

Windows CI #324 at commit `cd63c20b8b0f8f829481dcfc92555ce5e7254246` passed Ruff + pytest.

### TB-003 — Alpha-Visible Metadata Topology for Transparent Sources
Implemented and Windows-CI verified.
- meaningfully transparent metadata analysis uses `alpha_visible` topology as primary raw support;
- effectively opaque input retains RGB-background fallback;
- alpha topology does not itself grant deletion authority;
- anchor/local/dominance/exclusion/joint-planner rules remain mandatory;
- evidence records segmentation basis and alpha visibility threshold;
- no automatic threshold was lowered.

Windows CI #328 and #329 passed Ruff + pytest.

### TB-004 — Bounded Visual Separator Refinement
Implemented and Windows-CI verified.
- configured proportional grid remains deterministic initial hypothesis;
- refinement is bounded to ±16 px around predicted internal separators;
- qualifying separators require strong transparent-gutter support;
- source pixels are never resampled.

Windows CI #330 at commit `76359438bbfe2af0e8f2a8da4649308db204b21e` passed Ruff + pytest.

Representative extraction evidence remains stable:
- Candidate A x edges: predicted `(0, 397, 794, 1192, 1589, 1986)` → refined `(0, 397, 793, 1192, 1589, 1986)`; y separator unchanged at `396`;
- Candidate B x edges: predicted `(0, 395, 790, 1186, 1581, 1976)` → refined `(0, 395, 790, 1174, 1576, 1976)`; y separator unchanged at `398`;
- Candidate B offsets therefore preserve the evidence-backed `1186→1174` and `1581→1576` corrections.

### TB-005 — Conservative Four-Side Multi-Tone Border Consensus
The original multi-tone fallback and subsequent corpus-driven safety hardening are implemented and Windows-CI verified.

Initial behavior:
- existing edge and single-tone inset paths remain primary;
- no global cross-side color tolerance increase;
- four strong sides are required for multi-tone authority;
- own side colors/evidence are retained;
- contact risk remains mandatory;
- `border_consensus_mode` is propagated.

Windows CI #333 and #340 passed the initial TB-005 behavior/evidence regressions.

#### TB-005 integrated defect 1 — incomplete multi-tone band ownership
A read-only corpus run exposed Candidate B frame 5 as falsely `AUTO_FIXED`: side thicknesses were `1/5/5/1` and visual output retained decorative green border. This demonstrated that four strong candidate lines alone do not prove complete border-band ownership.

SSOT v1.1 added a conservative constructed-thickness coherence gate (maximum spread 2 px) while permitting asymmetric side offsets. No threshold or global color tolerance was relaxed.

Windows CI #347 passed Ruff + pytest after the geometry-coherence fix and regression coverage.

#### TB-005 integrated defect 2 — rejected border evidence collapsed into absence
The v1.1 rerun correctly revoked multi-tone authority from Candidate B frames 3 and 5, but `consensus_mode = none` was then interpreted as ordinary border absence. Both frames proceeded to `AUTO_FIXED` through `SMART_FIT` while their decorative border remained.

SSOT v1.2 therefore distinguishes true absence from strong-but-rejected border evidence:
- provider exposes explicit REVIEW-required ambiguity and reason;
- frame evidence records `border_requires_review` and `border_review_reason`;
- FramePipeline returns `BORDER.AMBIGUOUS` before border removal, metadata mutation or smart fit;
- three-side differently colored border evidence is also explicit REVIEW rather than silent absence.

Windows CI #351 at commit `7e93b94533fd66652d90c20a64078eb3a840ac3e` passed Ruff + pytest for the ambiguity/evidence contract.

No automatic safety threshold was lowered during TB-005 hardening.

## Integrated Tier-B Run — Current Safe Boundary
A read-only integrated run was executed after CI #351 using the hash-matched Candidate A/B source bytes and refined extraction.

Source integrity:
- Candidate A SHA-256 before/after remained `4e86ac089a8342ac2c7a3ab985c7e2b41deb091601297c9b2fa55777ceb4e906`;
- Candidate B SHA-256 before/after remained `13e8755ef4056bf04021ee8e86c733fa883f5617bb6a6ad02bc12e74d08c84d8`;
- source bytes were not written to Git and were not mutated by the run.

Per-corpus result:
- Candidate A: `REVIEW 10 / 10`;
- Candidate B: `REVIEW 10 / 10`;
- `PASS = 0`, `AUTO_FIXED = 0`, `FAIL = 0` across the 20-frame representative corpus;
- therefore no current representative frame is silently destructively modified.

Candidate A classification:
- all 10 frames use the existing `single_tone` border path;
- 5 frames reach anchored metadata evidence but joint cleanup remains REVIEW because border contact exists outside approved metadata adjacency;
- the remaining frames remain REVIEW because metadata cleanup ownership is absent/ambiguous after border analysis exclusion.

Candidate B classification:
- frames 3 and 5: `border_consensus_mode = none`, `border_requires_review = true`, reason `four-side multi-tone thickness geometry is incoherent`, final finding `BORDER.AMBIGUOUS`;
- the other 8 frames remain `single_tone` and REVIEW through conservative border-contact/joint-cleanup gates;
- no B3/B5 smart-fit or border crop occurs after the ambiguity fix.

## Next Evidence-Backed Defect Class
The integrated run closes the known silent `AUTO_FIXED` border-residue path but leaves substantial over-review.

The next defect class is **border contact topology / incomplete border-band completion**, not threshold insufficiency. Representative evidence includes:
- Candidate B frame 1 right-side inner contact fraction ≈ `0.905` and bottom ≈ `0.809`;
- Candidate B frame 7 left-side inner contact fraction ≈ `0.921`;
- several other frames show contact ranges concentrated near rounded corners while current contact trimming is narrower than the observed rounded-corner span;
- Candidate A also shows large matching inner-strip ranges on selected sides, including bottom-side contact well above the automatic risk threshold.

These observations are diagnostic only. They do **not** authorize lowering the contact-risk threshold, globally widening color tolerance, or deleting long matching strips. The next hardening step must separate:
1. genuine adjacent decorative-border tone / rounded-corner continuation;
2. metadata adjacency that JointCleanupPlanner can own;
3. real artwork touching the inner border.

Until that ownership model is specified and regression-proven, REVIEW remains correct.

## Gate Status
**M2 Tier-B: NOT ACCEPTED.**

Safety improved: the current representative run has no automatic destructive output and the known B5 border-residue auto-fix path is closed. However, acceptance cannot close while all 20 representative frames remain REVIEW and supported decorative border/metadata cleanup has not demonstrated intended automatic behavior on the integrated corpus.

Issue #12 and M2 / Issue #2 must remain open.

## Repository Safety
- candidate source bytes remain outside Git history;
- only hashes, dimensions, aggregate measurements and defect evidence are versioned;
- temporary diagnostic outputs remain outside tracked runtime/source directories;
- no production threshold is changed without SSOT + regression evidence;
- corpus diagnostics are read-only;
- no generated PNG/ZIP/database/log/cache/temp/build artifacts are intentionally committed.

References: `35_INTERFACE_AND_STAGE_CONTRACTS.md`, `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `66_TIER_B_METADATA_AND_EXTRACTION_REFINEMENT_SPEC.md`, `67_MULTITONE_BORDER_CONSENSUS_SPEC.md`, ADR-023, ADR-028, Issue #12, PR #11.
