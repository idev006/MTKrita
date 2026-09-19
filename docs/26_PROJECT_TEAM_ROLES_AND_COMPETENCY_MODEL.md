# Project Team Roles and Competency Model

## Status
SSOT — Team Roles & Competency Baseline v1.0

## Purpose
กำหนดโครงสร้างทีม บทบาท ความสามารถหลัก หน้าที่ อำนาจการตัดสินใจ ผลส่งมอบ และหลักฐานที่ต้องรับผิดชอบของแต่ละตำแหน่งในโครงการ MTKrita ภายใต้แนวทาง Document-Driven Project + SSOT

ตำแหน่งในเอกสารนี้เป็น **virtual professional roles** สำหรับการแบ่งความรับผิดชอบและมุมมองเชิงวิชาชีพของโครงการ ไม่ได้หมายความว่ามีบุคลากรมนุษย์หลายคนเข้าร่วมจริง

---

## 1. Operating Principle

โครงการยึดหลัก:

`Competency → Responsibility → Deliverable → Evidence → Quality Gate`

และ:

`Responsibility ≠ Authority`

ผู้ที่เป็นผู้พัฒนาหรือผู้รับผิดชอบงาน ไม่มีสิทธิ์เปลี่ยน requirement, ลด quality threshold หรืออนุมัติ release นอกขอบเขตอำนาจของตนเองโดยไม่ผ่าน change control

---

## 2. Project Director

### Core Competencies
- product vision and strategic governance
- portfolio / program decision making
- scope-quality-schedule tradeoff governance
- executive risk management
- release and phase-gate governance

### Primary Duties
- รักษา vision และ business outcome ของ MTKrita
- อนุมัติ scope baseline และการเปลี่ยนแปลงระดับโครงการ
- ตัดสินข้อขัดแย้งด้าน scope / quality / schedule
- อนุมัติ production release หลังได้รับ evidence จากทีมที่เกี่ยวข้อง

### Authority
- final authority สำหรับ project scope change ระดับสำคัญ
- final approval สำหรับ G4 Production Release
- อนุมัติ documented exception ต่อ priority rule เมื่อจำเป็น

### Key Deliverables / Evidence
- vision/scope approval
- gate approval record
- major exception decision record
- release authorization

---

## 3. Senior Project Manager

### Core Competencies
- project planning, WBS, dependency management
- milestone and critical-path management
- risk/issue/change management
- requirements traceability governance
- Definition of Ready / Definition of Done

### Primary Duties
- ดูแล milestone M0–M7 และ dependency ระหว่าง workstreams
- ควบคุม backlog, risk register, decision cadence และ status
- ตรวจ requirement → design → code → test → evidence traceability
- ป้องกัน scope drift และ undocumented work

### Authority
- ควบคุม execution plan และ milestone readiness
- ปฏิเสธ work item ที่ไม่ผ่าน Definition of Ready
- ปฏิเสธ milestone close หาก evidence ไม่ครบ

### Key Deliverables / Evidence
- project execution plan
- milestone status
- risk register
- dependency map
- change log coordination
- gate-readiness evidence index

---

## 4. Senior Software Engineer

### Core Competencies
- Python software architecture
- modular/domain-driven design
- API/interface contracts
- error handling and observability
- dependency isolation
- automated testing and maintainability
- Windows-compatible Python packaging awareness

### Primary Duties
- ออกแบบ core architecture และ module boundaries
- รักษา Python orchestration/control-plane architecture
- นิยาม provider interfaces และ engine abstraction
- code review ด้าน correctness, maintainability, safety
- ป้องกัน UI/business logic coupling

### Authority
- accountable สำหรับ technical architecture
- อนุมัติ implementation design ภายใน requirement/ADR ที่อนุมัติแล้ว
- ไม่มีสิทธิ์เปลี่ยน business requirement หรือ quality gate เอง

### Key Deliverables / Evidence
- system architecture
- ADR proposals
- source code / interfaces
- unit/component test evidence
- technical review notes

---

## 5. Senior Process Engineer

### Core Competencies
- process engineering and optimization
- process capability / failure mode analysis
- FMEA-style risk thinking
- deterministic workflow design
- rework reduction and exception handling

### Primary Duties
- ออกแบบ end-to-end sticker production process
- กำหนด sequence และ decision points เช่น split → border → metadata → transparency routing → background → QA → export
- ระบุ failure modes, fallback และ REVIEW conditions
- ลด manual touch และ hidden process variation

### Authority
- process owner สำหรับ image-production workflow
- เสนอ/อนุมัติ process design ภายใน scope ที่ได้รับอนุมัติ
- destructive behavior ต้องผ่าน QA/change control

### Key Deliverables / Evidence
- process flow
- stage contracts
- failure-mode analysis
- process acceptance criteria
- process capability evidence

---

## 6. Senior Pipeline Engineer

### Core Competencies
- orchestration and workflow engines
- idempotency, retry, recovery
- batch processing
- manifests and job state
- provider integration
- observability/performance

### Primary Duties
- สร้าง Python orchestration pipeline
- ประสาน OpenCV, Pillow และ optional providers
- ดูแล job lifecycle, resume/retry, batch 10/40 stickers
- ทำให้ทุก frame trace กลับ source/config/version ได้

### Authority
- accountable สำหรับ pipeline implementation
- เลือก technical orchestration pattern ภายใน architecture/ADR
- provider replacement ต้องรักษา interface contract และ evidence

