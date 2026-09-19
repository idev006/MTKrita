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
รองรับ fixed geometry, border/separator detection และ hybrid extraction และต้องสามารถ export frame ที่แยกแล้วเป็น PNG รายเฟรมตามลำดับ deterministic

### PR-005 Transparency Analysis
ต้องแยกได้ระหว่าง:
- ไม่มี alpha channel
- มี alpha แต่ opaque ทั้งภาพ
- มี meaningful transparency
- มี semi-transparent antialiased edges

### PR-006 Opaque Background Processing
ต้องสามารถสร้าง foreground mask และ alpha output จาก input ที่ไม่มี transparency โดยกรณี confidence ต่ำต้องส่ง REVIEW แทนการลบ foreground แบบเดา

### PR-007 Content Analysis
ต้องวัด content bounding box, connected components, edge contact, occupancy และ noise

### PR-008 Safe Auto-Fix
อนุญาตเฉพาะ operation ที่ไม่ทำลายเนื้อหา เช่น recenter, proportional scale, add transparent canvas และ remove high-confidence noise

### PR-009 QA States
ทุก frame ต้องมีหนึ่งในสถานะ `PASS`, `AUTO_FIXED`, `REVIEW`, `FAIL` พร้อมเหตุผลและ measurements ที่เกี่ยวข้อง

### PR-010 Export
ต้อง export PNG, preserve alpha, ใช้ RGB/RGBA และ deterministic filename scheme ตาม export profile

### PR-011 Reporting
ต้องมี machine-readable report และ human-readable summary พร้อม actions/findings ต่อ frame

### PR-012 Adaptive Border Detection and Removal
หลัง split เป็น frame ระบบต้องตรวจ border รายเฟรม และรองรับ border ที่มี:
- สีต่างกัน
- ความหนาต่างกัน
- ความหนาแต่ละด้านไม่เท่ากัน
- anti-alias / blur จากการ resize
- border ไม่ครบทุกด้าน

การตัดสิน border ต้องใช้ position/continuity/geometry/connectivity และ confidence ไม่ใช่ลบด้วยสีเพียงอย่างเดียว หาก border แตะ artwork และแยกไม่มั่นใจ ต้อง `REVIEW` โดยห้าม silent destructive removal

### PR-013 Quality-Preserving Image Processing
- lossless-first internal flow
- หลีกเลี่ยง repeated resize
- preserve aspect ratio
- preserve semi-transparent anti-aliased edges
- no default upscaling
- final resize เมื่อจำเป็นควรเกิดเพียงครั้งเดียวเท่าที่เป็นไปได้
- ห้าม recompress เป็น JPEG ระหว่าง processing โดยไม่มีเหตุผลที่ระบุ

### PR-014 Original Preservation
ต้นฉบับต้อง immutable โดย default และ output ต้องเขียนไปยัง job/output location แยกต่างหาก

### PR-015 Windows 11 Distribution
ผู้ใช้ปลายทางต้องสามารถติดตั้ง/ใช้งาน core application บน Windows 11 x64 โดยไม่ต้องติดตั้ง Python/OpenCV/developer toolchain ด้วยตนเอง ต้องมี standalone installer เป็นเป้าหมาย production และ portable build สำหรับ test/technical use

### PR-016 Exception-First Review UX
UI ต้องทำให้ผู้ใช้ตรวจ `REVIEW/FAIL` เป็นหลัก และให้ preview source/mask/border-removal/final output ก่อนอนุมัติ operation ที่มีความเสี่ยง

### PR-017 Frame Number / Sheet Metadata Removal
หลัง split เป็น frame ระบบต้องสามารถตรวจและลบหมายเลขประจำเฟรมที่เป็น metadata ของ sheet เช่น `01`, `02`, `31`, `40` ได้

ข้อกำหนด:
- detection region ต้อง configurable และโดย default จำกัดอยู่บริเวณ metadata zone เช่นมุมซ้ายบน
- ห้ามลบตัวเลข/ข้อความที่เป็นส่วนหนึ่งของ sticker artwork
- automatic removal ต้องใช้ confidence threshold
- ambiguity ต้องเป็น `REVIEW`
- feature ต้องเปิด/ปิดได้ตาม profile

### PR-018 Conditional Background Removal Routing
ระบบต้องตรวจ meaningful transparency ก่อน background processing เสมอ

- หาก frame มี meaningful transparent background อยู่แล้ว ให้ **SKIP background removal** โดย default และรักษา alpha/anti-aliased edges เดิม
- หาก frame ไม่มี meaningful transparency หรือ fully opaque ให้ route เข้าสู่ opaque background-removal pipeline
- ห้ามทำ segmentation ซ้ำบน transparent frame โดยไม่มี explicit reason/config
- routing decision ต้องถูกบันทึกใน manifest/processing log

### PR-019 Mandatory MVP Processing Contract
ก่อนประกาศ MVP พร้อมใช้งาน ระบบต้องทำ workflow ขั้นต่ำนี้ได้ครบ:

`Sticker Sheet → Split Frames → Remove Border → Remove Frame Number → Conditional Background Removal → PNG Export`

รายละเอียด acceptance และ safety baseline ให้อ้างอิง `24_MVP_MINIMUM_FUNCTIONAL_BASELINE.md` ซึ่งเป็น release blocker สำหรับ MVP

## Non-functional Requirements

### NFR-001 Reproducibility
Input + config + engine version เดียวกันต้องให้ผลลัพธ์ equivalent/deterministic สำหรับ deterministic stages

### NFR-002 Auditability
ทุก auto-fix และ processing strategy ต้อง log ได้ว่าทำอะไร เพราะเหตุใด และใช้ค่าใด

### NFR-003 Safety
ห้าม overwrite ต้นฉบับโดย default และห้าม silently delete uncertain foreground

### NFR-004 CPU-first MVP
MVP ต้องไม่บังคับ GPU

### NFR-005 Extensibility
LINE-specific requirements ต้องแยกเป็น export profile และ third-party engines ต้องถูกซ่อนหลัง adapters

### NFR-006 Maintainability
Critical image-processing logic ต้องแยก module, testable และไม่ผูกกับ UI

### NFR-007 Portability
Core processing ต้อง headless-capable; Krita เป็น optional integration ไม่ใช่ runtime requirement ของ core MVP

### NFR-008 Quality Evidence
Critical release behavior ต้องมี objective verification evidence และ requirement-to-test traceability
