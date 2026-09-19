# MTKrita Implementation Backlog and Work Breakdown

## Status
SSOT — Engineering Work Breakdown v1.0

## Purpose
แปลง requirement และ architecture ของ MTKrita เป็น work packages ที่ทีมพัฒนาสามารถดำเนินการได้โดยรักษา dependency, acceptance criteria และ quality gates

## Work Package Rules
ทุก work package ต้องมี:
- requirement mapping
- dependency
- implementation owner role
- acceptance criteria
- verification method
- target gate

---

## M2 — Transparent Processing Baseline

### WP-M2-01 Hybrid Sheet Geometry
**Requirement:** PR-003, PR-004, MF-001
**Owner:** Senior Software Engineer + Pipeline Engineer
**Depends on:** current `sheet.py`
**Work:**
- support non-perfectly-divisible resized sheets
- infer separator/cell boundaries conservatively
- retain exact deterministic path when geometry is exact
- produce boundary confidence/evidence
**Acceptance:**
- exact 5x2 case unchanged
- resized archetype splits into correct 10 frames
- ambiguous geometry returns REVIEW/failure reason rather than guessed destructive split
**Verification:** grid corpus + geometry edge cases
**Gate:** G2/G3

### WP-M2-02 Border Topology Hardening
**Requirement:** PR-012, MF-002
**Owner:** Process Engineer + Software Engineer
**Depends on:** border detector/remover
**Work:**
- test rounded/blurred/resized borders
- same-color artwork near/touching border
- unequal side widths
- partial borders
**Acceptance:**
- no known false-positive destructive removal in approved corpus
- ambiguous contact routes REVIEW
**Verification:** T-BORDER regression suite
**Gate:** G3

### WP-M2-03 Frame Metadata / Number Removal Hardening
**Requirement:** PR-017, MF-003
**Owner:** Software Engineer + Tester
**Depends on:** metadata detector
**Work:**
- configurable metadata zones
- multiple badge styles
- preserve numerical/text artwork outside metadata zone
- confidence thresholds configurable
**Acceptance:**
- supported frame badge removed
- artwork numbers preserved
- ambiguity refused
**Verification:** metadata corpus
**Gate:** G3

### WP-M2-04 Frame Pipeline Orchestrator
**Requirement:** PR-019
**Owner:** Pipeline Engineer
**Depends on:** WP-M2-01..03, router, content, fit, validation
**Work:**
- implement ordered per-frame stages
- stage result/evidence propagation
- PASS/AUTO_FIXED/REVIEW/FAIL mapping
- no GUI dependency
**Acceptance:**
- one extracted transparent frame traverses end-to-end deterministically
- stage failure produces structured finding
**Verification:** component + E2E test
**Gate:** G2

### WP-M2-05 Manifest / FrameResult Integration
**Requirement:** PR-009, PR-011, MF-005
**Owner:** Pipeline Engineer + Document/Audit roles
**Depends on:** frame orchestrator
**Work:**
- stage actions/findings
- source sheet/frame lineage
- engine/config versions
- output hash/path
**Acceptance:** every PNG traces to source frame and processing evidence
**Verification:** manifest schema tests
**Gate:** G2

### WP-M2-06 Transparent Corpus Gate
**Requirement:** M2 Exit Criteria
**Owner:** Tester + QA Auditor
**Depends on:** all M2 WPs
**Work:**
- approved golden corpus
- regression run
- source immutability verification
- CI evidence
**Acceptance:** no Critical defect; mandatory transparent behavior passes
**Gate:** G2/G3

---

## M3 — Opaque Processing Baseline

### WP-M3-01 Background Classification
**Requirement:** PR-006, PR-018, MF-004
**Owner:** Process Engineer + Software Engineer
**Work:** classify uniform / near-uniform / complex; estimate background evidence from safe edge samples
**Acceptance:** supported archetypes classified reproducibly; low confidence routes REVIEW

### WP-M3-02 Edge-Connected Background Provider
**Requirement:** PR-006
**Owner:** Software Engineer
**Work:** OpenCV-based connectivity/flood-fill provider; preserve disconnected dark foreground
**Acceptance:** black-background archetype removes background without deleting black hair/text

### WP-M3-03 Mask Refinement
**Requirement:** PR-013
**Owner:** Process Engineer
**Work:** anti-alias preservation, edge cleanup, halo detection/refinement
**Acceptance:** white outline and semitransparent edges retained within QA thresholds

### WP-M3-04 Advanced Fallback Provider Boundary
**Requirement:** ADR-013
**Owner:** Senior Software Engineer
**Work:** stable provider interface for GrabCut/optional future ML; no provider-specific domain rules
**Acceptance:** provider can be swapped without changing orchestrator contract

### WP-M3-05 Opaque Routing Orchestration
**Requirement:** PR-018, PR-019
**Owner:** Pipeline Engineer
**Work:** call background processing only for frames with no meaningful transparency
**Acceptance:** transparent frames bypass segmentation; opaque frames produce RGBA or REVIEW

### WP-M3-06 Mixed Corpus E2E Gate
**Owner:** Tester + QA Auditor
**Acceptance:** transparent+opaque mixed suite passes, no unsafe foreground deletion, traceability complete
**Gate:** G3

---

## M4 — Desktop Beta
- WP-M4-01 PySide6 shell
- WP-M4-02 drag/drop job creation
- WP-M4-03 frame status grid
- WP-M4-04 source/mask/final overlays
- WP-M4-05 REVIEW actions
- WP-M4-06 export flow
- WP-M4-07 Windows usability/smoke tests

## M5 — Production Automation
- batch 4 sheets / 40 stickers
- job resume/retry
- watch-folder candidate
- ZIP packaging
- performance/throughput evidence
- batch manifest/report

## M6 — Release Candidate
- installer + portable build
- clean Windows verification
- dependency/license inventory
- golden regression
- known limitations
- release audit

## M7 — Production Release
- G4 approval
- signed/published artifacts where applicable
- checksums
- release notes
- versioned SSOT snapshot

## Priority Order
1. content safety
2. mandatory MVP contract
3. SSOT/traceability
4. deterministic correctness
5. LINE compliance
6. usability
7. throughput
8. advanced AI
