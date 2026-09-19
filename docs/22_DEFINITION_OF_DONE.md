# Definition of Done

A feature is not Done merely because it runs. It is Done only when all applicable items below are satisfied.

## Requirement
- requirement/acceptance criteria exist or are updated
- scope and failure behavior are clear
- traceability is updated for critical behavior

## Design
- module/interface responsibility is clear
- destructive-risk analysis completed
- architecture decision recorded if system-wide

## Implementation
- code is readable and isolated from UI where domain logic applies
- no unexplained production hard-coding
- source input remains immutable by default
- logs/findings are sufficient for diagnosis

## Verification
- unit/component tests pass
- relevant golden-image tests pass
- critical edge cases included
- fixed defects have regression coverage
- no unresolved Critical defect

## Image Quality
- no unexplained foreground loss
- alpha/antialiased edges satisfy quality checks
- no unnecessary repeated resize
- border removal does not remove ambiguous artwork
- low-confidence cases become REVIEW

## UX
- user-facing errors are actionable
- risky operation is previewable/explicit
- UI does not depend on color alone for status

## Documentation
- affected requirements/process/config/ADR docs updated
- changelog updated for release-impacting changes

## Release-impacting Feature
Additionally requires Windows 11 smoke test, dependency/license review, build artifact integrity checks and release evidence.