### Key Deliverables / Evidence
- JobController / pipeline modules
- job manifest schema
- batch/recovery design
- pipeline test evidence
- performance/observability evidence

---

## 7. UI/UX Designer

### Core Competencies
- desktop UX / information architecture
- exception-first workflow design
- visual hierarchy and feedback states
- accessibility/usability
- error/review interaction design

### Primary Duties
- ออกแบบ Windows desktop workflow
- ทำให้ผู้ใช้เห็น PASS/AUTO_FIXED/REVIEW/FAIL ชัดเจน
- ออกแบบ source/mask/border/final preview
- ลดการตรวจ manual โดยเน้น exception review

### Authority
- accountable สำหรับ UX specification
- ไม่สามารถลด safety/QA behavior เพื่อแลก usability โดยไม่ผ่าน change control

### Key Deliverables / Evidence
- UX flows
- wireframes/specification
- interaction states
- usability acceptance evidence

---

## 8. Software QA Auditor

### Core Competencies
- software quality systems
- requirement compliance audit
- verification evidence review
- defect severity governance
- false-pass / release-risk analysis

### Primary Duties
- ตรวจว่า implementation ตรง requirement และ quality policy
- ตรวจ evidence ก่อน milestone/release gate
- ตรวจว่า QA engine ไม่มี unacceptable false-pass
- ตรวจ destructive-risk controls

### Authority
- สามารถ block quality gate เมื่อ evidence ไม่พอ
- สามารถ require corrective action / additional testing
- ไม่มีอำนาจเปลี่ยน product requirement โดยลำพัง

### Key Deliverables / Evidence
- QA audit report
- gate findings
- nonconformity records
- release-quality sign-off evidence

---

## 9. Software Auditor

### Core Competencies
- design/change/configuration control
- audit trail and reproducibility
- third-party dependency/license review
- release governance
- evidence integrity

### Primary Duties
- ตรวจ SSOT consistency และ change control
- ตรวจ configuration/version/reproducibility
- ตรวจ third-party license boundaries
- ตรวจ release artifact traceability

### Authority
- block release เมื่อ audit trail / compliance evidence ไม่ครบ
- require documentation or configuration correction

### Key Deliverables / Evidence
- audit report
- configuration-control evidence
- license/dependency inventory
- release audit checklist

---

## 10. Senior Software Tester

### Core Competencies
- test strategy and test design
- unit/component/integration/E2E testing
- regression and golden corpus
- image-processing edge cases
- Windows installation/clean-machine testing
- defect reproduction

### Primary Duties
- สร้าง test strategy และ test suites
- ดูแล golden corpus transparent/opaque/mixed cases
- ทดสอบ destructive edge cases และ regression
- ทดสอบ installer/portable build บน Windows

### Authority
- test sign-off ตาม acceptance criteria
- สามารถ block gate เมื่อ mandatory tests fail
- ไม่สามารถ waive failed acceptance criteria โดยลำพัง

### Key Deliverables / Evidence
- test plan
- test cases
- automated test suite
- regression report
- defect records
- release verification evidence

---

## 11. Senior Software Document Writer

### Core Competencies
- technical writing
- SSOT information architecture
- terminology and revision control
- requirements documentation
- traceability documentation
- change-log discipline

### Primary Duties
- ควบคุมเอกสาร SSOT ให้สอดคล้องกัน
- ดูแล document IDs, status, revision, cross-reference
- เปลี่ยนการตัดสินใจสำคัญจากบทสนทนาให้เป็นเอกสารที่ actionable
- ตรวจว่าเอกสารนำ implementation ไม่ใช่ตามหลัง implementation

### Authority
- accountable สำหรับ document structure/quality
- สามารถปฏิเสธการประกาศข้อมูลเป็น project truth หากยังไม่ได้บันทึกใน SSOT
- ไม่มีอำนาจเปลี่ยน requirement content โดยไม่ผ่าน owner/change control

### Key Deliverables / Evidence
- SSOT documents
- revision/changelog
- terminology consistency
- traceability references
- documentation completeness report

---

## 12. Cross-Role Control Rules

1. ไม่มีตำแหน่งใดแก้ requirement สำคัญโดยลำพัง
2. งานที่มี destructive risk ต้องผ่าน Process + Software + QA/Test review ตามระดับความเสี่ยง
3. Architecture change ต้องมี ADR
4. Requirement change ต้องอัปเดต requirement + traceability + tests
5. Release change ต้องมี changelog + release evidence
6. ข้อมูลสำคัญที่อยู่เฉพาะใน chat/meeting/issue แต่ยังไม่เข้า SSOT ยังไม่ถือเป็น project truth
7. Source code ที่ขัดกับ SSOT ต้องถูกแก้ที่ code หรือผ่าน change control เพื่อแก้ SSOT ก่อน

---

## 13. Team RACI Reference
RACI ระดับ workstream อยู่ที่ `00_TEAM_GOVERNANCE.md` เอกสารนี้เป็น SSOT สำหรับ competency, duties, authority และ deliverables ของแต่ละ role

---

## 14. Review Cadence
เอกสารนี้ต้องถูก review เมื่อ:
- เพิ่ม/ลดบทบาททีม
- เปลี่ยน authority หรือ quality gate
- เพิ่ม workstream ใหม่
- พบ responsibility gap หรือ overlap ที่ทำให้เกิด defect / delay / audit finding

ทุกการเปลี่ยนต้องผ่าน Document-Driven SSOT change control
