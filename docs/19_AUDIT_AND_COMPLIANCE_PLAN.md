# Audit and Compliance Plan

## Purpose
Define evidence and review controls for requirements, design, implementation, testing, release, and third-party dependencies.

## Audit Areas

### Requirements
- Each blocking behavior has a requirement identifier.
- Requirements have testable acceptance criteria.
- LINE-specific constraints are versioned in an export profile.

### Design
- Significant architecture changes are recorded as ADRs.
- Potentially destructive operations have explicit safety controls.
- Source input remains immutable by default.

### Implementation
- Critical processing modules require review before release.
- Production thresholds must be configurable or documented with rationale.
- Dependency versions must be controlled.

### Verification
- Requirements map to verification evidence.
- Critical and major defects add permanent regression cases.
- Release-candidate test evidence is retained.

### Release
- Release version maps to an exact source commit/tag.
- Build artifacts include checksums and release notes.
- Windows 11 installation smoke tests pass.
- Current official LINE guidelines are rechecked before a profile is declared submission-ready.

### Third-party Components
Maintain a dependency/license inventory. Krita integration and redistribution must follow its applicable GPL obligations; OpenCV version/license and all other dependencies must be reviewed before public distribution.

## Minimum Release Evidence
- source commit/tag
- requirements baseline
- ADRs
- automated and manual test report
- golden corpus version
- dependency inventory
- build record
- artifact hashes
- release checklist

## Findings
Classify audit findings as Critical, Major, or Minor. Critical findings block release. Major findings require correction or explicit documented risk acceptance.

## Review Independence
The QA/Audit perspective must verify evidence independently from the implementation rationale, even when project responsibilities are represented by virtual roles.