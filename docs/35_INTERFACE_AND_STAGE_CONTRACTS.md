# MTKrita Interface and Stage Contracts

## Status
SSOT — Stage Contract Baseline v1.8

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
**Evidence:** side, inset offset from frame edge, thickness, color/range, continuity, confidence, inner-edge contact risk, contact fraction and localized contact ranges  
**Review:** border/artwork or border/metadata ambiguity; same/near-border-color content touching the inner border boundary  
**Prohibited:** global color deletion; automatic crop when border/artwork or border/metadata contact risk is detected  
**Rule:** a border may begin at offset 0 or after bounded transparent/empty near-edge padding  
**Rule:** inset-border fallback requires multi-side consensus (or equivalently strong topology evidence); a single candidate strip cannot authorize destructive crop  
**Rule:** high strip/color confidence alone is insufficient when topology/contact evidence indicates possible artwork loss  
**Rule:** detecting an inset border with contact risk is useful evidence but must remain `REVIEW` unless S-06A produces an approved joint cleanup plan

## S-05 Source Transparency Classification
**Domain service:** MTKrita-owned routing/provenance service  
**Input:** extracted/border-cleaned frame before any cleanup that can create alpha  
**Output:** `SourceTransparencyDecision` = PRESERVE_ALPHA or REMOVE_BACKGROUND + alpha evidence  
**Rule:** meaningful source transparency → preserve/skip segmentation  
**Rule:** fully opaque RGBA is treated as opaque  
**Invariant:** this decision is immutable provenance for the frame unless an explicit owner-approved override mode is used

## S-06 Frame Metadata Detection / Cleanup Planning
**Provider boundary:** `MetadataProcessingProvider`  
**Input:** frame + metadata-zone config + optional analysis-only exclusion mask supplied by an approved upstream detector  
**Output:** metadata detection + cleanup mask/plan + confidence/evidence  
**Required evidence:** candidate count, selected bbox, anchor distance/proximity, fill/compactness, area ratio, dominance margin to the next plausible candidate, confidence and reason  
**Required exclusion evidence when used:** exclusion-applied flag, excluded-pixel count/ratio, excluded-candidate-pixel count, whether fragmentation occurred, whether fragment association was applied/resolved, associated fragment count, whether the resulting metadata mask requires joint cleanup, and the coordinate-space identity shared with the frame  
**Automatic-selection rule:** the selected component must satisfy all configured area/shape constraints, lie within the approved corner-anchor envelope, and exceed the next plausible candidate by the configured dominance margin  
**Analysis-exclusion rule:** an approved spatial border mask may be excluded from connected-component analysis to prevent the decorative border from merging with a badge; exclusion affects analysis only and is not itself proof that any excluded pixel is metadata  
**Fragmentation rule:** if exclusion may have split one metadata object into multiple fragments, the selected fragment must not be treated as a complete destructive metadata mask unless the association rule below proves completeness; otherwise `REVIEW`  
**Safe fragment-association rule:** exclusion-fragmented metadata may be reconstructed for *joint cleanup only* when all of the following hold:
- the primary anchored fragment and every associated fragment belong to the same connected component in the pre-exclusion candidate topology;
- all non-excluded fragments from that raw topology group remain inside the configured corner-anchor envelope; any fragment from the group outside the envelope causes `REVIEW`;
- every associated secondary fragment is spatially adjacent to the approved exclusion boundary rather than arbitrarily nearby;
- the reconstructed union still satisfies configured metadata area/compactness/anchor constraints;
- there is exactly one dominant reconstructed anchored candidate; competing reconstructed groups cause `REVIEW`;
- excluded pixels themselves are not copied into the metadata mask; overlap pixels remain the responsibility of the separately approved border mask;
- the resulting detection is marked `requires_joint_cleanup=true` and must never be passed to standalone metadata removal.
**Review:** multiple plausible anchored candidates, insufficient dominance margin, implausible shape/area, metadata connected to unexplained artwork, unresolved exclusion fragmentation, or a raw topology group extending outside the anchor envelope  
**Prohibited:** deleting arbitrary text/numbers merely because they occur inside the broad metadata zone  
**Prohibited:** lowering global ambiguity thresholds to force a production case through automatic cleanup  
**Prohibited:** filling/deleting the whole anchor box, convex hull, bounding box, or performing broad morphology merely to reconnect an exclusion-fragmented badge  
**Rule:** the broad metadata zone is a search boundary; the smaller corner-anchor envelope is the automatic-selection boundary  
**Rule:** a clearly non-anchored component must not compete with an anchored badge for auto-selection, but it remains recorded as evidence  
**Rule:** detection may run without mutation for diagnostics/planning; destructive cleanup occurs only after the stage policy authorizes it  
**Important:** metadata detection/removal must not redefine source transparency provenance

## S-06A Joint Border + Metadata Cleanup Planning
**Domain service:** `JointCleanupPlanner`  
**Input:** immutable source-transparency provenance + border geometry/contact evidence + complete metadata detection/mask evidence + frame geometry  
**Output:** immutable `JointCleanupPlan` with status `SAFE_PLAN` or `REVIEW`  
**Required evidence:** explained/unexplained contact ranges or fractions, combined planned deletion mask, planned removed-pixel count/ratio, reasons and confidence  
**SAFE_PLAN rule:** all risky border contact must be explainable by approved metadata/corner geometry; any unexplained contact causes `REVIEW`  
**SAFE_PLAN rule:** border and metadata evidence must each meet their automatic policy thresholds independently; the planner does not raise weak detector confidence  
**SAFE_PLAN rule:** metadata mask completeness must be established; unresolved exclusion fragmentation cannot authorize joint mutation; safely associated metadata marked `requires_joint_cleanup=true` is valid only when paired with the exact approved border evidence/mask in the same coordinate space  
**Deletion scope rule:** the combined mask is bounded to approved spatial border bands plus approved metadata mask; no global color key is permitted  
**Coordinate rule:** all evidence/masks are validated in one pre-cleanup frame coordinate space  
**Mutation rule:** planner construction is non-destructive; applying a plan is a separate operation and may occur only for `SAFE_PLAN`  
**Determinism rule:** deterministic inputs/configuration must produce the same plan mask/evidence hash  
**Prohibited:** using joint planning to bypass source-transparency provenance, unexplained artwork contact, metadata ambiguity, unresolved fragmentation or configured safety bounds  
**Reference:** `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md` / ADR-028

## S-07 Transparent-Route Cleanup
**Input:** source-transparent frame + approved metadata or joint cleanup plan  
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
**Required provenance:** extraction method/confidence, border side/offset/thickness/contact evidence, source transparency decision, metadata cleanup/exclusion/association evidence, joint-cleanup plan evidence when used, significant actions/findings, final output reference/hash

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

References: `29_UML_SYSTEM_MODEL.md`, `27_END_TO_END_WORKFLOW_SPEC.md`, `25_DOCUMENT_DRIVEN_SSOT_OPERATING_MODEL.md`, `44_PROVIDER_INTERFACE_ARCHITECTURE.md`, `64_JOINT_BORDER_METADATA_CLEANUP_SPEC.md`, ADR-015, ADR-016, ADR-023 and ADR-028.
