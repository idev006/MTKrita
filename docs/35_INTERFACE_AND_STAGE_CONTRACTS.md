# MTKrita Interface and Stage Contracts

## Status
SSOT — Stage Contract Baseline v1.4

## Purpose
กำหนด contract ของ critical pipeline stages เพื่อให้ orchestration, providers, tests และ QA อ้างอิง behavior เดียวกัน และรองรับ engine/provider replacement โดยไม่เปลี่ยน domain workflow

## Interface-First Rule
The Python orchestrator shall depend on **abstract provider contracts**, not concrete OpenCV/Pillow/ImageMagick/ML classes.

Concrete implementations are selected through validated configuration and a provider registry/factory.

Recommended Python mechanisms:
- `typing.Protocol` for structural interfaces where practical
- `abc.ABC` when enforced inheritance/lifecycle hooks are useful
- immutable dataclasses for requests/results where practical

Provider-specific objects must not leak across the domain boundary unless wrapped in MTKrita-owned models.

## Common Provider Contract
Every replaceable provider should expose:
- stable provider id
- provider version/capability metadata
- declared deterministic/non-deterministic behavior
- explicit request/input model
- structured result/output model
- findings/measurements/confidence where applicable
- recoverable vs non-recoverable failure indication

## Common Stage Result
ทุก critical stage ควรรายงานอย่างน้อย:
- stage name
- status: SUCCEEDED / SKIPPED / REVIEW / FAILED
- findings
- actions
- measurements
- provider/strategy
- confidence เมื่อเกี่ยวข้อง
- input artifact reference
- output artifact reference
- attempt id/version

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
**Evidence:** side, inset offset from frame edge, thickness, color/range, continuity, confidence, inner-edge contact risk  
**Review:** border/artwork or border/metadata ambiguity; same/near-border-color content touching the inner border boundary  
**Prohibited:** global color deletion; automatic crop when border/artwork or border/metadata contact risk is detected  
**Rule:** a border may begin at offset 0 or after bounded transparent/empty near-edge padding  
**Rule:** inset-border fallback requires multi-side consensus (or equivalently strong topology evidence); a single candidate strip cannot authorize destructive crop  
**Rule:** high strip/color confidence alone is insufficient when topology/contact evidence indicates possible artwork loss  
**Rule:** detecting an inset border with contact risk is useful evidence but must remain `REVIEW` until a separately approved joint-cleanup contract exists

## S-05 Source Transparency Classification
**Domain service:** MTKrita-owned routing/provenance service  
**Input:** extracted/border-cleaned frame before any cleanup that can create alpha  
**Output:** `SourceTransparencyDecision` = PRESERVE_ALPHA or REMOVE_BACKGROUND + alpha evidence  
**Rule:** meaningful source transparency → preserve/skip segmentation  
**Rule:** fully opaque RGBA is treated as opaque  
**Invariant:** this decision is immutable provenance for the frame unless an explicit owner-approved override mode is used

## S-06 Frame Metadata Detection / Cleanup Planning
**Provider boundary:** `MetadataProcessingProvider`  
**Input:** frame + metadata-zone config  
**Output:** metadata detection + cleanup mask/plan + confidence/evidence  
**Review:** multiple or ambiguous candidates  
**Prohibited:** deleting arbitrary text/numbers outside approved metadata evidence  
**Important:** metadata detection/removal must not redefine source transparency provenance

## S-07 Transparent-Route Cleanup
**Input:** source-transparent frame + approved metadata cleanup plan  
**Output:** cleaned RGBA preserving source alpha semantics  
**Rule:** no background segmentation by default

## S-08 Background Classification
**Provider boundary:** `BackgroundClassificationProvider`  
**Input:** source-opaque frame  
**Output:** class = uniform / near-uniform / complex + evidence  
**Purpose:** choose safest suitable provider

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
**Domain service:** `QAEngine` owns project policy. Provider-specific measurements may be consumed, but PASS/REVIEW/FAIL policy remains MTKrita-owned.  
**Input:** working/final candidate + processing evidence  
**Output:** PASS / AUTO_FIXED / REVIEW / FAIL + findings  
**Rule:** QA evaluates; it does not silently alter image content

## S-13 Export
**Provider boundary:** `ExportProvider`  
**Input:** QA-eligible frame + export profile + pre-resolved target reference  
**Output:** PNG artifact + SHA-256 + byte size  
**Rules:** deterministic naming; preserve alpha; validate profile; no unrelated overwrite; atomic commit where supported

## S-14 Manifest/Evidence
**Domain service:** MTKrita-owned serializer/evidence model  
**Input:** job/frame/stage outcomes  
**Output:** machine-readable manifest + summary  
**Invariant:** sufficient traceability to source/config/version  
**Required provenance:** extraction method/confidence, border side/offset/thickness/contact evidence, source transparency decision, metadata cleanup evidence, significant actions/findings, final output reference/hash

## Provider Registry / Factory
Provider selection shall be resolved during job initialization from validated TOML configuration.

```text
TOML config
   ↓
Config validation
   ↓
ProviderRegistry
   ↓
Resolve interface → concrete provider
   ↓
Inject providers into Pipeline/JobController
```

The core pipeline must not use scattered provider-name branching. Provider-specific selection belongs in one composition/registry layer.

## Provider Contract Principles
A provider must:
1. expose deterministic configuration where practical
2. return structured evidence, not only an image
3. not overwrite source
4. not redefine PASS/REVIEW policy
5. declare whether operation is deterministic
6. declare failure/retry behavior
7. avoid leaking engine-specific state into domain models
8. be replaceable by a contract-compatible implementation

## Interface Stability
Breaking changes to stage/provider contracts require:
- SSOT update
- ADR if architectural
- traceability review
- regression update
- migration note where persisted manifests/artifacts are affected

References: `29_UML_SYSTEM_MODEL.md`, `27_END_TO_END_WORKFLOW_SPEC.md`, `25_DOCUMENT_DRIVEN_SSOT_OPERATING_MODEL.md`, `44_PROVIDER_INTERFACE_ARCHITECTURE.md`, ADR-015, ADR-016 and ADR-023.
