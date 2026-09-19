# Quality Management Plan

## Objective
MTKrita ต้องให้ผลลัพธ์ที่รักษาคุณภาพต้นฉบับมากที่สุด, ไม่ทำลาย artwork โดยไม่แจ้ง, ทำงานซ้ำได้ และอธิบายเหตุผลของการตัดสินใจทุก frame ได้

## Quality Model
ใช้แนวคิดจาก ISO/IEC 25010 เป็นกรอบคุณลักษณะซอฟต์แวร์ โดยเน้น:
- Functional suitability
- Reliability
- Performance efficiency
- Usability
- Maintainability
- Portability
- Security/integrity of user files

## Image Quality Policy
1. Lossless-first: ใช้ PNG/RGBA ภายใน pipeline เมื่อเหมาะสม
2. Single final resize: หลีกเลี่ยงการ resize ซ้ำหลายทอด
3. No implicit JPEG recompression
4. Preserve semi-transparent antialiased edges
5. Preserve aspect ratio
6. Never upscale by default
7. Never silently discard foreground pixels
8. Original input is immutable by default

## Adaptive Border Removal Quality Standard
Border detection ทำระดับ per-frame หลัง split และต้องรองรับสี/ความหนาที่แตกต่างกัน

Evidence ที่ใช้ตัดสิน border:
- proximity to canvas edge
- long-run continuity
- rectangular geometry
- color/cohort consistency
- local thickness estimate
- connectedness to image boundary
- foreground-contact risk

ห้ามใช้ global color deletion เช่น “ลบสีเขียวทั้งหมด” โดยไม่มี topology/position constraints

### Confidence policy
- `>= high_threshold` → removable candidate; re-QA required
- `medium` → REVIEW
- `low` → KEEP / REVIEW

เมื่อ border และ artwork เชื่อมกัน ระบบต้อง conservative และห้ามลบส่วนที่ไม่สามารถแยกได้ด้วย confidence สูง

## Quality Metrics
ขั้นต่ำต้องวัดได้:
- extraction accuracy
- foreground pixel preservation
- alpha-edge preservation
- frame-order correctness
- false PASS rate
- false REVIEW rate
- processing reproducibility
- percentage of frames requiring manual touch
- average processing duration

## Release Quality Targets
ก่อน v1.0 ให้ตั้ง quantitative thresholds จาก golden corpus จริง ไม่ใช้ค่าประเมินลอย ๆ

## Nonconformance Handling
ทุก defect ที่กระทบ content loss, wrong frame, wrong transparency หรือ invalid LINE export จัดเป็น major/critical และต้อง:
1. freeze affected release,
2. reproduce,
3. add regression fixture,
4. fix root cause,
5. rerun affected and full critical regression suites.

## Quality Ownership
Senior Software Engineer owns technical quality; QA Auditor independently verifies evidence; Software Tester owns verification execution; Project Director owns release acceptance based on evidence.