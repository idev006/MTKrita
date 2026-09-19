# MTKrita Release and Sign-off Checklist

## Status
SSOT — Release Verification Baseline v1.0

## Purpose
กำหนดเงื่อนไขก่อนเลื่อน milestone/release และก่อนส่ง build ให้ผู้ใช้จริง

## Engineering Sign-off
- requirements/ADR/traceability synchronized
- CI/static checks pass
- unit/component/integration tests pass
- golden corpus passes for target milestone
- no unresolved Critical content-safety defect
- worker/resource/path/config invariants verified
- pause/resume/recovery scenarios verified where in scope

## Artifact Sign-off
- versioned build artifacts
- effective config/profile versions recorded
- manifest/evidence generated
- dependency/license inventory current
- Windows smoke test completed
- installer/portable package verified where applicable

## Quality Sign-off
- QA findings reviewed
- known limitations documented
- REVIEW behavior validated for ambiguous destructive cases
- output profile compliance verified

## Documentation Sign-off
- Master Control status updated
- Current Implementation Status updated
- CHANGELOG updated
- runbook and troubleshooting current
- breaking contract/config changes include migration note

## Gate Mapping
G2: implementation + automated verification readiness
G3: full regression/golden corpus + Windows smoke + documentation/license review
G4: final audit + reproducible release artifacts + distribution validation

## Release Decision Record
Every release candidate must record release version, commit SHA, config/profile versions, test evidence references, known limitations, approver roles and decision date.
