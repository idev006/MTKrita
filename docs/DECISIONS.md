# Architecture Decision Records

## ADR-001 — Build an Automation Engine, Not a General Image Editor
**Status:** Accepted

Project value is sticker-specific automation. Existing editors already solve general canvas/layer/manual-editing problems.

## ADR-002 — Do Not Fork Krita for MVP
**Status:** Accepted

Build an independent engine first to avoid upstream merge and maintenance complexity.

## ADR-003 — Deterministic Before AI
**Status:** Accepted

Use rule-based image processing whenever the problem can be solved reliably without AI.

## ADR-004 — Three Input Modes
**Status:** Accepted

- AUTO
- TRANSPARENT
- OPAQUE

## ADR-005 — Conservative Automation
**Status:** Accepted

If uncertain, return `REVIEW` rather than perform destructive correction.

## ADR-006 — Config-Driven Export Profiles
**Status:** Accepted

LINE-specific constraints must not be scattered through core source code.

## ADR-007 — 512×512 Is a Working Frame
**Status:** Accepted

The source production sheet may use 512×512 cells. Final upload assets are generated through an export profile.
