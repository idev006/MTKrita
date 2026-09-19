# MTKrita Interface and Stage Contracts

## Status
SSOT — Stage Contract Baseline v1.0

## Purpose
กำหนด contract ของ critical pipeline stages เพื่อให้ orchestration, providers, tests และ QA อ้างอิง behavior เดียวกัน และรองรับ engine/provider replacement โดยไม่เปลี่ยน domain workflow

## Common Stage Result
ทุก critical stage ควรสามารถรายงานอย่างน้อย:
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
**Input:** source image + sheet profile/config  
**Output:** layout geometry + confidence/evidence  
**Failure/Review:** ambiguous geometry → REVIEW / alternate detector  
**Prohibited:** destructive guess

## S-03 Frame Extraction
**Input:** source image + approved geometry  
**Output:** ordered extracted frames + source boxes  
**Invariant:** extraction uses source pixels; no resampling unless explicitly required  
**Failure:** frame count/geometry mismatch

## S-04 Border Detection/Removal
**Input:** extracted frame  
**Output:** border detection + cleaned/unchanged frame  
**Evidence:** side, thickness, color/range, continuity, confidence  
**Review:** border/artwork ambiguity  
**Prohibited:** global color deletion

## S-05 Frame Metadata Detection/Removal
**Input:** border-cleaned frame + metadata-zone config  
**Output:** metadata detection + cleaned/unchanged frame  
**Review:** multiple or ambiguous candidates  
**Prohibited:** deleting arbitrary text/numbers outside approved metadata evidence

## S-06 Transparency Routing
**Input:** metadata-cleaned frame  
**Output:** route = PRESERVE_ALPHA or REMOVE_BACKGROUND + alpha evidence  
**Rule:** meaningful transparency → preserve/skip segmentation  
**Rule:** fully opaque RGBA is treated as opaque for routing

## S-07 Background Classification
**Input:** opaque frame  
**Output:** class = uniform / near-uniform / complex + evidence  
**Purpose:** choose safest suitable provider

## S-08 Background Removal
**Input:** opaque frame + provider context  
**Output:** RGBA frame + mask + confidence/evidence  
**Review:** insufficient foreground/background confidence  
**Prohibited:** silent foreground deletion

## S-09 Content Analysis
**Input:** RGBA working frame  
**Output:** bbox, occupancy, edge contact, components/noise evidence  
**Review:** suspicious clipping/edge collision

## S-10 Smart Fit
**Input:** RGBA frame + target profile  
**Output:** fitted RGBA + scale/offset  
**Rules:** preserve aspect ratio; no default upscale; minimize resampling  
**Review:** significant requested upscale or unsafe fit

## S-11 QA Validation
**Input:** working/final candidate + processing evidence  
**Output:** PASS / AUTO_FIXED / REVIEW / FAIL + findings  
**Rule:** QA evaluates; it does not silently alter image content

## S-12 Export
**Input:** QA-eligible frame + export profile  
**Output:** PNG artifact + hash/metadata  
**Rules:** deterministic naming; preserve alpha; validate profile; no unrelated overwrite

## S-13 Manifest/Evidence
**Input:** job/frame/stage outcomes  
**Output:** machine-readable manifest + summary  
**Invariant:** sufficient traceability to source/config/version

## Provider Contract Principles
A provider must:
1. expose deterministic configuration where practical
2. return structured evidence, not only an image
3. not overwrite source
4. not redefine PASS/REVIEW policy
5. declare whether operation is deterministic
6. declare failure/retry behavior

## Interface Stability
Breaking changes to stage contracts require:
- SSOT update
- ADR if architectural
- traceability review
- regression update
- migration note where persisted manifests/artifacts are affected

References: `29_UML_SYSTEM_MODEL.md`, `27_END_TO_END_WORKFLOW_SPEC.md`, `25_DOCUMENT_DRIVEN_SSOT_OPERATING_MODEL.md`.
