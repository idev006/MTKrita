# MTKrita Master Project Control

## Status
SSOT — Project Control Baseline v1.7

## Purpose
เอกสารควบคุมระดับบนสุดของโครงการ MTKrita เชื่อม Vision → Goals → Objectives → Mandatory Workflow → Workstreams → Milestones → Quality Gates → Release Criteria และป้องกัน scope drift

## Operating Principle
MTKrita เป็น **Document-Driven Project with SSOT** และใช้ **Python เป็น Orchestration / Control Plane**

> **Document first, implementation second, evidence always.**

> **If it is not captured in the approved SSOT, it is not yet project truth.**

รายละเอียด: `25_DOCUMENT_DRIVEN_SSOT_OPERATING_MODEL.md`

## 1. Project Vision
สร้าง Windows 11 application ที่เป็น **Sticker Production Automation Machine** สามารถรับ Sticker Sheet แล้วแยกและประมวลผลเป็น PNG รายเฟรมอย่างปลอดภัย ตรวจสอบได้ ลดงาน manual และรักษาคุณภาพ artwork โดยรองรับทั้ง transparent และ non-transparent input

## 2. Project Goals
- **G-01 Automation** — ลด manual work ใน split, border removal, frame-number removal, background routing/removal, PNG export
- **G-02 Content Safety** — ห้าม silent loss ของตัวละคร ข้อความ white outline props หรือ artwork
- **G-03 Quality Preservation** — lossless-first, preserve alpha/anti-alias, avoid repeated resize, no default upscale
- **G-04 Repeatability** — deterministic stages reproducible จาก source/config/version เดียวกัน
- **G-05 Production Readiness** — batch production + Windows 11 standalone distribution
- **G-06 Engine Independence** — ใช้ proven/open-source providers หลัง stable interfaces โดยไม่ผูก domain workflow กับ engine เดียว
- **G-07 Auditable Behavior** — workflow, use cases, UML, state, sequence, recovery และ stage contracts ต้องอยู่ใน SSOT
- **G-08 Developer Handoff Readiness** — ทีมพัฒนาต้องสามารถเริ่มงานจาก SSOT ได้โดยไม่ต้อง reconstruct intent จากบทสนทนา
- **G-09 Interface-First Extensibility** — orchestrator/domain layer ต้องพึ่ง provider contracts ไม่พึ่ง concrete engine implementations
- **G-10 Configuration Consistency** — TOML เป็น canonical human-maintained configuration format และ effective config ต้อง validate/hash ได้
- **G-11 Centralized Resource Safety** — path และ shared mutable resource ต้องผ่าน PathManager/ResourceBroker
- **G-12 Parallel Production** — รองรับ batch + multi-worker parallel execution โดย worker แยกกันและ shared-state commitment ถูกควบคุมจากส่วนกลาง
- **G-13 Operational Resilience** — pause/stop/resume/retry/recover/checkpoint/log/diagnostic เป็น first-class system behavior
- **G-14 Verification Readiness** — golden corpus, acceptance matrix, release sign-off และ operational runbook ต้องพร้อมก่อน milestone gate ที่เกี่ยวข้อง
- **G-15 Automated Testability** — critical code ต้องออกแบบให้ทดสอบ headless/automated ได้ง่าย โดย dependencies สำคัญสามารถ substitute/inject ได้ และ critical defects ต้องกลายเป็น regression tests

