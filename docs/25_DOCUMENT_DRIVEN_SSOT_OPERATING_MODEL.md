# MTKrita Document-Driven SSOT Operating Model

## Status
SSOT — Operating Model v1.0

## Purpose
กำหนดวิธีทำงานของโครงการ MTKrita ให้เป็น **Document-Driven Project** ที่มี **Single Source of Truth (SSOT)** ชัดเจน โดยเอกสารที่ได้รับการอนุมัติเป็นตัวกำหนดสิ่งที่ต้องสร้าง วิธีตรวจรับ และเงื่อนไขที่ถือว่างานเสร็จ ไม่ใช่ให้โค้ดเป็นตัวสร้าง requirement ย้อนหลัง

---

## 1. Core Philosophy

> **Document first, implementation second, evidence always.**

ลำดับการทำงานมาตรฐานคือ:

```text
Intent / Owner Decision
        ↓
SSOT Requirement
        ↓
Architecture / ADR / Process Rule
        ↓
Acceptance Criteria
        ↓
Traceability Mapping
        ↓
Implementation
        ↓
Automated / Manual Verification
        ↓
Evidence
        ↓
Gate Approval
        ↓
Release
```

ห้ามถือว่า feature เสร็จเพียงเพราะ code compile หรือทำงานในตัวอย่างหนึ่งได้

---

## 2. SSOT Hierarchy

หากข้อมูลขัดกัน ให้ใช้ลำดับอำนาจดังนี้:

1. `MASTER_PROJECT_CONTROL.md` — project direction / scope / priorities / gates
2. `00_TEAM_GOVERNANCE.md` — roles / authority / quality gates / change control
3. `01_PROJECT_CHARTER.md` — vision / purpose / project success
4. `02_PRODUCT_REQUIREMENTS.md` — functional / non-functional requirements
5. `24_MVP_MINIMUM_FUNCTIONAL_BASELINE.md` — mandatory MVP contract
6. `DECISIONS.md` — accepted architectural decisions
7. `03_SYSTEM_ARCHITECTURE.md` / `04_IMAGE_PROCESSING_PIPELINE.md` — design and processing model
8. QA / Test / Traceability documents — verification and evidence rules
9. GitHub Issues / PRs — execution units derived from the SSOT
10. Source code — implementation of approved requirements and design

Source code must not silently redefine upstream requirements.

---

## 3. Required Change Flow

Any change affecting behavior, image quality, processing order, destructive operation, supported input, output contract, dependency/runtime architecture or release condition must follow:

```text
Change request
   ↓
Impact analysis
   ↓
Update requirement / SSOT
   ↓
ADR if architectural
   ↓
Update traceability
   ↓
Update acceptance tests
   ↓
Implement
   ↓
Verify
   ↓
Record evidence
```

Emergency defect fixes may implement and document in the same PR, but the PR cannot be considered complete until SSOT and regression evidence are synchronized.

---

## 4. Python Orchestrator Principle

MTKrita uses **Python as the orchestration/control plane** of the system.

Python is responsible for:
- interpreting project/domain rules,
- selecting the correct processing path,
- invoking image-processing providers/engines,
- passing artifacts between stages,
- applying confidence thresholds,
- enforcing PASS / AUTO_FIXED / REVIEW / FAIL routing,
- maintaining manifest/audit evidence,
- providing the same core workflow to CLI, GUI, batch and future API modes.

Python is **not required to reimplement every image-processing algorithm**. Proven open-source engines/libraries may provide lower-level capabilities.

Reference provider model:

```text
                 Python Orchestrator
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
      OpenCV          Pillow        Optional Providers
        │               │           ImageMagick / ML
        └───────────────┼────────────────┘
                        ▼
                Sticker Domain Pipeline
```

Provider selection must remain replaceable behind stable interfaces where practical.

---

## 5. Engine-Agnostic Rule

Domain rules must not be embedded irreversibly inside one third-party engine.

Examples:
- `BackgroundRemovalProvider`
- `BorderDetector`
- `MetadataDetector`
- `GridDetector`
- `ExportProvider`

The orchestrator owns **when and why** a capability is used; a provider owns **how** a specific image-processing operation is executed.

Changing a provider should not require rewriting the complete sticker workflow unless an approved ADR explicitly changes the architecture.

---

## 6. Mandatory Stage Contract

Every critical pipeline stage must define:
- input contract,
- output contract,
- deterministic/non-deterministic classification,
- confidence or validation evidence when relevant,
- failure behavior,
- REVIEW behavior for ambiguity,
- test coverage,
- traceability ID.

Example:

```text
Stage: Frame Number Removal
Input: extracted frame
Output: cleaned frame + metadata findings + confidence
Unsafe ambiguity: REVIEW
Destructive silent fallback: prohibited
```

---

## 7. Definition of Ready for Implementation

A critical feature is ready for coding only when:
- requirement exists in SSOT,
- expected behavior is measurable,
- destructive-risk behavior is defined,
- acceptance test cases are identified,
- architecture/process owner is known,
- traceability entry exists or is created in the same change set.

---

## 8. Definition of Done for a Feature

A feature is complete only when:
- implementation matches the approved SSOT,
- unit/component/integration tests pass as applicable,
- regression cases are added for fixed defects,
- source remains non-destructive where required,
- audit/manifest evidence is available where required,
- traceability is updated,
- docs match implementation,
- relevant quality gate is passed.

---

## 9. GitHub Execution Rule

GitHub Issues and Pull Requests are **execution records**, not the authoritative source of product intent.

Each implementation issue/PR must reference the requirement/ADR/test documents that authorize it.

PR review order:
1. SSOT alignment
2. safety / destructive-risk review
3. architecture/process fit
4. tests and regression evidence
5. code quality
6. documentation synchronization

---

## 10. Project Principle Summary

MTKrita shall be operated as:

> **A document-driven, SSOT-controlled, Python-orchestrated, engine-agnostic sticker-production automation system with measurable gates and auditable evidence.**

This statement is an architectural and governance principle of the project.
