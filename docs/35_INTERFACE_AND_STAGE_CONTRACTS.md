# MTKrita Interface and Stage Contracts

## Status
SSOT — Stage Contract Baseline v2.0

## Purpose
กำหนด contract ของ critical pipeline stages เพื่อให้ orchestration, providers, tests และ QA อ้างอิง behavior เดียวกัน และรองรับ engine/provider replacement โดยไม่เปลี่ยน domain workflow

## Interface-First Rule
The Python orchestrator shall depend on abstract provider contracts, not concrete OpenCV/Pillow/ImageMagick/ML classes. Concrete implementations are selected through validated configuration and a provider registry/factory.

Recommended mechanisms:
- `typing.Protocol` where practical
- `abc.ABC` where enforced inheritance/lifecycle hooks help
- immutable dataclasses for requests/results where practical

Provider-specific objects must not leak across the domain boundary unless wrapped in MTKrita-owned models.

## Common Provider Contract
Every replaceable provider should expose:
- stable provider id/version/capabilities
- declared deterministic/non-deterministic behavior
- explicit input/result models
- findings/measurements/confidence where applicable
- recoverable vs non-recoverable failure indication

## Common Stage Result
Critical stages report at least stage name, status, findings, actions, measurements, provider/strategy, confidence where applicable, input/output artifact refs and attempt/version identity.

## S-01 File Inspection
**Input:** source path  
**Output:** FileInspection + source hash  
**Failure:** unreadable/corrupt/invalid source → FAIL  
**Invariant:** source bytes unchanged

## S-02 Layout Detection
**Provider boundary:** `LayoutDetectionProvider`  
**Input:** source image + sheet profile/config  
**Output:** layout geometry + confidence/evidence  
**Failure/Review:** ambiguous geometry → REVIEW / alternate detector  
**Prohibited:** destructive guess

## S-03 Frame Extraction
**Provider boundary:** `FrameExtractionProvider` where replacement is useful; otherwise MTKrita core service  
**Input:** source image + approved geometry  
**Output:** ordered extracted frames + source boxes + extraction method/confidence  
**Invariant:** extraction uses source pixels; no resampling unless explicitly required  
**Failure:** frame count/geometry mismatch

## S-04 Border Detection/Removal
**Provider boundary:** `BorderProcessingProvider`  
**Input:** extracted frame  
**Output:** border detection + cleaned/unchanged frame  
**Required evidence:** side, inset offset, thickness, color/range, band continuity, visible support, visible-pixel color purity, confidence, inner-edge contact risk, contact fraction and localized contact ranges  
**Review:** border/artwork or border/metadata ambiguity; same/near-border-color content touching inner border; insufficient visible support; insufficient color purity; inconsistent multi-side geometry/color  
**Prohibited:** global color deletion; automatic crop when contact risk exists unless S-06A approves a joint plan  
**Rule:** border may begin at offset 0 or after bounded transparent/empty near-edge padding  
**Rule:** inset-border fallback requires multi-side consensus or equivalently strong topology evidence  
**Rounded-corner rule:** transparent samples expected outside a rounded border are absence-of-support, not wrong-color evidence; visible support and visible color purity must be measured separately  
**Policy rule:** evidence modeling may improve without lowering the automatic safety threshold merely to increase pass rate  
**Rule:** high color purity alone is insufficient when support/topology/contact evidence indicates possible artwork loss

## S-05 Source Transparency Classification
**Domain service:** MTKrita-owned routing/provenance service  
**Input:** extracted/border-cleaned frame before any cleanup that can create alpha  
**Output:** `SourceTransparencyDecision` = PRESERVE_ALPHA or REMOVE_BACKGROUND + alpha evidence  
**Rule:** meaningful source transparency → preserve/skip segmentation  
**Rule:** fully opaque RGBA → opaque route  
**Invariant:** decision is immutable provenance unless explicit owner-approved override is used

