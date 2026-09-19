# MTKrita Team Execution Playbook

## Status
SSOT — Team Execution Baseline v1.0

## Purpose
กำหนดวิธีที่ทีมพัฒนาหลายบทบาททำงานร่วมกันให้เร็วโดยไม่เสีย traceability, safety หรือ architectural consistency

## Work Intake
1. select WBS item / issue
2. identify controlling SSOT requirement/ADR
3. identify interfaces/stages/resources affected
4. identify acceptance tests and risks
5. assign owner/reviewer roles

## Implementation Cycle
Design delta -> SSOT update if needed -> implementation -> tests -> evidence -> review -> merge.

## Parallel Team Rules
- teams may work in parallel when contracts are stable
- shared contract changes require coordination before parallel implementation continues
- provider work can proceed independently behind stable interfaces
- worker/runtime work must respect MainBoard/ResourceBroker contracts
- QA creates acceptance/regression cases concurrently, not after coding finishes

## Review Responsibilities
- Software Engineer: architecture/code correctness
- Process/Pipeline Engineer: stage/process integrity
- Tester: objective verification
- QA Auditor: safety/gate evidence
- Document Writer: SSOT synchronization
- PM/Project Director: scope/change/gate control

## Daily/Iteration Status Format
- Done
- In Progress
- Blocked/Risk
- Decision Needed
- Evidence/PR references

## Escalation
Critical risks: source loss, silent foreground deletion, corrupted shared state, unrecoverable job, contract drift, or security/path violation. Stop affected release path until resolved/documented.

## Completion Rule
No task is complete until code, tests, evidence and affected SSOT are synchronized.
