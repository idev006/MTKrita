# MTKrita Opaque Background Removal Specification

## Status
SSOT Extension — M3 Phase 1 Uniform Edge-Connected Background Removal v1.0

## Product Requirement
For sticker-sheet frames whose source background is opaque, MTKrita must produce a transparent-background PNG while preserving sticker artwork, Thai text, props, white outlines, enclosed dark details, and any disconnected sticker components.

This capability is required for UC-07 and is part of the product-level acceptance target defined in `69_USE_CASE_ACCEPTANCE_MATRIX.md`.

## Scope of Phase 1
Phase 1 supports opaque frames whose background is approximately uniform and connected to the image boundary. The initial representative owner corpus uses a near-black background surrounding sticker artwork and frame decoration.

The algorithm is intentionally conservative and deterministic. It does not attempt semantic subject segmentation.

## Locked Safety Rules
- Source pixels are immutable.
- Background removal may affect only pixels proven to belong to the edge-connected background component, plus a bounded anti-alias fringe adjacent to that component.
- Enclosed dark pixels are not background merely because their color resembles the background. This preserves black/brown text and interior artwork details.
- No global color-key deletion is allowed.
- No opaque frame may be reported automatic unless background eligibility is proven.
- If boundary evidence is inconsistent or removal would consume excessive content, route to REVIEW.
- Existing M2 border and metadata safety contracts remain in force after transparency conversion.
- `REVIEW > destructive guess` remains mandatory.

## Eligibility
An opaque frame is eligible for Phase-1 automatic background removal only when:
1. the source route is `REMOVE_BACKGROUND`;
2. the dominant boundary/background sample is sufficiently dark or otherwise sufficiently uniform;
3. the boundary-connected candidate covers a plausible background fraction;
4. removal leaves visible foreground content;
5. the removed region is connected to the image boundary;
6. the removed ratio does not exceed the configured safety ceiling.

The first implementation SHALL optimize for the owner acceptance corpus: near-black, edge-connected background.

## Algorithm
1. Convert source to RGB without changing source bytes.
2. Estimate dark-background eligibility from boundary samples.
3. Build a candidate background mask using a conservative per-pixel darkness threshold.
4. Compute connected components in the candidate mask.
5. Keep only components that touch the image boundary.
6. Set those proven background pixels to alpha 0.
7. Build a bounded 1–2 px fringe around proven background.
8. Only for low-chroma/dark fringe pixels, derive partial alpha from brightness to reduce black halos.
9. Preserve all non-background RGB values unchanged.
10. Record deterministic evidence and source hash.

## Required Evidence
- source size and source mode;
- background model kind;
- boundary dark fraction;
- hard removed pixel count and ratio;
- fringe adjusted pixel count;
- remaining visible pixel count and ratio;
- resulting meaningful transparency ratio;
- deterministic mask SHA-256;
- status and reasons.

## Status
- `NOT_ELIGIBLE`
- `SAFE_REMOVE`
- `REVIEW`

Only `SAFE_REMOVE` may be applied automatically.

## Interaction with M2 Border Removal
For opaque sheets with a colored frame border on a dark background, M3 Phase 1 runs before automatic border cleanup for the frame. Once the edge-connected opaque background becomes transparent, the existing transparent-route border topology can analyze and remove the frame border using its normal safety gates.

The original source route remains part of evidence, but downstream processing may operate on the newly transparent working copy.

## Frame Number
Removing frame-number badges remains optional. Background removal must not depend on frame-number detection. Existing metadata cleanup may remove the badge when its safety contract is satisfied; otherwise the number may remain.

## Required Tests
1. uniform black background around bright artwork -> SAFE_REMOVE;
2. black text enclosed by white sticker artwork remains opaque;
3. disconnected foreground islands remain opaque;
4. non-uniform/noisy boundary -> REVIEW;
5. almost-all-background/empty foreground -> REVIEW;
6. excessive removal -> REVIEW;
7. transparent source -> NOT_ELIGIBLE/no mutation;
8. deterministic output/mask hash;
9. source image immutability;
10. integration: opaque black frame -> transparency -> border cleanup path can continue.

## Owner Acceptance Corpus
The four owner-supplied 1536×613 sticker sheets (2 rows × 5 columns each, 40 stickers total) are the first M3 product acceptance corpus. Source bytes are read-only and are never committed to Git history.

Acceptance requires:
- 10 extracted frames per sheet;
- frame border removed;
- opaque black background converted to transparency;
- artwork/text/props visibly preserved;
- frame number may remain unless safely removable;
- final PNGs visually inspected and presented to the owner.

References: `04_IMAGE_PROCESSING_PIPELINE.md`, `23_SUPPORTED_INPUT_ARCHETYPES.md`, `41_M2_M3_IMPLEMENTATION_PLAN.md`, `69_USE_CASE_ACCEPTANCE_MATRIX.md`, `73_CLOSED_RING_BORDER_TOPOLOGY_SPEC.md`, `74_SPATIAL_RING_METADATA_JOINT_CLEANUP_SPEC.md`.
