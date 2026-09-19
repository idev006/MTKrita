# Software Verification and Test Strategy

## Test Objective
พิสูจน์ว่า MTKrita ทำงานถูกต้อง ปลอดภัยต่อภาพต้นฉบับ ทำซ้ำได้ และไม่สร้างผลลัพธ์พร้อมขายเมื่อมีความเสี่ยงที่ยังไม่ได้รับการตรวจ

## Testability Principle
MTKrita must be designed for automated verification. Critical behavior must be testable headlessly without UI interaction. Infrastructure/provider dependencies should be injectable or replaceable where needed so unit, contract, integration, recovery and fault-injection tests can run deterministically.

Reference: `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`.

## Test Pyramid
1. Unit tests — algorithms and pure functions
2. Contract tests — provider/interface conformance
3. Component tests — detector/mask/fit/QA/export modules
4. Integration tests — orchestrator + MainBoard services/stores/broker/providers
5. Golden-image regression — pixel/alpha/geometry comparisons
6. End-to-end tests — full sheet to export package
7. Fault-injection/recovery tests — worker loss, stale lease, interrupted commit, restart/resume
8. Exploratory/adversarial tests — unusual layouts and hostile image cases
9. Installation tests — Windows 11 clean-machine scenarios

## Critical Test Families

### T-BORDER Adaptive Border Detection/Removal
Cover:
- 1/2/3/5/10/20 px borders
- different color on every frame
- gradient/anti-aliased border
- uneven side thickness
- partial border
- black border touching black hair/text
- border similar to foreground
- resized/blurred border
- no-border input

Assertions:
- no foreground loss beyond defined tolerance
- correct border-removal status and confidence
- ambiguous contacts become REVIEW, not PASS

### T-ALPHA Transparency
- true RGBA transparency
- RGBA fully opaque
- semi-transparent antialiasing
- alpha noise
- halos/fringing

### T-OPAQUE Background Separation
- white/solid/gradient/shadow/complex backgrounds
- similar foreground/background colors
- text close to background color

### T-GRID Split
- exact 5×2
- scaled sheet
- margin variation
- missing separator
- colored separators
- nonuniform separator thickness

### T-QUALITY Resampling
- confirm no unnecessary resize
- verify proportional scaling
- verify no default upscaling
- compare alpha edge before/after

### T-LINE Export
- PNG
- transparency
- even dimensions
- max canvas
- file size
- count and naming

### T-CONTRACT Provider Interfaces
- shared provider contract suite
- structured evidence/result
- failure semantics
- source immutability
- cancellation/timeout behavior where applicable
- no direct shared-state mutation

### T-RECOVERY Reliability
- worker termination during task
- stale/duplicate worker results
- interrupted final artifact commit
- corrupted checkpoint
- application restart during RUNNING
- pause/resume and stop/resume
- provider failure
- resource rejection such as insufficient disk

Assertions:
- no false COMPLETED state
- stale attempts rejected
- valid checkpoints resume correctly
- authoritative state remains consistent
- diagnostic evidence available

## Golden Corpus
Golden inputs and expected artifacts must be versioned separately from production source when licensing/privacy requires it. Each critical bug becomes a permanent regression case.

## Image Comparison
Use multiple metrics rather than only pixel equality:
- exact geometry assertions
- alpha-mask overlap / IoU
- foreground pixel loss count
- edge distance metrics
- perceptual similarity where resampling legitimately changes pixels

## Test Isolation
Automated tests must use isolated temporary workspaces, must not depend on current working directory or execution order, and must not write to production config/output locations. Parallel-capable tests must not share mutable state.

## CI Baseline
Pull-request CI runs at minimum:
- Ruff/static checks
- unit tests
- contract/component tests
- selected fast regression fixtures

Promotion gates add golden corpus, E2E, recovery/fault-injection and Windows/package verification as appropriate.

## Severity
- Critical: content loss, wrong frame, destructive source overwrite, false submission-ready result
- Major: invalid transparency/export, materially wrong fit, major border remnants
- Minor: cosmetic/report/UI issue without output corruption

## Exit Criteria
No unresolved Critical defects; Major defects require explicit release waiver. All critical-path regression tests must pass on supported Windows 11 build target. Critical features must also meet the testability definition in `59_TESTABILITY_AND_AUTOMATED_TEST_ARCHITECTURE.md`.
