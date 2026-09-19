# MTKrita Pull Request — Document-Driven SSOT Checklist

## 1. SSOT Authorization
Identify the authoritative project documents that authorize this change.

- Requirement IDs / documents:
- ADR(s), if applicable:
- Pipeline / architecture references:
- GitHub issue:

> A PR must not introduce critical product behavior that is absent from or inconsistent with the SSOT.

## 2. Purpose and Scope
Describe what this PR changes and what is intentionally out of scope.

## 3. Mandatory Processing Contract Impact
Check all affected stages:

- [ ] Input inspection / fingerprint
- [ ] Layout detection / split
- [ ] Border detection / removal
- [ ] Frame-number / metadata removal
- [ ] Transparency routing
- [ ] Background removal
- [ ] Content analysis / smart fit
- [ ] QA / status routing
- [ ] PNG export / manifest
- [ ] UI / UX
- [ ] Packaging / Windows distribution
- [ ] No mandatory pipeline stage affected

## 4. Safety / Destructive-Risk Review
- [ ] Original source remains immutable by default
- [ ] No silent uncertain foreground/content deletion
- [ ] Ambiguous destructive cases route to `REVIEW`
- [ ] No default upscaling introduced
- [ ] Alpha / anti-aliased edges are preserved where applicable
- [ ] Not applicable (explain below)

Risk notes:

## 5. Provider / Orchestrator Boundary
If this change uses or modifies a processing provider:

- Provider/engine:
- Why this provider is selected:
- Is the sticker-domain decision kept in the Python orchestrator/domain layer? Yes / No / N/A
- Replacement/fallback behavior:

## 6. Verification Evidence
- [ ] Unit tests
- [ ] Component tests
- [ ] Golden-image / regression tests
- [ ] End-to-end test
- [ ] Windows test
- [ ] Manual visual review
- [ ] Static analysis / lint

Evidence / commands / CI run:

## 7. Traceability
List requirement → design/module → test mapping added or updated.

## 8. Documentation Synchronization
- [ ] Product requirement updated if behavior changed
- [ ] ADR updated if architecture changed
- [ ] Pipeline/architecture docs updated if process changed
- [ ] Test/traceability docs updated
- [ ] Changelog/release notes updated when required
- [ ] Documentation change not required (explain)

## 9. Gate Readiness
Target gate: G0 / G1 / G2 / G3 / G4

- [ ] Acceptance criteria met
- [ ] CI passes
- [ ] Known limitations documented
- [ ] No unresolved Critical defect introduced

## Reviewer Order
1. SSOT alignment
2. content/destructive safety
3. architecture/process fit
4. test and regression evidence
5. code quality
6. documentation synchronization
