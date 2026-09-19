# MTKrita Documentation Index

## Start Here — Developer Handoff
For a new development team, begin with:
1. `42_DEVELOPER_START_HERE.md` — onboarding entry point
2. `37_DEVELOPER_HANDOFF_PACKAGE.md` — handoff package and project rules
3. `50_ENGINEERING_HANDOFF_CHECKLIST.md` — readiness checklist before implementation
4. `51_REFERENCE_IMPLEMENTATION_BLUEPRINT.md` — reference package/module architecture
5. `41_M2_M3_IMPLEMENTATION_PLAN.md` — near-term implementation sequence
6. `38_IMPLEMENTATION_BACKLOG_AND_WORK_BREAKDOWN.md` — actionable work packages
7. `40_ACCEPTANCE_TEST_MATRIX.md` — acceptance evidence required
8. `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md` — verification corpus requirements
9. `39_CODING_STANDARDS_AND_REPO_CONVENTIONS.md` — coding/repository rules
10. `58_SSOT_COVERAGE_AUDIT.md` — documentation readiness audit

## SSOT Rule
MTKrita is a Document-Driven Project. When conflicts occur, follow the SSOT hierarchy defined in `25_DOCUMENT_DRIVEN_SSOT_OPERATING_MODEL.md`.

## Master Control
- `MASTER_PROJECT_CONTROL.md`
- `25_DOCUMENT_DRIVEN_SSOT_OPERATING_MODEL.md`
- `00_TEAM_GOVERNANCE.md`
- `26_PROJECT_TEAM_ROLES_AND_COMPETENCY_MODEL.md`
- `01_PROJECT_CHARTER.md`

## Requirements / Scope
- `02_PRODUCT_REQUIREMENTS.md`
- `24_MVP_MINIMUM_FUNCTIONAL_BASELINE.md`
- `23_SUPPORTED_INPUT_ARCHETYPES.md`
- `05_STICKER_SHEET_SPEC.md`
- `07_LINE_EXPORT_PROFILE.md`

## Architecture / Behavior / UML
- `03_SYSTEM_ARCHITECTURE.md`
- `DECISIONS.md`
- `27_END_TO_END_WORKFLOW_SPEC.md`
- `28_USE_CASE_SPECIFICATION.md`
- `29_UML_SYSTEM_MODEL.md`
- `30_SEQUENCE_DIAGRAMS.md`
- `31_STATE_MACHINE_SPEC.md`
- `32_DEPLOYMENT_AND_RUNTIME_ARCHITECTURE.md`
- `33_ERROR_RECOVERY_AND_IDEMPOTENCY_SPEC.md`
- `34_DATA_FLOW_AND_ARTIFACT_LIFECYCLE.md`
- `35_INTERFACE_AND_STAGE_CONTRACTS.md`
- `36_SECURITY_AND_FILE_SAFETY_MODEL.md`
- `44_PROVIDER_INTERFACE_ARCHITECTURE.md`
- `45_TOML_CONFIGURATION_SPEC.md`
- `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`
- `47_MAINBOARD_INTERNAL_COMMUNICATION_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `51_REFERENCE_IMPLEMENTATION_BLUEPRINT.md`

## Image Processing / Pipeline Engineering
- `04_IMAGE_PROCESSING_PIPELINE.md`
- `15_PROCESS_ENGINEERING_SPEC.md`
- `17_PIPELINE_ENGINEERING_GUIDE.md`
- `09_DATA_MODELS_AND_CONFIG.md`

## Quality / Verification / Traceability
- `06_QA_RULEBOOK.md`
- `10_TEST_PLAN.md`
- `13_QUALITY_MANAGEMENT_PLAN.md`
- `14_SOFTWARE_TEST_STRATEGY.md`
- `20_REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `22_DEFINITION_OF_DONE.md`
- `40_ACCEPTANCE_TEST_MATRIX.md`
- `52_TEST_DATA_AND_GOLDEN_CORPUS_SPEC.md`
- `54_RELEASE_AND_SIGNOFF_CHECKLIST.md`

## UX / Distribution / Audit
- `16_UI_UX_SPECIFICATION.md`
- `18_WINDOWS_DISTRIBUTION_PLAN.md`
- `19_AUDIT_AND_COMPLIANCE_PLAN.md`
- `11_RISK_REGISTER.md`
- `12_SOURCE_AND_LICENSE_NOTES.md`
- `58_SSOT_COVERAGE_AUDIT.md`

## Project Execution
- `08_MVP_SCOPE_AND_ROADMAP.md`
- `21_PROJECT_EXECUTION_PLAN.md`
- `38_IMPLEMENTATION_BACKLOG_AND_WORK_BREAKDOWN.md`
- `41_M2_M3_IMPLEMENTATION_PLAN.md`
- `57_TEAM_EXECUTION_PLAYBOOK.md`

## Engineering / Handoff / Operations
- `37_DEVELOPER_HANDOFF_PACKAGE.md`
- `39_CODING_STANDARDS_AND_REPO_CONVENTIONS.md`
- `42_DEVELOPER_START_HERE.md`
- `43_CURRENT_IMPLEMENTATION_STATUS_AND_KNOWN_GAPS.md`
- `50_ENGINEERING_HANDOFF_CHECKLIST.md`
- `53_OPERATIONAL_RUNBOOK.md`
- `55_PROJECT_GLOSSARY_AND_NAMING.md`
- `56_MAINTENANCE_AND_EXTENSION_GUIDE.md`

## Configuration
- `configs/line_static.toml` — canonical LINE static export profile
- TOML is the canonical human-maintained configuration format
- JSON is used for machine-generated manifests/evidence where appropriate

## History
- `CHANGELOG.md`

## Mandatory Engineering Principles
- Document first, implementation second, evidence always.
- If it is not captured in approved SSOT, it is not yet project truth.
- Prefer REVIEW over destructive guessing.
- Preserve original source and artwork safety over automation rate.
- Python is the orchestration/control plane.
- Depend on provider interfaces, not concrete engines.
- TOML is the canonical configuration format.
- All critical runtime paths go through PathManager/typed path references.
- Workers compute in isolation; shared-state commit is centralized through MainBoard/ResourceBroker.
- Batch and multi-worker execution must remain pauseable, resumable, recoverable and diagnosable.
- Structured logs, checkpoints and durable state are first-class architecture requirements.
