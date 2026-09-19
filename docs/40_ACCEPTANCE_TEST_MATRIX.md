# MTKrita Acceptance Test Matrix

## Status
SSOT — Acceptance Verification Baseline v1.1

## Purpose
กำหนด objective acceptance tests สำหรับ capability สำคัญของ MTKrita เพื่อให้ทีมพัฒนาและ QA ใช้เกณฑ์เดียวกันก่อนปิด work package / milestone

## Test Outcome Vocabulary
- PASS — expected behavior proven
- REVIEW — ambiguity handled safely as designed
- FAIL — requirement not satisfied
- BLOCKED — evidence/test asset unavailable

## MF-001 Split Sticker Sheet to PNG Frames
| ID | Scenario | Expected |
|---|---|---|
| AT-SPLIT-001 | exact 5x2 sheet | 10 frames in correct order |
| AT-SPLIT-002 | resized/non-divisible geometry | correct boundaries or REVIEW; no guessed destructive split |
| AT-SPLIT-003 | configurable margins/gaps | correct frame boxes |
| AT-SPLIT-004 | invalid geometry | structured failure/review reason |
| AT-SPLIT-005 | output naming | deterministic PNG filenames |

## MF-002 Remove Frame Border
| ID | Scenario | Expected |
|---|---|---|
| AT-BORDER-001 | green 3 px border | removed |
| AT-BORDER-002 | alternate color | removed if evidence high |
| AT-BORDER-003 | unequal side width | correct side-specific removal |
| AT-BORDER-004 | anti-aliased/resized border | supported or REVIEW |
| AT-BORDER-005 | artwork interrupts border | no destructive auto removal |
| AT-BORDER-006 | same-color artwork near border | artwork preserved / REVIEW |

## MF-003 Remove Frame Number / Metadata
| ID | Scenario | Expected |
|---|---|---|
| AT-META-001 | number badge in configured corner | removed |
| AT-META-002 | artwork contains numbers elsewhere | preserved |
| AT-META-003 | multiple ambiguous components in metadata zone | REVIEW/refusal |
| AT-META-004 | different badge size/style within supported constraints | removed or REVIEW |

## MF-004 Conditional Background Removal
| ID | Scenario | Expected |
|---|---|---|
| AT-ROUTE-001 | RGB no alpha | route background removal |
| AT-ROUTE-002 | RGBA all alpha=255 | route background removal |
| AT-ROUTE-003 | meaningful source transparency | skip background removal |
| AT-ROUTE-004 | opaque source + metadata cleanup creates alpha | still route background removal |
| AT-ROUTE-005 | transparent source + metadata cleanup | preserve source-alpha route; no segmentation |
| AT-ROUTE-006 | manifest provenance | records source transparency separately from cleanup/final alpha |
| AT-BG-001 | opaque black connected background | transparent output |
| AT-BG-002 | black hair/text inside foreground | preserved |
| AT-BG-003 | light/white background | supported deterministic removal |
| AT-BG-004 | near-uniform slight gradient | remove or REVIEW based on confidence |
| AT-BG-005 | foreground/background similarity | REVIEW; no silent deletion |
| AT-BG-006 | white anti-aliased sticker outline | preserved without unacceptable halo |

## Quality Preservation
| ID | Scenario | Expected |
|---|---|---|
| AT-QUAL-001 | downscale required | aspect ratio preserved |
| AT-QUAL-002 | source smaller than target | no upscale by default |
| AT-QUAL-003 | semi-transparent edge | alpha preserved |
| AT-QUAL-004 | repeated retry/resume | no repeated quality degradation |
| AT-QUAL-005 | source file hash before/after | unchanged |

## QA / State / Evidence
| ID | Scenario | Expected |
|---|---|---|
| AT-QA-001 | high-confidence clean case | PASS or AUTO_FIXED |
| AT-QA-002 | destructive ambiguity | REVIEW |
| AT-QA-003 | invalid/unprocessable file | FAIL with reason |
| AT-EVID-001 | exported PNG | traces to source sheet/frame |
| AT-EVID-002 | auto-fix | action + measurements recorded |
| AT-EVID-003 | provider use | provider/config version recorded where applicable |
| AT-EVID-004 | alpha provenance | source/cleanup/background-removal/final alpha provenance distinguishable |

## LINE / PNG Output
| ID | Scenario | Expected |
|---|---|---|
| AT-EXP-001 | valid final frame | PNG RGB/RGBA |
| AT-EXP-002 | transparent sticker | transparent pixels preserved |
| AT-EXP-003 | export dimensions | match active profile constraints |
| AT-EXP-004 | even dimensions required | validator detects violations |

## Recovery / Idempotency
| ID | Scenario | Expected |
|---|---|---|
| AT-REC-001 | process interruption after stage checkpoint | resume without restarting safe completed stages unnecessarily |
| AT-REC-002 | repeated same job/config | equivalent deterministic result |
| AT-REC-003 | output write failure | source unaffected; structured failure |
| AT-REC-004 | retry after failure | no duplicate destructive transform chain |

## Windows / Distribution
| ID | Scenario | Expected |
|---|---|---|
| AT-WIN-001 | clean Windows 11 x64 | app starts without separately installed Python |
| AT-WIN-002 | portable build | runs from extracted directory |
| AT-WIN-003 | installer | install/uninstall smoke pass |
| AT-WIN-004 | non-ASCII Thai path | supported or documented limitation before release |

## Milestone Gate Mapping
### M2
Must pass AT-SPLIT, AT-BORDER, AT-META, AT-ROUTE, core AT-QUAL and AT-EVID for transparent corpus. AT-ROUTE-004 through AT-ROUTE-006 are mandatory provenance regressions.

### M3
Must pass AT-BG and mixed transparent/opaque E2E with no Critical content-loss defect.

### M4
Must add UX acceptance around review/preview/export.

### M5
Must add batch 40-sticker and recovery/performance acceptance.

### M6/M7
Must pass Windows clean-machine, regression/golden corpus, audit and release evidence.

## Release Rule
A Critical requirement may not be declared complete without identifiable acceptance evidence linked to this matrix or a superseding SSOT revision.

References: `DECISIONS.md` ADR-023, `27_END_TO_END_WORKFLOW_SPEC.md`, `35_INTERFACE_AND_STAGE_CONTRACTS.md`.
