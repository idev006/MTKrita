# Project Execution Plan

## Objective
Deliver MTKrita from documentation baseline to production-quality Windows 11 application through controlled increments with measurable exit criteria.

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
- transparent pipeline
- opaque pipeline
- content analysis/smart fit
- export

### WS4 Quality & Verification — Tester + QA Auditor
- unit/component/E2E framework
- golden corpus
- regression and release evidence

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

### M2 — Transparent MVP
Exit: 5×2 split + adaptive border + alpha/content + smart fit + LINE PNG export passes transparent corpus.

### M3 — Opaque MVP
Exit: deterministic background strategies and REVIEW fallback pass opaque corpus without unsafe foreground deletion.

### M4 — Desktop Beta
Exit: drag/drop, status grid, overlays, review actions and export work on Windows 11.

### M5 — Production Automation
Exit: 4 sheets / 40 stickers batch, reports, ZIP packaging, recovery/idempotency and performance verified.

### M6 — v1.0 Release Candidate
Exit: all G3 evidence complete; no Critical defects; Windows installer/portable candidates verified.

### M7 — v1.0 Release
Exit: G4 approval, release artifacts/checksums/licenses/known limitations published.

## Priority Order
Content safety > deterministic correctness > LINE compliance > usability > throughput > advanced AI features.

## Scope Control
New features may not delay critical processing correctness. OCR, AI segmentation, duplicate detection and deeper Krita integration remain post-core unless required to meet an accepted defect/quality target.

## Decision Cadence
Architecture/process changes: ADR. Requirement changes: requirement + traceability + test review. Release changes: changelog + release checklist.
