# MTKrita MVP Minimum Functional Baseline

## Status
SSOT — Mandatory Minimum Capability Baseline v1.0

## Purpose
เอกสารนี้กำหนดความสามารถขั้นต่ำที่ MTKrita ต้องทำได้ก่อนถือว่า MVP ใช้งานได้จริง โดยยึด workflow การผลิตสติ๊กเกอร์ชีสเป็นหลัก

> **Sticker Sheet** ในโครงการนี้หมายถึงไฟล์รูปภาพหนึ่งไฟล์ที่ประกอบด้วยสติ๊กเกอร์หลายเฟรมอยู่ภายในภาพเดียวกัน

---

## MF-001 Split Sticker Sheet into Individual PNG Frames
ระบบต้องสามารถรับ Sticker Sheet แล้วแยกออกเป็นแต่ละเฟรม พร้อม export เป็นไฟล์ PNG แยกรายเฟรม

### Required behavior
- รองรับ layout แบบ configurable
- MVP baseline ต้องรองรับอย่างน้อย 2 rows × 5 columns = 10 frames
- รักษาลำดับเฟรมแบบ deterministic
- แต่ละ output ต้องเป็น PNG
- ห้าม overwrite source sheet

### Example output
```text
01.png
02.png
03.png
...
10.png
```

---

## MF-002 Remove Frame Border
หลัง split แล้ว ระบบต้องสามารถตรวจจับและลบเส้นขอบของแต่ละเฟรมได้

### Required behavior
- ทำงานแบบ per-frame
- รองรับ border หลายสี
- รองรับ border หลายความหนา
- รองรับความหนาแต่ละด้านไม่เท่ากัน
- รองรับ anti-aliased / resized border
- ห้ามใช้ global color deletion เป็นวิธีหลัก
- ใช้ position, continuity, geometry, connectivity และ confidence
- หาก border สัมผัส artwork และแยกไม่มั่นใจ ต้องส่ง `REVIEW`
- ห้าม silent destructive removal

---

## MF-003 Remove Frame Number / Sheet Metadata
ระบบต้องสามารถตรวจจับและนำหมายเลขประจำเฟรมที่เป็น metadata ของ sheet ออก เช่น `01`, `02`, `31`, `40`

### Required behavior
- การลบหมายเลขต้องทำหลัง split เป็น frame
- ต้องจำกัด detection ให้อยู่ใน configurable metadata region โดย default เช่นมุมซ้ายบน
- ต้องไม่ลบตัวเลขหรือข้อความที่เป็นส่วนหนึ่งของ sticker artwork
- การลบอัตโนมัติต้องอาศัย confidence
- กรณีไม่มั่นใจต้อง `REVIEW`
- ฟีเจอร์ต้องสามารถเปิด/ปิดได้ตาม profile

---

## MF-004 Conditional Background Removal
ระบบต้องตรวจสอบก่อนว่า frame มี meaningful transparency อยู่แล้วหรือไม่

### Path A — Already Transparent
หาก frame มี transparent background ที่ใช้งานได้อยู่แล้ว:
- ข้าม background-removal stage
- ห้าม segment/remove background ซ้ำโดยไม่จำเป็น
- รักษา alpha และ semi-transparent anti-aliased edges

### Path B — Opaque / Non-transparent Background
หาก frame ไม่มี meaningful transparency:
- วิเคราะห์ background
- สร้าง foreground mask
- remove background
- สร้าง RGBA output ที่ background เป็น transparent
- หาก segmentation confidence ต่ำ ต้อง `REVIEW`
- ห้ามลบ foreground แบบเดา

---

## MF-005 PNG Output Contract
ทุกเฟรมที่ผ่าน processing ต้องสามารถ export เป็น PNG ได้

### Minimum output properties
- PNG
- RGB/RGBA ตาม stage/profile
- alpha preserved/created เมื่อจำเป็น
- deterministic filename
- source traceability กลับไปยัง sheet และ frame index ได้

---

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
Per-frame Processing
        ├─ Detect & Remove Frame Border
        ├─ Detect & Remove Frame Number
        └─ Transparency Decision
              ├─ meaningful alpha exists
              │      ↓
              │    SKIP background removal
              │
              └─ opaque / no meaningful alpha
                     ↓
                 Remove Background
                     ↓
                 Create Transparent RGBA
        ↓
Content / Edge QA
        ↓
PNG Export
        ↓
Manifest / Findings
```

---

# Mandatory Safety Rules

1. **Source immutable by default** — ห้ามแก้หรือ overwrite source sheet
2. **No silent content loss** — ห้ามลบ artwork โดยไม่มี evidence/confidence
3. **Transparent means skip** — ถ้ามี meaningful transparency อยู่แล้ว ต้องไม่ remove background ซ้ำโดย default
4. **Metadata is not artwork** — border และ frame number เป็น removable metadata เมื่อยืนยันได้
5. **Ambiguous means REVIEW** — กรณีไม่แน่ใจให้คนตรวจ ไม่เดา
6. **Lossless-first** — ใช้ PNG/lossless flow และหลีกเลี่ยง repeated resize
7. **Traceable outputs** — ทุก PNG ต้องย้อนกลับได้ว่าเกิดจาก source sheet และ frame ใด

---

# MVP Acceptance Criteria
MVP ขั้นต่ำจะถือว่าผ่านเมื่อชุดทดสอบที่อนุมัติสามารถพิสูจน์ได้ว่า:

- 5×2 sheet ถูก split เป็น 10 PNG ถูกลำดับ
- border ถูกลบในกรณี high-confidence โดยไม่สูญเสีย artwork
- frame number ถูกลบโดยไม่กระทบ caption/artwork
- transparent frame ข้าม background removal
- opaque frame ถูกแปลงเป็น transparent background ได้ใน supported archetypes
- ambiguous border/number/background cases ถูกส่ง `REVIEW`
- source hash ไม่เปลี่ยนหลัง processing
- ไม่มี Critical defect ที่ทำให้เกิด silent content loss

---

# Scope Priority
ก่อนเพิ่มฟีเจอร์ขั้นสูง ระบบต้องทำ MF-001 ถึง MF-005 ให้ผ่าน acceptance criteria ก่อน

ฟีเจอร์ต่อไปนี้ไม่สามารถใช้แทน baseline นี้ได้:
- OCR ขั้นสูง
- AI semantic review
- duplicate caption detection
- deep Krita integration
- animated sticker support

Baseline นี้เป็น blocker สำหรับการประกาศ MVP พร้อมใช้งาน
