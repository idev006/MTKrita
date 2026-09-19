# Project Execution Plan

## Objective
Deliver MTKrita from documentation baseline to production-quality Windows 11 application through controlled increments with measurable exit criteria.

## Mandatory MVP Processing Contract
ก่อนประกาศ MVP พร้อมใช้งาน ระบบต้องทำ workflow ขั้นต่ำนี้ได้ครบ:

```text
Sticker Sheet Input
        ↓
Split Frames
        ↓
Remove Frame Border
        ↓
Remove Frame Number / Sheet Metadata
        ↓
Check Transparency
        ├─ meaningful transparency exists → SKIP background removal
        └─ opaque / no meaningful alpha → Remove Background → Transparent RGBA
        ↓
PNG Export
        ↓
QA / Manifest
```

เอกสารควบคุมหลัก: `24_MVP_MINIMUM_FUNCTIONAL_BASELINE.md`

## Workstreams

### WS1 Product & Governance — PM / Project Director
- scope baseline
- risks/decisions
- acceptance gates
- release governance

### WS2 Core Architecture — Senior Software Engineer
- repository structure
- typed data/config models
- adapters/interfaces
- error and logging model

### WS3 Image Process — Process + Pipeline Engineers
- sheet analysis/split
- adaptive border detection/removal
- frame-number / sheet-metadata removal
- transparency routing
- transparent pipeline
- opaque background-removal pipeline
- content analysis/smart fit
- PNG export

### WS4 Quality & Verification — Tester + QA Auditor
- unit/component/E2E framework
- golden corpus
- regression and release evidence
- mandatory baseline acceptance evidence for MF-001 through MF-005

### WS5 Desktop UX — UI/UX + Software Engineer
- Windows UI
- preview overlays
- exception review queue
- export flow

### WS6 Distribution — Pipeline Engineer + Tester
- standalone build
- portable build
- installer
- clean-machine verification

### WS7 Documentation & Audit — Document Writer + Auditors
- SSOT maintenance
- traceability
- license/dependency inventory
- release checklist/evidence

## Milestones

### M0 — Documentation Baseline
Exit: governance, architecture, processing, QA, testing, UX, release and traceability baseline committed.

### M1 — Core Skeleton
Exit: CLI runs; config models load; job/frame manifest created; automated test harness active.

### M2 — Transparent Processing Baseline
Exit:
- 5×2 split works and exports deterministic PNG frames
- adaptive border removal works on supported high-confidence cases
- frame-number removal baseline exists and is profile-controlled
- meaningful transparency is detected correctly
- already-transparent frames explicitly skip background removal
- alpha/content + smart fit + LINE PNG validation pass transparent corpus

### M3 — Opaque Processing Baseline
Exit:
- opaque/non-transparent frames route automatically into background-removal pipeline
- supported opaque archetypes are converted to transparent RGBA without unsafe foreground deletion
- black/colored background removal does not use unsafe global color deletion
- ambiguous cases route to REVIEW
- end-to-end mandatory workflow MF-001 → MF-005 passes approved corpus

### M4 — Desktop Beta
Exit: drag/drop, status grid, overlays, review actions and export work on Windows 11.

### M5 — Production Automation
Exit: 4 sheets / 40 stickers batch, reports, ZIP packaging, recovery/idempotency and performance verified.

### M6 — v1.0 Release Candidate
Exit: all G3 evidence complete; mandatory MVP baseline passes; no Critical defects; Windows installer/portable candidates verified.

### M7 — v1.0 Release
Exit: G4 approval, release artifacts/checksums/licenses/known limitations published.

## Priority Order
Content safety > mandatory MVP contract > deterministic correctness > LINE compliance > usability > throughput > advanced AI features.

## Scope Control
No optional feature may delay or replace the mandatory MVP capabilities MF-001 through MF-005. OCR, AI semantic review, duplicate detection, animated sticker support and deeper Krita integration remain post-core unless required to resolve an accepted defect/quality target.

## Decision Cadence
Architecture/process changes: ADR. Requirement changes: requirement + traceability + test review. Release changes: changelog + release checklist.
