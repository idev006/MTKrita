# Product Requirements

## Functional Requirements

### PR-001 Input
รองรับ PNG/JPEG และตรวจชนิดไฟล์จริง ไม่อาศัย extension อย่างเดียว

### PR-002 Processing Modes
- `AUTO`
- `TRANSPARENT`
- `OPAQUE`

`AUTO` เป็นค่า default

### PR-003 Sticker Sheet
MVP รองรับ 2 rows × 5 columns = 10 frames แต่โครงสร้างต้อง configurable เพื่อรองรับ layout อื่นในอนาคต

### PR-004 Frame Extraction
รองรับ fixed geometry, border/separator detection และ hybrid extraction

### PR-005 Transparency Analysis
ต้องแยกได้ระหว่าง:
- ไม่มี alpha channel
- มี alpha แต่ opaque ทั้งภาพ
- มี meaningful transparency
- มี semi-transparent antialiased edges

### PR-006 Opaque Background Processing
ต้องสามารถสร้าง foreground mask และ alpha output จาก input ที่ไม่มี transparency

### PR-007 Content Analysis
ต้องวัด content bounding box, connected components, edge contact, occupancy และ noise

### PR-008 Safe Auto-Fix
อนุญาตเฉพาะ operation ที่ไม่ทำลายเนื้อหา เช่น recenter, proportional scale, add transparent canvas และ remove confident noise

### PR-009 QA States
ทุก frame ต้องมีหนึ่งในสถานะ:
- `PASS`
- `AUTO_FIXED`
- `REVIEW`
- `FAIL`

พร้อมเหตุผล

### PR-010 Export
ต้อง export PNG, preserve alpha, ใช้ RGB/RGBA และ filename scheme ที่ deterministic

### PR-011 Reporting
ต้องมี JSON report สำหรับเครื่อง และ summary สำหรับคน

## Non-functional Requirements

- Reproducible: input + config + engine version เดียวกันต้องให้ผลลัพธ์เดิม
- Auditable: ทุก auto-fix ต้อง log
- Safe: ห้าม overwrite ต้นฉบับโดย default
- CPU-first MVP: ไม่บังคับ GPU
- Extensible: LINE-specific requirements ต้องแยกเป็น export profile