## S-06 Frame Metadata Detection / Cleanup Planning
**Provider boundary:** `MetadataProcessingProvider`  
**Input:** frame + metadata-zone config + optional approved analysis-only exclusion mask  
**Output:** metadata detection + cleanup mask/plan + confidence/evidence  
**Required evidence:** candidate count, selected bbox, anchor distance/proximity, fill/compactness, area ratio, dominance margin, confidence/reason, exclusion evidence, post-exclusion isolation evidence and coordinate identity  
**Automatic-selection rule:** selected destructive candidate must satisfy configured area/shape constraints, be fully bounded by the approved corner-anchor envelope, be isolated after exclusion, and exceed competing plausible anchored candidates by configured dominance margin  
**Analysis-exclusion rule:** approved spatial border mask may be excluded from connectivity analysis; exclusion affects analysis only and is not itself proof that any excluded pixel is metadata  

### Safe post-exclusion association
Exclusion-fragmented metadata may be reconstructed for joint cleanup only when:
- selected primary/local fragments are fully contained inside the approved anchor envelope;
- selected secondary fragments created by exclusion are adjacent to the approved exclusion boundary and spatially local to the primary candidate;
- the selected post-exclusion candidate/local group has no non-excluded connected path outside the anchor envelope;
- remote fragments from the same pre-exclusion raw topology may be ignored only when the approved exclusion mask disconnects them from the selected candidate;
- ignored/out-of-anchor fragments remain evidence only and never enter shape scoring or deletion mask;
- reconstructed local union passes configured area/fill/compactness/anchor constraints;
- exactly one dominant plausible anchored local candidate exists;
- excluded pixels are not copied into metadata mask; overlap remains border-owned;
- detection is marked `requires_joint_cleanup=true` and cannot be passed to standalone metadata removal.

**Review:** selected candidate extends outside anchor via non-excluded connectivity; competing anchored candidates; insufficient dominance; implausible local shape/area; unexplained artwork contact; unresolved local association; mismatched exclusion identity  
**Important refinement:** pre-exclusion raw-group membership is connectivity evidence, not destructive ownership. A remote fragment no longer invalidates an otherwise isolated local badge merely because both were connected only through the decorative border before approved exclusion.

### Exclusion-aware shape evidence
Approved exclusion-overlap pixels associated with the isolated local candidate may contribute to shape/fill confidence only inside the candidate bbox. They never enter metadata deletion mask, remain border-owned, and do not justify lowering the automatic threshold. Evidence records overlap-pixel count used only for scoring.

### Enclosed-interior completion
Visible interior pixels such as dark digits may be added only when they form holes topologically fully enclosed by approved local badge support. Open exterior-connected regions are never filled. Bounding-box fill, convex hull fill and broad morphology are prohibited.

**Rule:** broad metadata zone is search boundary; smaller anchor envelope is automatic destructive-selection boundary  
**Rule:** clearly non-anchored components do not compete for automatic selection but remain evidence  
**Rule:** detection may run without mutation for diagnostics/planning  
**Prohibited:** deleting arbitrary text/numbers merely because they occur in broad metadata zone  
**Prohibited:** lowering ambiguity/confidence thresholds to force production cases through  
**Important:** metadata cleanup must never redefine source transparency provenance

## S-06A Joint Border + Metadata Cleanup Planning
**Domain service:** `JointCleanupPlanner`  
**Input:** immutable source-transparency provenance + border geometry/contact evidence + complete isolated metadata mask/evidence + frame geometry  
**Output:** immutable `JointCleanupPlan` = SAFE_PLAN or REVIEW  
**Required evidence:** explained/unexplained contact ranges/fractions, combined planned deletion mask, planned removed-pixel count/ratio, reasons and confidence  
**SAFE_PLAN rule:** all risky border contact must be explainable by approved metadata/corner geometry  
**SAFE_PLAN rule:** border and metadata evidence independently meet configured automatic policy; planner does not raise weak confidence  
**SAFE_PLAN rule:** metadata completeness and post-exclusion isolation are established and exact approved border/exclusion identity matches  
**Deletion scope:** approved spatial border bands + approved metadata mask only; no global color key  
**Coordinate rule:** all evidence/masks share one pre-cleanup frame coordinate space  
**Mutation rule:** planning is non-destructive; apply only SAFE_PLAN  
**Determinism rule:** deterministic inputs/config produce same plan mask/evidence hash  
**Prohibited:** bypassing provenance, unexplained artwork contact, ambiguity, isolation failure or safety bounds  
**Reference:** `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md` / ADR-028

