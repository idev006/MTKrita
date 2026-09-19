# MTKrita Master Project Control

## Status
SSOT — Project Control Baseline v1.0

## Purpose
เอกสารนี้เป็นเอกสารควบคุมระดับบนสุดของโครงการ MTKrita เพื่อเชื่อมโยง Vision → Goals → Objectives → Mandatory Workflow → Workstreams → Milestones → Quality Gates → Release Criteria ให้เป็นสายเดียวกัน และป้องกัน scope drift ระหว่างการพัฒนา

---

## 1. Project Vision
สร้าง Windows 11 application ที่ทำหน้าที่เป็น **Sticker Production Automation Machine** สามารถรับ Sticker Sheet แล้วแยกและประมวลผลเป็น PNG รายเฟรมอย่างปลอดภัย ตรวจสอบได้ และลดงาน manual ที่ซ้ำซ้อน โดยรักษาคุณภาพ artwork และรองรับทั้ง input ที่ transparent และ non-transparent

---

## 2. Project Goals

### G-01 Automation
ลดการทำงานแบบ manual ในขั้น split, border removal, frame-number removal, background routing/removal และ PNG export

### G-02 Content Safety
ห้าม silent loss ของตัวละคร ข้อความ white outline props หรือรายละเอียด artwork

### G-03 Quality Preservation
ใช้ lossless-first processing, preserve alpha/anti-alias, avoid repeated resize และไม่ upscale โดย default

### G-04 Repeatability
ผลลัพธ์ deterministic stages ต้อง reproducible จาก source/config/version เดียวกัน

### G-05 Production Readiness
รองรับ batch production และ Windows 11 distribution โดยผู้ใช้ไม่ต้องติดตั้ง Python/developer toolchain

---

## 3. Mandatory Minimum Objectives
MVP ต้องพิสูจน์ได้ว่า:

1. Sticker Sheet 5×2 ถูก split เป็น 10 PNG ตามลำดับได้ถูกต้อง
2. Border หลายสี/หลายความหนาถูกลบได้เมื่อ confidence สูง
3. Frame number / sheet metadata ถูกลบได้โดยไม่ทำลายข้อความ/ตัวเลขใน artwork
4. Frame ที่มี meaningful transparency อยู่แล้วต้องข้าม background removal
5. Frame ที่ opaque ต้องสามารถ route เข้าสู่ background-removal pipeline และสร้าง transparent RGBA ได้ใน supported archetypes
6. Ambiguous destructive case ต้องกลายเป็น `REVIEW`
7. Source file ต้องไม่ถูก overwrite และ source hash ต้องคงเดิม
8. Output PNG ทุกไฟล์ต้อง trace กลับไปยัง source sheet/frame ได้

รายละเอียดทางเทคนิค: `24_MVP_MINIMUM_FUNCTIONAL_BASELINE.md`

---

## 4. Mandatory End-to-End Workflow

```text
Sticker Sheet Input
        ↓
File Inspection / Source Fingerprint
        ↓
Layout Detection
        ↓
Split Frames
        ↓
Adaptive Border Detection & Removal
        ↓
Frame Number / Sheet Metadata Detection & Removal
        ↓
Transparency Routing
        ├─ meaningful alpha exists → preserve alpha / skip BG removal
        └─ opaque / no meaningful alpha → background-removal pipeline
                                      ↓
                               transparent RGBA
        ↓
Content Bounds / Edge Safety
        ↓
Smart Fit / Quality Preservation
        ↓
QA
        ├─ PASS
        ├─ AUTO_FIXED
        ├─ REVIEW
        └─ FAIL
        ↓
PNG Export
        ↓
Manifest / Evidence / Package
```

---

## 5. Scope Boundaries

### Must-have before MVP release
- MF-001 Split PNG frames
- MF-002 Border removal
- MF-003 Frame-number removal
- MF-004 Conditional background removal
- MF-005 PNG output + traceability

### Deferred unless required by defect resolution
- OCR semantic correctness
- duplicate caption detection
- AI semantic review
- animated sticker support
- deep Krita editor integration
- automatic LINE submission

Optional features may not delay mandatory MVP correctness.

---

## 6. Workstreams

- **WS1 Product/Governance** — Project Director + PM
- **WS2 Core Architecture** — Senior Software Engineer
- **WS3 Image Processing** — Senior Process Engineer + Pipeline Engineer
- **WS4 Verification** — Senior Software Tester + QA Auditor
- **WS5 Desktop UX** — UI/UX Designer + Software Engineer
- **WS6 Distribution** — Pipeline Engineer + Tester
- **WS7 Documentation/Audit** — Document Writer + Software Auditor

Governance details: `00_TEAM_GOVERNANCE.md`

---

## 7. Milestones

### M0 Documentation Baseline
Governance, requirements, architecture, QA, testing, traceability approved.

### M1 Core Skeleton — COMPLETE
CLI, manifests, immutable inspection, test harness, Windows CI.

### M2 Transparent Processing Baseline — IN PROGRESS
Split + border + frame-number + transparency router + alpha/content + smart-fit + PNG validation.

### M3 Opaque Processing Baseline
Opaque background removal + REVIEW fallback + mixed transparent/opaque E2E.

### M4 Desktop Beta
Drag/drop UI, exception-first review, preview, export.

### M5 Production Automation
4 sheets / 40 stickers, batch, resume/retry, ZIP/manifest.

### M6 v1.0 Release Candidate
Regression/golden corpus, Windows packaging, audit evidence.

### M7 v1.0 Production Release
G4 approval and published release artifacts.

---

## 8. Quality Gates

- **G0 Requirements Ready** — measurable scope + acceptance + risk
- **G1 Design Ready** — interfaces/process/testability defined
- **G2 Verification Ready** — tests/static checks/non-destructive behavior
- **G3 Release Candidate** — regression + golden corpus + Windows smoke + docs/license review
- **G4 Production Release** — final audit + reproducible artifacts + installer/portable validation

No milestone may be marked complete solely because code exists; objective evidence is required.

---

## 9. Priority Rule

`Content Safety > Mandatory MVP Contract > Deterministic Correctness > LINE Compliance > Usability > Throughput > Advanced AI`

When tradeoffs occur, this order governs decisions unless Project Director approves a documented exception.

---

## 10. Change Control
Any change affecting crop, split, border removal, metadata removal, alpha/background removal, image quality, output dimensions or destructive behavior requires:

1. requirement review/update
2. ADR if architectural
3. regression tests
4. traceability update
5. changelog/update evidence
6. QA review before release

---

## 11. Project Control References
- `00_TEAM_GOVERNANCE.md`
- `01_PROJECT_CHARTER.md`
- `02_PRODUCT_REQUIREMENTS.md`
- `03_SYSTEM_ARCHITECTURE.md`
- `04_IMAGE_PROCESSING_PIPELINE.md`
- `06_QA_RULEBOOK.md`
- `13_QUALITY_MANAGEMENT_PLAN.md`
- `14_SOFTWARE_TEST_STRATEGY.md`
- `20_REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `21_PROJECT_EXECUTION_PLAN.md`
- `22_DEFINITION_OF_DONE.md`
- `23_SUPPORTED_INPUT_ARCHETYPES.md`
- `24_MVP_MINIMUM_FUNCTIONAL_BASELINE.md`

This document governs project direction; lower-level documents provide technical detail and evidence.
