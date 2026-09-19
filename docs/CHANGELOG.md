# Documentation Changelog

## v0.3 — 2026-09-19
- Promoted supported input archetypes into main SSOT.
- Added formal end-to-end workflow specification including happy, alternate, review and failure flows.
- Added use case specification covering processing, review, resume/retry, export, transparent/opaque routing, border removal, metadata removal and 40-sticker batch flow.
- Added UML system model with context, component, class, provider and package dependency diagrams.
- Added sequence diagrams for main, transparent, opaque, review and recovery flows.
- Added job/frame/stage state machine specification.
- Added deployment and runtime architecture for Windows 11 standalone operation.
- Added error, recovery and idempotency specification.
- Added data flow and artifact lifecycle specification.
- Added interface and stage contracts for all critical pipeline stages.
- Added security and file safety model.
- Added project team roles and competency model.
- Strengthened Document-Driven SSOT rule: if important knowledge is not captured in approved SSOT, it is not yet project truth.
- Updated documentation index, Master Project Control and requirements traceability to reference the behavioral model suite.

## v0.2 — 2026-09-19
- Added project governance, virtual professional roles, RACI and quality gates.
- Expanded product requirements with adaptive per-frame border detection/removal.
- Added quality-preserving processing requirements: lossless-first, anti-aliased alpha preservation, minimal resize, no default upscaling.
- Added Quality Management Plan and comprehensive Software Test Strategy.
- Added Process Engineering Specification and Pipeline Engineering Guide.
- Added UI/UX Specification focused on exception-first review.
- Added Windows 11 standalone distribution plan.
- Added Audit/Compliance Plan and Requirements Traceability Matrix.
- Added Project Execution Plan and Definition of Done.
- Added documentation index and new ADRs for border removal, quality transforms, headless/Krita boundary and Windows distribution.
- Revalidated LINE static sticker export baseline against official guidelines dated 2026-09-19.

## v0.1 — 2026-09-19
- Initialized MTKrita project documentation.
- Defined automation-machine product vision.
- Defined transparent / opaque / auto processing modes.
- Defined MVP architecture and non-destructive safety principles.
- Defined QA states and auto-fix boundaries.
- Defined configurable LINE export profile.
- Defined roadmap, data models, test plan, risks and license notes.
- Recorded decision not to fork Krita during MVP.