## 3. Mandatory Minimum Objectives
MVP ต้องพิสูจน์ได้ว่า:
1. Sticker Sheet 5×2 split เป็น 10 PNG ตามลำดับถูกต้อง
2. Border หลายสี/หลายความหนาถูกลบเมื่อ confidence สูง
3. Frame number / sheet metadata ถูกลบโดยไม่ทำลาย artwork
4. meaningful transparency ต้อง bypass background removal
5. opaque frame route เข้าสู่ background-removal และสร้าง transparent RGBA สำหรับ supported archetypes
6. ambiguous destructive case → REVIEW
7. source immutable และ source hash คงเดิม
8. final PNG trace กลับ source sheet/frame ได้
9. critical implementation trace กลับ requirement/design/test ได้
10. job/frame lifecycle และ recovery behavior ต้องเป็นไปตาม state/recovery SSOT
11. replaceable processing capabilities ต้องอยู่หลัง stable interfaces/provider contracts
12. configuration ที่มีผลต่อ behavior ต้องถูก load/validate จาก TOML และบันทึก effective config hash
13. critical runtime paths ต้องผ่าน PathManager/typed refs และ shared mutable resources ต้องถูก brokered
14. batch/multi-worker execution ต้องป้องกัน stale/duplicate worker result จากการ overwrite authoritative state
15. system restart ต้อง reconcile incomplete work และสามารถ resume จาก safe checkpoint ได้
16. structured logs + stable error codes + correlation identifiers ต้องเพียงพอสำหรับ diagnosis
17. target milestone ต้องมี acceptance/golden-corpus evidence และ release/sign-off record ตาม gate
18. critical features ต้องมี automated unit/contract/component/integration/regression tests ตามความเหมาะสม และ critical reliability paths ต้องรองรับ fault-injection/recovery tests

## 4. Mandatory End-to-End Workflow
```text
Sticker Sheet Input
  ↓
File Inspection / Fingerprint
  ↓
Layout Detection
  ↓
Split Frames
  ↓
Adaptive Border Detection & Removal
  ↓
Frame Number / Metadata Detection & Removal
  ↓
Transparency Routing
  ├─ meaningful alpha → preserve / skip BG removal
  └─ opaque → background removal → transparent RGBA
  ↓
Content Bounds / Edge Safety
  ↓
Smart Fit / Quality Preservation
  ↓
QA → PASS / AUTO_FIXED / REVIEW / FAIL
  ↓
PNG Export
  ↓
Manifest / Evidence / Package
```

Authoritative workflow detail: `27_END_TO_END_WORKFLOW_SPEC.md`.

## 5. Architecture Control Rules
- Python owns orchestration, routing, state, QA policy and evidence.
- Replaceable image-processing capabilities are accessed through MTKrita-owned interfaces.
- Concrete providers are composed at the system edge through a registry/factory.
- Provider-specific objects must not leak into stable domain contracts without wrappers.
- TOML is the canonical human-maintained configuration format.
- Runtime paths participating in the application contract are resolved through `PathManager` or typed path refs.
- MainBoard/control-plane services coordinate jobs/workers/resources; MainBoard is not a monolithic God Object.
- Workers perform isolated computation and may use only immutable inputs + private scratch; they do not mutate shared job state/final outputs directly.
- Shared-state commitment is serialized/transactional through MainBoard-owned services such as ResourceBroker/JobStore.
- Worker result acceptance uses task attempt/lease identity; stale late results are rejected.
- Durable checkpoints, startup reconciliation, structured logs and diagnostic evidence are architectural requirements.
- Critical behavior must be headless-testable; provider/infrastructure dependencies use explicit replaceable seams where needed.
- Hidden global mutable state and UI-only business logic are prohibited because they undermine testability and reuse.

References: `44_PROVIDER_INTERFACE_ARCHITECTURE.md` through `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`, ADR-015 through ADR-022.

## 6. Scope Boundaries
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
- deep Krita integration
- automatic LINE submission

Optional features may not delay mandatory MVP correctness.

## 7. Workstreams
- **WS1 Product/Governance** — Project Director + PM
- **WS2 Core Architecture** — Senior Software Engineer
- **WS3 Image Processing** — Senior Process Engineer + Pipeline Engineer
- **WS4 Verification** — Senior Software Tester + QA Auditor
- **WS5 Desktop UX** — UI/UX Designer + Software Engineer
- **WS6 Distribution** — Pipeline Engineer + Tester
- **WS7 Documentation/Audit** — Document Writer + Software Auditor

