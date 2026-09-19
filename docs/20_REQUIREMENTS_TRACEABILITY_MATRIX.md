# Requirements Traceability Matrix

## Purpose
Maintain an auditable chain from product requirement to behavior/design component, verification method, and release evidence.

| Requirement | Behavior / Design / Module | Primary Verification | Release Gate |
|---|---|---|---|
| PR-001 Input integrity | FileInspector; UC-001; Security Model | invalid/signature/mode tests | G2 |
| PR-002 AUTO/TRANSPARENT/OPAQUE | JobController + TransparencyRouter; UC-005/006 | mode-selection component tests | G2 |
| PR-003 5×2 configurable sheet | SheetAnalyzer/GridDetector; Workflow S-02/S-03 | grid golden corpus | G2 |
| PR-004 hybrid extraction / PNG frame split | GridDetector/FrameExtractor; UC-001/009 | exact + scaled/margin/border cases; PNG order checks | G3 |
| PR-005 alpha analysis | AlphaAnalyzer / TransparencyRouter; Sequence transparent/opaque | RGBA transparent/opaque/AA tests | G2 |
| PR-006 opaque processing | BackgroundAnalyzer/MaskEngine; UC-006 | opaque golden corpus | G3 |
| PR-007 content bounds | ContentAnalyzer; Stage S-09 | bbox/edge/occupancy tests | G2 |
| PR-008 safe auto-fix | AutoFixEngine; State/Review rules | destructive-safety tests | G3 |
| PR-009 QA status/reasons | QAEngine; State Machine | state/reason/transition tests | G2 |
| PR-010 PNG export | ExportEngine; Stage S-12 | PNG/LINE profile tests | G3 |
| PR-011 reporting | ManifestWriter; Artifact Lifecycle | schema/report/traceability tests | G2 |
| PR-012 adaptive border detection/removal | BorderDetector; UC-007; Stage S-04 | multi-color/multi-width/ambiguous-contact suite | G3 |
| PR-013 quality-preserving processing | SmartFit; Artifact Lifecycle | no-upscale/resampling/alpha-edge suite | G3 |
| PR-014 original preservation | FileInspector/JobController; Security Model | source-hash immutability tests | G2 |
| PR-015 Windows distribution | Deployment Architecture | clean Windows install E2E | G4 |
| PR-016 exception-first UX | Review Sequence; UI Spec | usability + REVIEW-flow acceptance | G3 |
| PR-017 frame-number removal | MetadataDetector; UC-008; Stage S-05 | corner badge, artwork-number preservation, ambiguity tests | G3 |
| PR-018 conditional background routing | TransparencyRouter; UC-005/006; Stage S-06 | RGB, opaque RGBA, meaningful-alpha routing tests | G2 |
| PR-019 mandatory MVP contract | End-to-End Workflow + FramePipeline | end-to-end MF-001→MF-005 mixed corpus | G3 |

## Mandatory MVP Traceability

| Baseline Capability | Requirement Mapping | Behavioral SSOT | Evidence Required |
|---|---|---|---|
| MF-001 Split Sticker Sheet → PNG frames | PR-003, PR-004, PR-010 | `27`, `28 UC-001`, `35 S-02/S-03` | deterministic 10-frame extraction + PNG outputs |
| MF-002 Remove frame border | PR-012 | `28 UC-007`, `35 S-04` | border corpus with no silent artwork loss |
| MF-003 Remove frame number | PR-017 | `28 UC-008`, `35 S-05` | metadata removal + false-positive prevention tests |
| MF-004 Conditional background removal | PR-005, PR-006, PR-018 | `30` transparent/opaque sequences; `35 S-06/S-08` | transparent-skip + opaque-to-transparent evidence |
| MF-005 PNG output contract | PR-010, PR-011, PR-014 | `34`, `35 S-12/S-13`, `36` | valid PNG + manifest traceability + immutable source |

## Behavioral Model Traceability

| Concern | Authoritative Document | Required Verification |
|---|---|---|
| end-to-end workflow | `27_END_TO_END_WORKFLOW_SPEC.md` | E2E happy/alternate/review/failure flows |
| actor/system behavior | `28_USE_CASE_SPECIFICATION.md` | use-case acceptance tests |
| architecture/components | `29_UML_SYSTEM_MODEL.md` | architecture review + dependency checks |
| interaction order | `30_SEQUENCE_DIAGRAMS.md` | integration/order tests |
| job/frame lifecycle | `31_STATE_MACHINE_SPEC.md` | state transition tests |
| Windows runtime/deployment | `32_DEPLOYMENT_AND_RUNTIME_ARCHITECTURE.md` | clean-machine smoke/install tests |
| retry/resume/idempotency | `33_ERROR_RECOVERY_AND_IDEMPOTENCY_SPEC.md` | crash/retry/resume tests |
| artifact lifecycle | `34_DATA_FLOW_AND_ARTIFACT_LIFECYCLE.md` | hash/path/retention/traceability tests |
| pipeline contracts | `35_INTERFACE_AND_STAGE_CONTRACTS.md` | interface/component contract tests |
| file/security safety | `36_SECURITY_AND_FILE_SAFETY_MODEL.md` | corrupt/path traversal/collision/source-change tests |

## Traceability Rule
No Critical requirement may be released without at least one objective verification method and identifiable evidence.

## Change Rule
When a requirement changes, review all mapped behavioral documents, design modules, tests and release criteria. When a critical defect is discovered, update this matrix if coverage was incomplete.
