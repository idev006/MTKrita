# MTKrita Coding Standards and Repository Conventions

## Status
SSOT — Engineering Conventions v1.1

## Purpose
กำหนดมาตรฐานร่วมสำหรับการพัฒนา MTKrita เพื่อให้ codebase maintainable, testable, headless-capable และสอดคล้องกับ document-driven architecture

## Language and Runtime
- Python >= 3.11
- typing required for public/core interfaces
- dataclass / enum / protocol-style contracts preferred for stable domain objects
- avoid hidden global mutable state

## Architectural Boundaries
### UI
May call application services. Must not own image-processing/business rules.

### Application / Orchestration
Owns workflow ordering, routing, stage transitions, confidence policy, evidence aggregation.

### Domain
Owns sticker-specific concepts, findings, states, contracts, decisions.

### Providers / Image Processing
Own lower-level algorithms and third-party engine integration. Must not redefine sticker-domain policy.

### Infrastructure
Filesystem, serialization, OS integration, packaging.

## Dependency Direction
```text
UI/CLI -> Application -> Domain -> Provider Interfaces
                         ^
                         |
               Provider Implementations
```
Domain must not depend on desktop UI.

## Module Guidelines
Prefer focused modules. Critical logic must be independently testable.
Expected direction:
```text
src/mtkrita/
  models.py
  pipeline/
  sheet/
  border/
  metadata/
  background/
  content/
  transform/
  qa/
  export/
  providers/
  infrastructure/
```
Incremental migration from current flat modules is allowed when justified; do not reorganize solely for aesthetics.

## Function / API Rules
- no mutable object construction in default arguments
- validate externally supplied dimensions/thresholds
- explicit failure/result types preferred over silent fallbacks
- destructive actions require confidence/evidence
- public stage operations should be deterministic unless documented otherwise
- avoid in-place mutation of source image objects when practical
- prefer explicit inputs/outputs over hidden environment/current-working-directory dependencies

## Testability Rules
Critical code must be designed so it can be tested headlessly and automatically.

Required practices:
- inject or replace provider/infrastructure dependencies where behavior depends on them
- provide test seams for PathManager, JobStore, ResourceBroker, EventBus, Scheduler/WorkerManager boundary, clock/time source, ID generation and LogSink where applicable
- do not instantiate hidden infrastructure dependencies deep inside domain/application logic
- provider implementations must be testable through shared contract suites
- side effects should be pushed toward infrastructure boundaries
- filesystem tests use isolated temporary workspaces
- tests must not depend on execution order or production directories
- reproducible critical defects require regression tests

Reference: `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`.

## Image Safety Rules
- source files immutable
- no JPEG intermediate in core pipeline
- preserve RGBA/semitransparent pixels
- no default upscale
- avoid repeated resampling
- no global color deletion as generic border/background/metadata solution

## Error Handling
- expected ambiguity -> structured REVIEW finding
- invalid input -> structured FAIL/error
- programmer invariant violation -> exception + test
- do not catch broad exceptions merely to continue silently

## Logging and Evidence
Critical stage logs/evidence should include where relevant:
- job/frame id
- stage id
- provider/engine version
- config values/hash
- confidence/measurements
- action taken
- output hash/path

Never log file contents or secrets unnecessarily.

## Testing
Every defect fix requires a regression test when reproducible.
Critical algorithm changes require:
- unit/component tests
- contract tests when provider/interface behavior changes
- edge case tests
- corpus/E2E evidence when destructive behavior can change
- fault/recovery tests when state, worker, lease, checkpoint or commit behavior changes

## Static Quality
CI must run at minimum:
- Ruff
- pytest
Additional mypy/type checks may be promoted to required gate when baseline is stable.

## Git / PR Rules
- one coherent purpose per PR
- reference SSOT requirement/ADR
- describe destructive risk
- include tests/evidence
- no direct behavior change on `main` without traceable documentation synchronization
- critical changes use feature branches and PR gate

## Naming
- requirements: `PR-###`
- mandatory functions: `MF-###`
- use cases: `UC-###`
- work packages: `WP-M#-##`
- ADR: `ADR-###`
- stages: stable human-readable stage ids in evidence

## Configuration
Behavioral thresholds that may need tuning should be config-driven rather than duplicated literals across modules. Defaults must be documented and tested.

## Review Checklist
A reviewer must verify:
1. SSOT authorization
2. architecture layer correctness
3. no silent destructive behavior
4. tests match acceptance criteria
5. code remains headless/testable where required
6. dependencies are substitutable at approved seams
7. source immutability
8. traceability/evidence
9. documentation synchronization
