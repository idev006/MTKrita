# Requirements Traceability Matrix

## Purpose
Maintain an auditable chain from product requirement to design component, verification method, and release evidence.

| Requirement | Design / Module | Primary Verification | Release Gate |
|---|---|---|---|
| PR-001 Input integrity | FileInspector | invalid/signature/mode tests | G2 |
| PR-002 AUTO/TRANSPARENT/OPAQUE | JobController + analyzers | mode-selection component tests | G2 |
| PR-003 5×2 configurable sheet | SheetAnalyzer/GridDetector | grid golden corpus | G2 |
| PR-004 hybrid extraction / PNG frame split | GridDetector/FrameExtractor | exact + scaled/margin/border cases; PNG order checks | G3 |
| PR-005 alpha analysis | AlphaAnalyzer / TransparencyRouter | RGBA transparent/opaque/AA tests | G2 |
| PR-006 opaque processing | BackgroundAnalyzer/MaskEngine | opaque golden corpus | G3 |
| PR-007 content bounds | ContentAnalyzer | bbox/edge/occupancy tests | G2 |
| PR-008 safe auto-fix | AutoFixEngine | destructive-safety tests | G3 |
| PR-009 QA status/reasons | QAEngine | state/reason tests | G2 |
| PR-010 PNG export | ExportEngine | PNG/LINE profile tests | G3 |
| PR-011 reporting | ManifestWriter | schema/report tests | G2 |
| PR-012 adaptive border detection/removal | BorderDetector/BorderRemovalEngine | multi-color/multi-width/ambiguous-contact suite | G3 |
| PR-013 quality-preserving processing | SmartFit/ExportEngine | no-upscale/resampling/alpha-edge suite | G3 |
| PR-014 original preservation | FileInspector/JobController | source-hash immutability tests | G2 |
| PR-015 Windows distribution | Distribution | clean Windows install E2E | G4 |
| PR-016 exception-first UX | Desktop Review UI | usability + REVIEW-flow acceptance | G3 |
| PR-017 frame-number removal | MetadataDetector/MetadataRemoval | corner badge, artwork-number preservation, ambiguity tests | G3 |
| PR-018 conditional background routing | TransparencyRouter | RGB, opaque RGBA, meaningful-alpha routing tests | G2 |
| PR-019 mandatory MVP contract | Pipeline Orchestrator | end-to-end MF-001→MF-005 mixed corpus | G3 |

## Mandatory MVP Traceability

| Baseline Capability | Requirement Mapping | Evidence Required |
|---|---|---|
| MF-001 Split Sticker Sheet → PNG frames | PR-003, PR-004, PR-010 | deterministic 10-frame extraction + PNG outputs |
| MF-002 Remove frame border | PR-012 | border corpus with no silent artwork loss |
| MF-003 Remove frame number | PR-017 | metadata removal + false-positive prevention tests |
| MF-004 Conditional background removal | PR-005, PR-006, PR-018 | transparent-skip + opaque-to-transparent evidence |
| MF-005 PNG output contract | PR-010, PR-011, PR-014 | valid PNG + manifest traceability + immutable source |

## Traceability Rule
No Critical requirement may be released without at least one objective verification method and identifiable evidence.

## Change Rule
When a requirement changes, review all mapped design modules, tests and release criteria. When a critical defect is discovered, update this matrix if coverage was incomplete.
