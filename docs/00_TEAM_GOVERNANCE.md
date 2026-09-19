# MTKrita Project Governance and Virtual Team RACI

## Status
SSOT — Governance Baseline v1.0

## Purpose
กำหนดบทบาท ความรับผิดชอบ อำนาจอนุมัติ และ quality gates สำหรับการพัฒนา MTKrita ให้เป็น Sticker Production Automation Machine ที่ตรวจสอบย้อนหลังได้และพัฒนาได้อย่างเป็นระบบ

## Working Model
ตำแหน่งต่อไปนี้เป็น **บทบาทวิชาชีพเสมือน (virtual professional roles)** ที่ใช้แยกมุมมองและความรับผิดชอบของงาน ไม่ได้หมายความว่ามีบุคลากรมนุษย์หลายคนเข้าร่วมจริง

## Roles

### Project Director
- รักษา product vision และ business outcome
- อนุมัติ phase gate และ scope change ที่มีผลระดับโครงการ
- ตัดสินข้อขัดแย้งด้าน scope / quality / schedule

### Senior Project Manager
- WBS, milestone, dependency, risk, decision log
- ตรวจ traceability ระหว่าง requirement → implementation → test → release
- ดูแล Definition of Ready / Definition of Done

### Senior Software Engineer
- ออกแบบ architecture, interfaces, error handling, configuration model
- coding standards, maintainability, dependency isolation
- non-destructive and deterministic design

### Senior Process Engineer
- ออกแบบสายการผลิต image-processing แบบ end-to-end
- ลด rework, manual touch และ hidden variation
- นิยาม process capability, failure mode และ fallback

### Senior Pipeline Engineer
- ออกแบบ orchestration: ingest → split → border removal → alpha/background → fit → QA → export
- batch processing, idempotency, job manifests, recovery
- performance and observability

### UI/UX Designer
- desktop workflow, information hierarchy, error/review states
- interaction design สำหรับ drag/drop, preview, review queue และ export
- usability/accessibility baseline

### Software QA Auditor
- ตรวจ compliance กับ requirement และ quality policy
- review evidence ก่อน release
- ตรวจว่า QA engine ไม่มี false-pass ที่ยอมรับไม่ได้

### Software Auditor
- ตรวจ design controls, change controls, configuration management, reproducibility และ audit trail
- ตรวจ third-party license boundary

### Senior Software Tester
- test strategy, golden corpus, regression, destructive-edge cases
- Windows installation and end-to-end acceptance testing
- defect reproduction and release verification

### Senior Software Document Writer
- ควบคุม SSOT, terminology, document IDs, revision and changelog
- ทำให้เอกสาร actionable และ consistent กับ implementation

## RACI Summary

| Workstream | Director | PM | SW Eng | Process | Pipeline | UX | QA Auditor | Auditor | Tester | Doc Writer |
|---|---|---|---|---|---|---|---|---|---|---|
| Product scope | A | R | C | C | C | C | C | C | I | C |
| Architecture | C | C | A/R | C | R | I | C | C | C | C |
| Processing rules | I | C | R | A/R | R | I | C | C | R | C |
| UI/UX | I | C | C | C | C | A/R | C | I | C | C |
| Test strategy | I | C | C | C | C | C | C | C | A/R | C |
| Quality gate | I | C | C | C | C | C | A/R | R | R | C |
| Release approval | A | R | C | C | C | C | R | R | R | C |
| Documentation | C | C | C | C | C | C | C | C | C | A/R |

A = Accountable, R = Responsible, C = Consulted, I = Informed

## Quality Gates

### Gate G0 — Requirements Ready
Must have: approved scope, measurable acceptance criteria, risks, external constraints.

### Gate G1 — Design Ready
Must have: architecture, interfaces, processing rules, testability, rollback/error strategy.

### Gate G2 — Implementation Ready for Verification
Must have: unit tests, static checks, deterministic config, no destructive silent behavior.

### Gate G3 — Release Candidate
Must have: regression pass, golden corpus pass, Windows smoke test, license review, documentation complete.

### Gate G4 — Production Release
Must have: release audit, signed-off known limitations, reproducible build evidence, installer/portable validation.

## Change Control
Any change that affects image quality, cropping, segmentation, border removal, export dimensions, LINE rules, or destructive behavior requires:
1. requirement update,
2. decision record if architectural,
3. tests added/updated,
4. changelog entry,
5. QA review before release.
