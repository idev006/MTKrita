# MTKrita Document-Driven SSOT Operating Model

## Status
SSOT — Operating Model v1.2

## Purpose
กำหนดวิธีทำงานของโครงการ MTKrita ให้เป็น **Document-Driven Project** ที่มี **Single Source of Truth (SSOT)** ชัดเจน โดยเอกสารที่ได้รับการอนุมัติเป็นตัวกำหนดสิ่งที่ต้องสร้าง วิธีตรวจรับ และเงื่อนไขที่ถือว่างานเสร็จ ไม่ใช่ให้โค้ดหรือบทสนทนาเป็นตัวสร้าง requirement ย้อนหลัง

## 1. Core Philosophy

> **Document first, implementation second, evidence always.**

> **If it is not captured in the approved SSOT, it is not yet project truth.**

ลำดับมาตรฐาน:

```text
Intent / Owner Decision
  ↓
SSOT Requirement
  ↓
Architecture / ADR / Workflow / Use Case / Stage Contract
  ↓
Acceptance Criteria
  ↓
Traceability Mapping
  ↓
Implementation
  ↓
Verification
  ↓
Evidence
  ↓
Gate Approval
  ↓
Release
```

## 2. SSOT Hierarchy
หากข้อมูลขัดกัน ให้ใช้ลำดับอำนาจดังนี้:

1. `MASTER_PROJECT_CONTROL.md`
2. `00_TEAM_GOVERNANCE.md`
3. `26_PROJECT_TEAM_ROLES_AND_COMPETENCY_MODEL.md`
4. `01_PROJECT_CHARTER.md`
5. `02_PRODUCT_REQUIREMENTS.md`
6. `24_MVP_MINIMUM_FUNCTIONAL_BASELINE.md`
7. `DECISIONS.md`
8. Architecture / Workflow / Use Case / UML / Sequence / State / Stage Contract documents
9. QA / Test / Traceability documents
10. GitHub Issues / PRs
11. Source code

Source code must not silently redefine upstream requirements.

## 3. Required Change Flow
Any change affecting behavior, quality, processing order, destructive operations, supported input, output contract, runtime/provider architecture or release condition must follow:

```text
Change request
  ↓
Impact analysis
  ↓
Update SSOT
  ↓
ADR if architectural
  ↓
Update workflow/use case/contracts if affected
  ↓
Update traceability + acceptance tests
  ↓
Implement
  ↓
Verify
  ↓
Record evidence
```

Emergency fixes may synchronize docs and code in the same PR, but cannot close until evidence and SSOT are aligned.

## 4. Python Orchestrator Principle
MTKrita uses **Python as the orchestration/control plane**.

Python owns domain routing, stage order, provider selection, confidence policy, state transitions, manifest/evidence, and shared workflow for GUI/CLI/batch/future API.

Python is not required to reimplement every image-processing algorithm. Proven open-source providers/libraries may implement lower-level operations.

## 5. Engine-Agnostic Rule
The orchestrator owns **when and why** a capability is used; providers own **how** a low-level operation is executed. Provider-specific APIs should remain behind stable contracts where practical.

## 6. Mandatory Behavioral Documentation
Critical behavior must be represented in the appropriate SSOT documents:
- workflow: `27_END_TO_END_WORKFLOW_SPEC.md`
- use cases: `28_USE_CASE_SPECIFICATION.md`
- UML/system model: `29_UML_SYSTEM_MODEL.md`
- interaction order: `30_SEQUENCE_DIAGRAMS.md`
- lifecycle/state: `31_STATE_MACHINE_SPEC.md`
- deployment/runtime: `32_DEPLOYMENT_AND_RUNTIME_ARCHITECTURE.md`
- recovery/idempotency: `33_ERROR_RECOVERY_AND_IDEMPOTENCY_SPEC.md`
- artifact/data flow: `34_DATA_FLOW_AND_ARTIFACT_LIFECYCLE.md`
- interface contracts: `35_INTERFACE_AND_STAGE_CONTRACTS.md`
- security/file safety: `36_SECURITY_AND_FILE_SAFETY_MODEL.md`

## 7. Definition of Ready
A critical feature is ready for implementation only when requirement, measurable behavior, destructive-risk policy, acceptance tests, responsible owner, and required traceability/design artifacts exist.

## 8. Definition of Done
A feature is complete only when implementation, tests, regression evidence, source-safety requirements, traceability, documentation synchronization and relevant quality gate all pass.

## 9. GitHub Execution Rule
Issues and PRs are execution records, not authoritative product intent. Each critical implementation PR must reference its controlling SSOT requirement/design/test documents.

Review order:
1. SSOT alignment
2. safety/destructive-risk review
3. architecture/process fit
4. tests/regression evidence
5. code quality
6. documentation synchronization

## 10. Team Knowledge Rule
Project-relevant knowledge must not remain only in chat, meeting notes or individual understanding. Important decisions, requirements, assumptions, constraints, team responsibilities, workflows, diagrams, risks, findings and release evidence must be promoted into approved SSOT documents.

## 11. Chat Communication Rule
Chat is a coordination channel, not the project record.

Default chat behavior:
- communicate briefly and concisely;
- show only the decision, high-level rationale, current status and next action unless detailed explanation is requested;
- avoid duplicating long technical specifications already stored in project documents;
- whenever a conversation introduces or changes project-relevant behavior, architecture, requirement, constraint, workflow, interface, configuration policy, risk, test rule or operational decision, update the appropriate SSOT document in the same work cycle.

The authoritative detail shall live in the repository documents, not only in the chat transcript.

## 12. Project Principle Summary

> **MTKrita is a document-driven, SSOT-controlled, Python-orchestrated, engine-agnostic sticker-production automation system with measurable gates and auditable evidence.**
