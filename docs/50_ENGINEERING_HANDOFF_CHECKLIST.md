# MTKrita Engineering Handoff Checklist

## Status
SSOT — Developer Handoff Readiness Checklist v1.0

## Purpose
ใช้ตรวจว่าทีมพัฒนาสามารถรับช่วงต่อได้โดยไม่ต้อง reconstruct intent จากบทสนทนาเดิม

## Mandatory Handoff Conditions
- [ ] อ่าน `42_DEVELOPER_START_HERE.md`
- [ ] อ่าน `37_DEVELOPER_HANDOFF_PACKAGE.md`
- [ ] เข้าใจ SSOT hierarchy และ change-control rule
- [ ] เข้าใจ Python MainBoard / orchestration model
- [ ] เข้าใจ provider interfaces และ TOML configuration
- [ ] เข้าใจ PathManager / ResourceBroker / worker isolation
- [ ] เข้าใจ Job/Frame/Stage state machines
- [ ] เข้าใจ retry, lease, attempt, checkpoint, resume rules
- [ ] เข้าใจ accepted input archetypes และ mandatory MVP flow
- [ ] เข้าใจ acceptance matrix และ golden-corpus requirements
- [ ] ตรวจ `43_CURRENT_IMPLEMENTATION_STATUS_AND_KNOWN_GAPS.md`
- [ ] ตรวจ issue/PR ที่ active ก่อนเริ่มแก้โค้ด

## Before Starting Any Work Package
1. ระบุ requirement/ADR ที่ authorize งาน
2. ระบุ stage/interface ที่ได้รับผลกระทบ
3. ระบุ test/acceptance evidence ที่ต้องเพิ่ม
4. ระบุ destructive-risk และ REVIEW fallback
5. ตรวจว่า path/config/state/shared-resource behavior ยังสอดคล้อง SSOT

## Before Opening a PR
- SSOT references ครบ
- test ใหม่/แก้ไขผ่าน
- static checks ผ่าน
- no source overwrite
- no direct shared-state write from worker
- no raw path construction outside PathManager boundary
- no concrete-provider dependency leak into domain/orchestrator
- config behavior documented in TOML schema/spec
- diagnostics/error codes updated if new failure mode introduced

## Handoff Result
เมื่อ checklist นี้ครบ ทีมพัฒนาสามารถดำเนินงานตาม WBS และ M2/M3 plan ได้โดยไม่ต้องอาศัยข้อมูลสำคัญจาก chat history
