# Requirements Traceability Matrix

## Purpose
Maintain an auditable chain from product requirement to design component, verification method, and release evidence.

| Requirement | Design / Module | Primary Verification | Release Gate |
|---|---|---|---|
| PR-001 Input integrity | FileInspector | invalid/signature/mode tests | G2 |
| PR-002 AUTO/TRANSPARENT/OPAQUE | JobController + analyzers | mode-selection component tests | G2 |
| PR-003 5×2 configurable sheet | SheetAnalyzer/GridDetector | grid golden corpus | G2 |
| PR-004 hybrid extraction | GridDetector/FrameExtractor | scaled/margin/border cases | G3 |
| PR-005 alpha analysis | AlphaAnalyzer | RGBA transparent/opaque/AA tests | G2 |
| PR-006 opaque processing | BackgroundAnalyzer/MaskEngine | opaque golden corpus | G3 |
| PR-007 content bounds | ContentAnalyzer | bbox/edge/occupancy tests | G2 |
| PR-008 safe auto-fix | AutoFixEngine | destructive-safety tests | G3 |
| PR-009 QA status/reasons | QAEngine | state/reason tests | G2 |
| PR-010 PNG export | ExportEngine | LINE profile tests | G3 |
| PR-011 reporting | ManifestWriter | schema/report tests | G2 |
| Adaptive border detection/removal | BorderDetector/BorderRemovalEngine | T-BORDER suite | G3 |
| Quality-preserving resampling | SmartFit/ExportEngine | T-QUALITY suite | G3 |
| Windows no-dev-dependency install | Distribution | clean Windows install E2E | G4 |

## Traceability Rule
No Critical requirement may be released without at least one objective verification method and identifiable evidence.

## Change Rule
When a requirement changes, review all mapped design modules, tests and release criteria. When a critical defect is discovered, update this matrix if coverage was incomplete.