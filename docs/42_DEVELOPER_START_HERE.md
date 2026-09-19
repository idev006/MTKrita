# MTKrita Developer Start Here

## Status
SSOT — Developer Onboarding Entry Point v1.0

## Who Should Read This
Any developer, tester, reviewer, or technical contributor joining MTKrita.

## 10-Minute Orientation
MTKrita is a document-driven, SSOT-controlled, Python-orchestrated sticker production automation system for Windows 11.

The mandatory MVP converts a multi-frame Sticker Sheet into individual PNG sticker assets while safely handling:
- frame splitting
- frame-border removal
- frame-number/metadata removal
- conditional background removal
- transparent PNG output
- QA and traceability

## First Principles
1. Documentation governs implementation.
2. Python orchestrates; providers execute low-level image operations.
3. Content safety outranks automation rate.
4. If destructive ambiguity remains, return REVIEW.
5. Source files are immutable.
6. Critical work is not done until evidence exists.

## Read These First
1. `MASTER_PROJECT_CONTROL.md`
2. `37_DEVELOPER_HANDOFF_PACKAGE.md`
3. `24_MVP_MINIMUM_FUNCTIONAL_BASELINE.md`
4. `41_M2_M3_IMPLEMENTATION_PLAN.md`
5. `38_IMPLEMENTATION_BACKLOG_AND_WORK_BREAKDOWN.md`
6. `40_ACCEPTANCE_TEST_MATRIX.md`
7. `35_INTERFACE_AND_STAGE_CONTRACTS.md`
8. `39_CODING_STANDARDS_AND_REPO_CONVENTIONS.md`

## Repository Quick Map
```text
.github/                CI and PR workflow
configs/                versioned runtime/export configuration
docs/                   SSOT
src/mtkrita/            core implementation
tests/                  automated tests
pyproject.toml           package/dependencies/tooling
```

## Development Environment
Target development runtime: Python 3.11+.
Typical local setup:
```text
python -m venv .venv
activate environment
python -m pip install -e ".[dev]"
ruff check src tests
pytest
```
Exact shell activation differs by OS/shell.

## Current Work
M2 is active. Do not start unrelated feature expansion before checking `38_IMPLEMENTATION_BACKLOG_AND_WORK_BREAKDOWN.md` and open GitHub issues/PRs.

Current active capability path:
```text
split -> border -> metadata -> transparency route -> content/fit -> QA -> PNG/manifest
```
M3 adds opaque-background removal after the routing decision.

## Before You Code
Confirm:
- requirement id exists
- work package exists or is approved
- stage contract exists
- test/acceptance id exists
- destructive behavior is defined
- branch/PR scope is coherent

If one of these is missing for a critical behavior, update SSOT first.

## Before You Open a PR
Run:
- Ruff
- pytest
- relevant corpus/component tests
Then complete `.github/pull_request_template.md` with:
- SSOT references
- WP/requirement ids
- safety impact
- acceptance evidence
- docs synchronized

## Before Merge
Reviewer confirms:
- no SSOT contradiction
- no silent destructive fallback
- tests prove intended behavior
- traceability/evidence updated
- CI green

## Where to Ask Questions
Questions should be resolved against the SSOT first. If a new decision is needed, record it in the appropriate requirement/ADR/process document instead of leaving the decision only in chat or PR comments.
