# MTKrita MVP Minimum Functional Baseline

## Status
SSOT — Mandatory Minimum Capability Baseline v1.1

## Purpose
เอกสารนี้กำหนดความสามารถขั้นต่ำที่ MTKrita ต้องทำได้ก่อนถือว่า MVP ใช้งานได้จริง โดยยึด workflow การผลิตสติ๊กเกอร์ชีสเป็นหลัก

> **Sticker Sheet** ในโครงการนี้หมายถึงไฟล์รูปภาพหนึ่งไฟล์ที่ประกอบด้วยสติ๊กเกอร์หลายเฟรมอยู่ภายในภาพเดียวกัน

## MF-001 Split Sticker Sheet into Individual PNG Frames
ระบบต้องสามารถรับ Sticker Sheet แล้วแยกออกเป็นแต่ละเฟรม พร้อม export เป็นไฟล์ PNG แยกรายเฟรม

Required behavior:
- รองรับ layout แบบ configurable
- MVP baseline ต้องรองรับอย่างน้อย 2 rows × 5 columns = 10 frames
- รักษาลำดับเฟรมแบบ deterministic
- แต่ละ output ต้องเป็น PNG
- ห้าม overwrite source sheet

## MF-002 Remove Frame Border
หลัง split แล้ว ระบบต้องสามารถตรวจจับและลบเส้นขอบของแต่ละเฟรมได้

Required behavior:
- ทำงานแบบ per-frame
- รองรับ border หลายสี/ความหนา/anti-alias/resized
- ห้ามใช้ global color deletion เป็นวิธีหลัก
- ใช้ position, continuity, geometry, connectivity และ confidence
- หาก border สัมผัส artwork และแยกไม่มั่นใจ ต้องส่ง `REVIEW`
- ห้าม silent destructive removal

## MF-003 Remove Frame Number / Sheet Metadata
ระบบต้องสามารถตรวจจับและนำหมายเลขประจำเฟรมที่เป็น metadata ของ sheet ออก เช่น `01`, `02`, `31`, `40`

Required behavior:
- ทำหลัง split เป็น frame
- detection region configurable
- ต้องไม่ลบตัวเลขหรือข้อความที่เป็น sticker artwork
- automatic removal ต้องอาศัย confidence
- กรณีไม่มั่นใจต้อง `REVIEW`
- feature ต้องเปิด/ปิดได้ตาม profile
- detector/remover ควรสร้าง mask/evidence แยกจาก source-transparency provenance

## MF-004 Conditional Background Removal
ระบบต้องตรวจสอบว่า frame มี meaningful transparency อยู่แล้วหรือไม่ **ก่อน operation ใด ๆ ที่สามารถสร้าง alpha ใหม่ได้**

### Path A — Already Transparent
หาก source/extracted frame มี transparent background ที่ใช้งานได้อยู่แล้ว:
- ข้าม background-removal stage
- ห้าม segment/remove background ซ้ำโดยไม่จำเป็น
- รักษา alpha และ semi-transparent anti-aliased edges
- metadata cleanup ที่อนุมัติแล้วสามารถ apply เพิ่มบน alpha เดิมได้

### Path B — Opaque / Non-transparent Background
หาก source/extracted frame ไม่มี meaningful transparency:
- route นี้ต้องคงเป็น opaque route แม้ metadata cleanup จะสร้าง transparent pixels ภายหลัง
- วิเคราะห์ background
- สร้าง foreground mask
- remove background
- ผสาน approved metadata mask ตามลำดับที่กำหนด
- สร้าง RGBA output ที่ background เป็น transparent
- หาก segmentation confidence ต่ำ ต้อง `REVIEW`

## MF-005 PNG Output Contract
ทุกเฟรมที่ผ่าน processing ต้องสามารถ export เป็น PNG ได้ พร้อม deterministic filename และ source traceability

# Mandatory Processing Workflow

```text
Sticker Sheet Input
        ↓
File Inspection
        ↓
Layout / Grid Detection
        ↓
Split Frames
        ↓
Detect & Remove Frame Border (safe/high-confidence only)
        ↓
Classify Source Transparency Provenance
        ↓
Detect Frame Number / Metadata → cleanup mask/evidence
        ↓
Route using Source Transparency Decision
        ├─ source meaningful alpha exists
        │      ↓
        │ preserve alpha + apply approved metadata cleanup
        │      ↓
        │ SKIP background removal
        │
        └─ source opaque / no meaningful alpha
               ↓
           Remove Background
               ↓
           Apply Metadata Mask
               ↓
           Create Transparent RGBA
        ↓
Content / Edge QA
        ↓
PNG Export
        ↓
Manifest / Findings / Provenance
```

# Mandatory Safety Rules
1. Source immutable by default
2. No silent content loss
3. Transparent means skip — based on **source transparency provenance**, not alpha created later by cleanup
4. Metadata is not artwork when confidently identified
5. Ambiguous means REVIEW
6. Lossless-first
7. Traceable outputs
8. Routing provenance is immutable for the frame unless explicit approved override applies

# MVP Acceptance Criteria
MVP ขั้นต่ำจะถือว่าผ่านเมื่อชุดทดสอบที่อนุมัติสามารถพิสูจน์ได้ว่า:
- 5×2 sheet ถูก split เป็น 10 PNG ถูกลำดับ
- border ถูกลบในกรณี high-confidence โดยไม่สูญเสีย artwork
- frame number ถูกลบโดยไม่กระทบ caption/artwork
- source-transparent frame ข้าม background removal
- source-opaque frame ยังคงเข้า background removal แม้ metadata cleanup จะสร้าง alpha
- ambiguous border/number/background cases ถูกส่ง `REVIEW`
- source hash ไม่เปลี่ยนหลัง processing
- ไม่มี Critical defect ที่ทำให้เกิด silent content loss

# Scope Priority
ก่อนเพิ่มฟีเจอร์ขั้นสูง ระบบต้องทำ MF-001 ถึง MF-005 ให้ผ่าน acceptance criteria ก่อน

References: `DECISIONS.md` ADR-023, `27_END_TO_END_WORKFLOW_SPEC.md`, `35_INTERFACE_AND_STAGE_CONTRACTS.md`.
