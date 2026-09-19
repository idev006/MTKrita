# MTKrita Testability and Automated Test Architecture

## Status
SSOT — Testability Architecture v1.0

## Purpose
กำหนดให้ MTKrita ถูกออกแบบเพื่อการทดสอบโดยอัตโนมัติตั้งแต่ระดับ architecture ไม่ใช่เพิ่ม testability ภายหลัง เพื่อให้ระบบเชื่อถือได้ เปลี่ยน provider ได้อย่างปลอดภัย และรองรับ CI/regression/fault-injection ได้ต่อเนื่อง

## Core Principle
> **Design for testability. Testability is an architectural property, not a testing afterthought.**

ทุก critical capability ต้องสามารถทดสอบแบบ headless, repeatable และ automation-friendly ได้โดยไม่ต้องพึ่ง UI หรือ manual interaction

## Mandatory Design Rules
1. dependency สำคัญต้อง inject/replace ได้
2. หลีกเลี่ยง hidden global mutable state
3. เวลา, UUID, filesystem, worker transport, JobStore, ResourceBroker และ provider boundary ต้องมี test seam เมื่อ behavior ขึ้นกับสิ่งเหล่านี้
4. business/domain logic ต้องแยกจาก UI และ concrete provider
5. stage contracts ต้องรองรับ fake/stub/mock implementation
6. deterministic stages ต้องให้ผล repeatable จาก input/config/version เดียวกัน
7. non-deterministic provider ถ้ามี ต้องประกาศ tolerance/seed/evidence policy
8. tests ต้องใช้ isolated temp workspace ผ่าน PathManager/test fixture
9. worker tests ห้ามใช้ shared mutable state แบบ production โดยไม่มี broker abstraction
10. critical failure/recovery behavior ต้องสามารถจำลองได้โดยไม่ต้อง crash OS จริง

## Test Layers
- Unit — pure/domain/helper logic
- Contract — provider/interface conformance
- Component — one stage + provider/fake dependencies
- Integration — orchestrator + stores/broker/providers
- E2E — sheet to final artifacts/manifest
- Golden regression — image/mask/geometry/reference evidence
- Fault injection — worker loss, stale lease, disk-full simulation, provider failure, interrupted commit
- Recovery — pause/resume/restart/checkpoint reconciliation
- UI smoke — presentation shell only; business correctness remains engine-tested
- Packaging/Windows smoke — installed runtime behavior

## Dependency Injection Targets
At minimum the application layer must be able to receive replaceable instances/adapters for:
- provider registry
- PathManager
- JobStore
- ResourceBroker
- EventBus
- Scheduler/WorkerManager boundary
- clock/time source where leases/timeouts are involved
- ID generator where reproducible tests need control
- LogSink/diagnostic sink

Production composition may construct concrete implementations at the application edge; core orchestration must not instantiate hidden infrastructure dependencies deep inside business logic.

## Provider Contract Testing
Every provider implementation must pass a shared contract suite covering:
- accepted input/output types
- structured result/evidence
- failure semantics
- source immutability
- determinism declaration
- timeout/cancellation behavior where applicable
- no direct shared-state mutation

The same contract suite should run against OpenCV/Pillow/future providers where the interface is shared.

## Automated CI Baseline
Pull requests affecting code must support headless automation. CI baseline:
1. Ruff/static checks
2. unit tests
3. component/contract tests
4. selected fast regression fixtures

Promotion gates add:
- golden corpus
- E2E
- recovery/fault-injection
- Windows smoke/package tests

## Fixture Strategy
Fixtures should be small, explicit and versioned where licensing/privacy permits. Test builders may generate synthetic images for deterministic edge cases. Real production-like golden corpus is maintained under the corpus specification and may be stored separately when required.

Required fixture families include:
- exact/resized 5x2 sheets
- transparent/opaque RGBA/RGB
- varied border color/width/topology
- metadata badge ambiguity
- dark foreground against dark background
- anti-aliased white outlines
- corrupt/unsupported files
- worker timeout/stale result scenarios

## Test Isolation
Every automated test must avoid interference with other tests:
- unique temporary job root
- private worker scratch
- no reliance on current working directory
- no writes to production config/output locations
- deterministic cleanup
- no dependence on test execution order

Parallel test execution must be safe for tests marked parallel-capable.

## Image Assertions
Do not rely only on whole-image byte equality where resampling/AA legitimately differs. Use appropriate assertions such as:
- exact frame count/order/geometry
- source hash unchanged
- alpha mask IoU
- foreground-loss threshold
- edge distance/halo metrics
- output dimensions/mode/profile
- artifact/manifest provenance

## Reliability/Fault Tests
Mandatory scenarios before production release include:
- worker terminates mid-task
- stale worker returns after lease expiry
- duplicate result submission
- interrupted artifact promotion
- corrupted checkpoint
- application restart during RUNNING
- pause then resume
- graceful stop then resume
- provider exception
- insufficient disk/resource rejection

Expected outcome: no false COMPLETED state, no stale overwrite, recoverable work resumes from valid checkpoint, diagnostic evidence remains available.

## Test-Friendly APIs
Prefer APIs that accept explicit inputs and return structured results. Avoid UI callbacks, environment lookups and direct filesystem access inside domain algorithms. Side effects should be pushed to infrastructure boundaries.

## Definition of Testable
A critical feature is not ready for implementation completion unless:
- behavior can be exercised headlessly
- dependencies can be substituted where needed
- success/failure/review states are observable
- evidence can be asserted
- automated tests exist at the appropriate layer

## Regression Rule
Every reproducible defect in a critical path should become a permanent automated regression case before the fix is considered complete.

## References
- `14_SOFTWARE_TEST_STRATEGY.md`
- `39_CODING_STANDARDS_AND_REPO_CONVENTIONS.md`
- `40_ACCEPTANCE_TEST_MATRIX.md`
- `52_GOLDEN_CORPUS_AND_TEST_DATA_SPEC.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `44_PROVIDER_INTERFACE_ARCHITECTURE.md`
