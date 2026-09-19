# UI/UX Specification

## UX Goal
ผู้ใช้ควรสามารถนำ Sticker Sheet เข้า → ตรวจผล → แก้เฉพาะ exception → export ได้ โดยไม่ต้องเข้าใจ OpenCV, alpha channels หรือ command line

## Primary Windows Workflow
1. Drag/drop one or more sheets
2. Select or auto-detect profile
3. Press `Analyze & Process`
4. View 10-frame status board
5. Review only `REVIEW/FAIL`
6. Export LINE package

## Main Screen

```text
┌──────────────────────────────────────────────┐
│ MTKrita                                     │
├──────────────────────────────────────────────┤
│ Drop Sticker Sheet Here                     │
│ Mode: AUTO     Profile: LINE Static         │
│ [Analyze & Process]                         │
├──────────────────────────────────────────────┤
│ 01 PASS   02 PASS   03 REVIEW   04 PASS ... │
│                                              │
│ Preview: Source | Mask | Processed | Final  │
│                                              │
│ Findings / Measurements / Actions           │
├──────────────────────────────────────────────┤
│ [Review Queue] [Export Passed] [Export All] │
└──────────────────────────────────────────────┘
```

## Progressive Disclosure
Default view shows only actionable status. Technical details such as alpha statistics, mask confidence and border thickness are expandable.

## Review Experience
For a REVIEW frame show:
- source preview
- detected border overlay
- foreground mask overlay
- intended removal overlay
- reason for review
- confidence
- recommended action

Controls:
- Accept proposed fix
- Keep border
- Force border removal (explicit risk confirmation)
- Open in external editor/Krita
- Re-run QA

## Status Semantics
Do not rely on color alone. Always display text/icon:
- PASS
- AUTO FIXED
- REVIEW
- FAIL

## Destructive Action UX
Any operation capable of deleting uncertain pixels must be explicit, previewable and reversible within the job. Original files are never overwritten by default.

## Accessibility
- keyboard-operable primary workflow
- readable scaling on Windows display scaling
- no color-only error meaning
- clear focus states
- Thai and English text must render correctly

## Performance UX
Long-running jobs must expose stage/progress and never appear frozen. Users should see which sheet/frame is being processed and can cancel between safe stage boundaries.

## Installation UX
Normal user experience target: download signed installer → Next → Install → launch. Portable ZIP should exist for testing/technical users.