# QA Rulebook

## QA States
- `PASS` — ผ่านทุก blocking rule
- `AUTO_FIXED` — พบปัญหาและแก้แบบ non-destructive แล้ว re-QA ผ่าน
- `REVIEW` — ต้องใช้มนุษย์ตัดสินใจหรือ confidence ต่ำ
- `FAIL` — ผิดข้อกำหนดสำคัญและ safe automation แก้ไม่ได้

## QA Categories

### File Integrity
- readable image
- valid dimensions
- expected output format
- RGB/RGBA

### Transparency
- meaningful alpha when required
- no accidental opaque background
- no unexpected halo

### Content Bounds
- artwork not clipped
- no unsafe edge contact
- caption/content preserved

### Occupancy
- content not too small
- content not oversized
- occupancy within configurable target range

### Noise
- isolated alpha pixels
- leftover sheet borders
- background remnants

### Frame Consistency
- correct frame count
- correct order
- no accidental blank frame

### Export Profile
- dimensions compliant
- even dimensions when required
- format and file-size limits compliant

## Severity
`INFO` / `WARNING` / `REVIEW` / `BLOCKER`

## Auto-Fix Allowed
- add transparent canvas
- translate/recenter
- proportional scale down
- remove highly confident isolated noise
- normalize output metadata/dimensions

## Auto-Fix Forbidden
- delete uncertain foreground
- hallucinate missing artwork
- rewrite captions
- alter faces
- crop away visible content
