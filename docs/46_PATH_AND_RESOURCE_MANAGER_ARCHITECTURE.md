# MTKrita Path and Resource Manager Architecture

## Status
SSOT — Architecture Baseline v1.1

## Purpose
กำหนดกติกาการอ้างอิง path และการเข้าถึง resource ภายใน MTKrita เพื่อป้องกัน path กระจัดกระจาย, accidental overwrite, race condition และ shared-resource conflict โดยให้ระบบมีจุดควบคุมกลางที่ตรวจสอบและทดสอบได้

## 1. Architectural Principle

> Application code and workers shall not construct or resolve project paths ad hoc.

Path ทุกประเภทที่เป็นส่วนหนึ่งของ runtime contract ต้องผ่าน `PathManager` หรือ typed path reference ที่สร้างโดย `PathManager` เท่านั้น

## 2. PathManager Responsibilities

`PathManager` เป็น service ที่รับผิดชอบ:
- normalize/canonicalize path
- resolve project/job/frame directories
- generate deterministic output paths
- prevent traversal outside approved roots
- distinguish source/read-only paths from working/output paths
- create private worker scratch locations
- reserve temporary and final artifact locations
- expose path aliases/typed handles instead of raw string concatenation
- apply platform-specific Windows path rules
- provide safe atomic-finalization targets
- support cleanup policy and retention policy

## 3. Canonical Roots

Reference logical roots:

```text
ApplicationRoot
ConfigRoot
WorkspaceRoot
JobRoot(job_id)
SourceRoot(job_id)          # immutable reference/copy policy
ScratchRoot(job_id)
WorkerScratchRoot(job_id, worker_id)
ArtifactRoot(job_id)
EvidenceRoot(job_id)
LogRoot(job_id)
ExportRoot(job_id)
QuarantineRoot(job_id)
```

Physical locations may vary by installation mode. Business logic refers to logical roots through `PathManager`.

## 4. Typed Path References

Preferred model:

```text
SourceRef
ArtifactRef
ScratchRef
OutputRef
EvidenceRef
LogRef
```

A typed reference shall carry at least:
- logical kind
- canonical absolute path or internal identifier
- job ownership
- frame/stage ownership when relevant
- mutability policy
- optional hash/version

Raw unvalidated path strings shall not cross critical service boundaries where a typed reference can be used.

## 5. Source Immutability

Source resources are read-only by policy.

Workers and processing providers must never overwrite the original source. Any derived data is written to private scratch or artifact locations allocated by the control plane.

## 6. ResourceManager / ResourceBroker

Path management and resource arbitration are related but separate responsibilities.

`ResourceManager` or `ResourceBroker` owns access to shared mutable resources such as:
- final output namespace
- manifest persistence
- shared logs
- job database
- artifact registry
- scarce providers/devices such as GPU slots if introduced later
- cleanup/retention operations
- file locks/leases where unavoidable

Workers request resource actions through a broker contract instead of directly mutating shared state.

## 7. Worker Private Resources

A worker may directly use:
- its own process memory
- its own immutable input payload
- its own private scratch directory allocated by PathManager/ResourceBroker
- local temporary objects that cannot conflict with another worker

A worker shall not directly mutate:
- shared manifest/database
- final export namespace
- global log file
- shared mutable config
- another worker's scratch space
- global job state

## 8. Atomic Output Rule

Critical output writes use a recovery-safe two-resource pattern:

```text
allocate private temp target
  ↓
write + flush + validate + hash
  ↓
report candidate + task/attempt identity to MainBoard
  ↓
persist durable COMMIT_INTENT in JobStore
  ↓
ResourceBroker atomic promote/rename to final path
  ↓
verify final path hash/identity
  ↓
finalize durable artifact/task state in JobStore
  ↓
publish committed event
```

The durable intent is mandatory for authoritative output/evidence publication that participates in task completion. It bridges the fact that filesystem rename and SQLite commit cannot be one native ACID transaction.

### 8.1 Commit Intent Identity
A commit intent records at least:
- commit id
- job id
- task id
- worker id
- attempt
- expected task generation
- source worker-scratch reference/path identity
- final PathManager-resolved target identity
- expected SHA-256
- byte size when known
- state: `INTENT`, `PROMOTED`, `COMMITTED`, `FAILED_INTEGRITY` or equivalent
- created/updated timestamps

### 8.2 Crash Reconciliation
On restart:
- intent + no final file → incomplete; keep/retry according to authoritative task state;
- intent + matching final file → eligible for idempotent durable finalization if task/attempt remains authoritative;
- intent + mismatching final file/hash → integrity error / REVIEW or FAIL policy; never overwrite silently;
- stale/superseded task attempt → cannot claim or finalize the artifact;
- committed records are immutable completion evidence except explicit retention/deletion operations.

Final file existence alone never establishes successful task/job completion.

## 9. Security Rules

- reject `..` traversal outside approved roots
- canonicalize before authorization checks
- sanitize user-derived filenames
- deterministic filename generation preferred
- disallow arbitrary absolute output destinations from untrusted job payloads unless explicitly approved
- never follow unsafe symlink/reparse-point escapes when enforcing root containment
- record source/output hashes where required

## 10. Interface Sketch

```python
class PathManager(Protocol):
    def job_root(self, job_id: str) -> Path: ...
    def source_ref(self, job_id: str, source: Path) -> SourceRef: ...
    def worker_scratch(self, job_id: str, worker_id: str) -> ScratchRef: ...
    def frame_artifact(self, job_id: str, frame_index: int, kind: str) -> ArtifactRef: ...
    def export_target(self, job_id: str, filename: str) -> OutputRef: ...
```

Concrete signatures may evolve, but application code must preserve the centralized path-management principle.

## 11. Acceptance Requirements

- no critical module constructs shared output paths by string concatenation
- workers cannot write another worker's private area
- path traversal tests pass
- source-overwrite tests pass
- parallel reservation of identical final target does not corrupt output
- crash during write leaves no artifact marked COMPLETE
- crash after filesystem promotion but before database finalization is reconciled deterministically from commit intent + final hash
- stale attempts cannot finalize or overwrite authoritative artifact identity

## 12. Relationship to Other SSOT

- `33_ERROR_RECOVERY_AND_IDEMPOTENCY_SPEC.md`
- `34_DATA_FLOW_AND_ARTIFACT_LIFECYCLE.md`
- `36_SECURITY_AND_FILE_SAFETY_MODEL.md`
- `35_INTERFACE_AND_STAGE_CONTRACTS.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- ADR-017, ADR-019, ADR-020 and ADR-024