Role competency/authority SSOT: `26_PROJECT_TEAM_ROLES_AND_COMPETENCY_MODEL.md`.

## 8. Milestones
- **M0 Documentation Baseline — COMPLETE** — governance, requirements, architecture, behavioral models, QA/testing/traceability and developer handoff baseline approved
- **M1 Core Skeleton — COMPLETE** — CLI, manifests, immutable inspection, test harness, Windows CI
- **M2 Transparent Processing Baseline — IN PROGRESS** — split + border + metadata + transparency routing + content/smart-fit + PNG validation
- **M3 Opaque Processing Baseline** — background removal + REVIEW fallback + mixed corpus E2E
- **M4 Desktop Beta** — drag/drop UI, exception-first review, preview, export
- **M5 Production Automation** — 4 sheets/40 stickers, batch, multi-worker, pause/resume/recovery, ZIP/manifest
- **M6 v1.0 Release Candidate** — regression/golden corpus, Windows packaging, reliability fault-injection, audit evidence
- **M7 v1.0 Production Release** — G4 approval and release artifacts

## 9. Quality Gates
- **G0 Requirements Ready** — measurable scope + acceptance + risk
- **G1 Design Ready** — architecture + workflow + interfaces + state/error strategy + testability
- **G2 Verification Ready** — automated tests/static checks/non-destructive behavior + traceability
- **G3 Release Candidate** — regression + golden corpus + Windows smoke + reliability/recovery evidence + docs/license review
- **G4 Production Release** — final audit + reproducible artifacts + installer/portable validation

No milestone is complete solely because code exists; objective evidence is mandatory.

## 10. Priority Rule
`Content Safety > Data/State Integrity > Mandatory MVP Contract > SSOT Compliance > Deterministic Correctness > Recoverability > LINE Compliance > Usability > Throughput > Advanced AI`

## 11. Change Control
Changes affecting split/crop, border, metadata, alpha/background, quality, dimensions, destructive behavior, provider architecture, orchestration, state/recovery, path/resource ownership, worker protocol, configuration schema, test seams or output contract require:
1. SSOT requirement/design review
2. ADR if architectural
3. automated regression/fault tests
4. traceability update
5. changelog/evidence update
6. QA review before release

## 12. Developer Handoff Package
Development teams begin with:
- `42_DEVELOPER_START_HERE.md`
- `37_DEVELOPER_HANDOFF_PACKAGE.md`
- `50_ENGINEERING_HANDOFF_CHECKLIST.md`
- `51_REFERENCE_IMPLEMENTATION_BLUEPRINT.md`
- `38_IMPLEMENTATION_BACKLOG_AND_WORK_BREAKDOWN.md`
- `41_M2_M3_IMPLEMENTATION_PLAN.md`
- `40_ACCEPTANCE_TEST_MATRIX.md`
- `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`
- `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`
- `39_CODING_STANDARDS_AND_REPO_CONVENTIONS.md`
- `43_CURRENT_IMPLEMENTATION_STATUS_AND_KNOWN_GAPS.md`

Operations/release/maintenance references:
- `53_OPERATIONAL_RUNBOOK.md`
- `54_RELEASE_AND_SIGNOFF_CHECKLIST.md`
- `55_PROJECT_GLOSSARY_AND_NAMING.md`
- `56_MAINTENANCE_AND_EXTENSION_GUIDE.md`
- `57_TEAM_EXECUTION_PLAYBOOK.md`
- `58_SSOT_COVERAGE_AUDIT.md`

## 13. Documentation Handoff Status
`58_SSOT_COVERAGE_AUDIT.md` records **READY FOR DEVELOPMENT HANDOFF**. This status means documentation is sufficient to continue implementation; it does not mean the software itself is production-ready.

## 14. Project Control References
See `docs/README.md` for the complete indexed SSOT set.

This document governs project direction; lower-level SSOT documents provide detailed behavior, design, execution and evidence rules.