## S-07 Transparent-Route Cleanup
**Input:** source-transparent frame + approved metadata or joint cleanup plan  
**Output:** cleaned RGBA preserving source alpha semantics  
**Rule:** no background segmentation by default

## S-08 Background Classification
**Provider boundary:** `BackgroundClassificationProvider`  
**Input:** source-opaque frame  
**Output:** uniform / near-uniform / complex + evidence  
**Purpose:** choose safest provider

## S-09 Background Removal
**Provider boundary:** `BackgroundRemovalProvider`  
**Input:** source-opaque frame + provider context + optional approved metadata cleanup mask  
**Output:** RGBA frame + mask + confidence/evidence  
**Review:** insufficient foreground/background confidence  
**Prohibited:** silent foreground deletion  
**Rule:** alpha introduced by metadata cleanup must not cause this stage to be skipped

## S-10 Content Analysis
**Provider boundary:** `ContentAnalysisProvider`  
**Input:** RGBA working frame  
**Output:** bbox, occupancy, edge contact, components/noise evidence  
**Review:** suspicious clipping/edge collision

## S-11 Smart Fit
**Provider boundary:** `ImageTransformProvider`  
**Input:** RGBA frame + target profile  
**Output:** fitted RGBA + scale/offset  
**Rules:** preserve aspect ratio; no default upscale; minimize resampling  
**Review:** significant requested upscale or unsafe fit

## S-12 QA Validation
**Domain service:** `QAEngine` owns project policy. Providers may supply measurements but not redefine PASS/REVIEW/FAIL.  
**Input:** working/final candidate + evidence  
**Output:** PASS / AUTO_FIXED / REVIEW / FAIL + findings  
**Rule:** QA evaluates; it does not silently alter image content

## S-13 Export
**Provider boundary:** `ExportProvider`  
**Input:** QA-eligible frame + export profile + pre-resolved target ref  
**Output:** PNG artifact + SHA-256 + byte size  
**Rules:** deterministic naming; preserve alpha; validate profile; no unrelated overwrite; atomic commit where supported

## S-14 Manifest/Evidence
**Domain service:** MTKrita-owned serializer/evidence model  
**Input:** job/frame/stage outcomes  
**Output:** machine-readable manifest + summary  
**Invariant:** sufficient traceability to source/config/version  
**Required provenance:** extraction method/confidence, border support/purity/geometry/contact evidence, source-transparency decision, metadata exclusion/isolation/association/interior evidence, joint-plan evidence, significant actions/findings, final output reference/hash

## Provider Registry / Factory
Provider selection is resolved during job initialization from validated TOML through one composition/registry layer. Core pipeline must not scatter provider-name branching.

## Provider Contract Principles
A provider must expose deterministic configuration where practical, return structured evidence, not overwrite source, not redefine PASS/REVIEW policy, declare deterministic/retry behavior, and remain replaceable without leaking engine-specific state into domain models.

## Interface Stability
Breaking stage/provider changes require SSOT update, ADR when architectural, traceability review, regression update and migration note when persisted evidence/artifacts are affected.

## Tier-B Evidence Link
Representative transparent-corpus findings that motivated v2.0 are recorded in `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`. The contract change improves evidence semantics and isolation proof; it does not lower destructive safety thresholds.

References: `29_UML_SYSTEM_MODEL.md`, `27_END_TO_END_WORKFLOW_SPEC.md`, `25_DOCUMENT_DRIVEN_SSOT_OPERATING_MODEL.md`, `44_PROVIDER_INTERFACE_ARCHITECTURE.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, `65_TIER_B_TRANSPARENT_CORPUS_EVIDENCE.md`, ADR-015, ADR-016, ADR-023 and ADR-028.
