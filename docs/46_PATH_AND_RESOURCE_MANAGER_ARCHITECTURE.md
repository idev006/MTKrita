# MTKrita Path and Resource Manager Architecture

## Status
SSOT — Architecture Baseline v1.2 — Immutable Input Staging Implemented

## Purpose
กำหนดกติกาการอ้างอิง path และการเข้าถึง resource ภายใน MTKrita เพื่อป้องกัน path กระจัดกระจาย, accidental overwrite, race condition และ shared-resource conflict โดยให้ระบบมีจุดควบคุมกลางที่ตรวจสอบและทดสอบได้

## 1. Architectural Principle

> Application code and workers shall not construct or resolve project paths ad hoc.

Path ทุกประเภทที่เป็นส่วนหนึ่งของ runtime contract ต้องผ่าน `PathManager` หรือ typed path reference ที่สร้างโดย `PathManager` เท่านั้น

## 2. PathManager Responsibilities

`PathManager` เป็น service ที่รับผิดชอบ:
- normalize/canonicalize path
- resolve project/job/input/frame directories
- generate deterministic output paths
- prevent traversal outside approved roots
- distinguish immutable input/read-only paths from worker scratch/output paths
- create private worker scratch locations
- reserve temporary and final artifact locations
- expose path aliases/typed handles instead of raw string concatenation
- apply platform-specific Windows path rules
- provide safe atomic-finalization targets
- support cleanup policy and retention policy

## 3. Canonical Roots

Current runtime roots include:

```text
WorkspaceRoot
JobRoot(job_id)
JobInputRoot(job_id)         # jobs/<job_id>/inputs — immutable after staging
WorkerScratchRoot(job_id, worker_id)
EvidenceRoot(job_id)
LogRoot(job_id)
ExportRoot(job_id)
```

Future installation/config/quarantine roots may remain separate physical locations. Business logic refers to logical roots through `PathManager`.

`PathManager.prepare_job(job_id)` prepares at minimum:
- `inputs/`
- `scratch/`
- `outputs/`
- `evidence/`
- `logs/`

## 4. Typed Path References

The implemented `PathKind` baseline includes:
- `JOB_ROOT`
- `INPUT`
- `WORKER_SCRATCH`
- `OUTPUT`
- `EVIDENCE`
- `LOG`

A `PathRef` carries:
- logical kind
- canonical workspace-owned path
- job ownership
- optional worker ownership where applicable

Rules:
- INPUT/OUTPUT/EVIDENCE/LOG are never worker-owned;
- WORKER_SCRATCH must carry worker ownership;
- raw unvalidated path strings shall not cross critical service boundaries where a typed reference can be used;
- final and staged paths are reconstructed by the control plane, not accepted as worker authority.

## 5. Source and Input Immutability

The original source selected by the user or upstream workflow is read-only by policy.

Before a worker consumes file input, MainBoard/ResourceBroker stages a copy into `JobInputRoot` and binds it to cryptographic evidence. The original source must never be renamed, overwritten, deleted or modified by staging or worker execution.

After successful staging, the job INPUT copy is immutable by policy for the lifetime of the execution contract. Workers may read it but may not overwrite it.

## 6. Immutable Input Staging

`ResourceBroker.stage_input_file()` owns ingress from an external/control-plane source file into a PathManager `INPUT` target.

Required sequence:

```text
explicit source selection
  ↓
PathManager.input(job_id, logical_name)
  ↓
refuse existing destination / unsafe source
  ↓
copy to private staging temp under input directory
  ↓
flush + fsync
  ↓
compute SHA-256 + byte size
  ↓
validate expected hash when supplied
  ↓
atomic promote to INPUT target
  ↓
return StagedInput evidence
```

Current safety rules:
- staging source must be a regular file and not a symlink;
- destination must be a same-job, non-worker `INPUT` reference;
- silent overwrite is prohibited;
- staging failure removes temporary file and leaves original source untouched;
- `verify_input_file()` verifies INPUT type, no worker ownership, file existence, no symlink, byte size when supplied, and SHA-256.

## 7. ResourceManager / ResourceBroker

Path management and resource arbitration are related but separate responsibilities.

`ResourceBroker` currently owns:
- immutable input staging/verification;
- worker candidate validation;
- SHA-256/byte-size integrity checks;
- authoritative OUTPUT/EVIDENCE promotion;
- overwrite refusal and same-job checks.

Broader ResourceManager responsibilities may later include manifests, scarce GPU/provider slots, retention and explicit file locks, but workers do not gain direct authority over those resources.

## 8. Worker Private Resources

A worker may directly use:
- its own process memory;
- explicit immutable INPUT references supplied by an approved ExecuteTask;
- its own private scratch directory allocated by PathManager;
- provider-local temporary objects/resources;
- IPC endpoints.

A worker shall not directly mutate:
- INPUT files;
- shared manifest/database;
- final export namespace;
- global log file;
- shared mutable config;
- another worker's scratch space;
- global job state.

An arbitrary path embedded in a durable descriptor, UI payload or provider payload does not become an approved input merely because it exists.

## 9. ExecuteTask Input Rule

Durable task descriptors store logical input identity/hash, not arbitrary external absolute paths.

At dispatch:
1. `ExecuteTaskCommandBuilder` loads the durable RUNNING task/descriptor;
2. resolves logical input using `PathManager.input(job_id, input_name)`;
3. verifies staged input through `ResourceBroker.verify_input_file()`;
4. emits a versioned immutable input record containing staged path/hash/size;
5. worker independently re-verifies file identity before processing where required.

This creates two integrity boundaries: control-plane pre-dispatch verification and worker-side pre-processing verification.

## 10. Atomic Output Rule

Critical output writes use a recovery-safe two-resource pattern:

```text
worker writes private scratch target
  ↓
flush + validate + hash
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

### 10.1 Commit Intent Identity
A commit intent records at least:
- commit id
- job id
- task id
- worker id
- attempt
- expected task generation
- source worker-scratch identity
- final PathManager-resolved target identity
- expected SHA-256
- byte size when known
- state: `INTENT`, `PROMOTED`, `COMMITTED`, `FAILED_INTEGRITY` or equivalent
- created/updated timestamps

### 10.2 Crash Reconciliation
On restart:
- intent + no final file → incomplete; keep/retry according to authoritative task state;
- intent + matching final file → eligible for idempotent durable finalization if task/attempt remains authoritative;
- intent + mismatching final file/hash → integrity error / REVIEW or FAIL policy; never overwrite silently;
- stale/superseded task attempt → cannot claim or finalize the artifact;
- committed records are immutable completion evidence except explicit retention/deletion operations.

Final file existence alone never establishes successful task/job completion.

## 11. Security Rules

- reject `..` traversal outside approved roots;
- canonicalize before authorization checks;
- sanitize user-derived filenames;
- deterministic filename generation preferred;
- reject arbitrary absolute worker input/output destinations from task payloads;
- never follow unsafe symlink/reparse-point escapes when enforcing root containment;
- original source remains immutable;
- staged INPUT is hash-bound and read-only by policy;
- record source/input/output hashes where required.

## 12. Interface Sketch

Current concrete semantics correspond to:

```python
class PathManager(Protocol):
    def job_root(self, job_id: str) -> PathRef: ...
    def input(self, job_id: str, filename: str) -> PathRef: ...
    def worker_scratch(self, job_id: str, worker_id: str) -> PathRef: ...
    def worker_file(self, job_id: str, worker_id: str, filename: str) -> PathRef: ...
    def output(self, job_id: str, filename: str) -> PathRef: ...
    def evidence(self, job_id: str, filename: str) -> PathRef: ...
```

Concrete signatures may evolve, but centralized path ownership and immutable input staging shall remain invariant.

## 13. Acceptance Requirements

- no critical module constructs shared output paths ad hoc;
- workers cannot write another worker's private area;
- path traversal tests pass;
- input/source overwrite tests pass;
- staging leaves external source unchanged;
- staged input overwrite is refused;
- staged input hash/size mismatch is rejected;
- worker cannot convert descriptor path text into input authority;
- parallel reservation of identical final target does not corrupt output;
- crash during write leaves no artifact marked COMPLETE;
- crash after filesystem promotion but before database finalization is reconciled deterministically from commit intent + final hash;
- stale attempts cannot finalize or overwrite authoritative artifact identity.

## 14. Relationship to Other SSOT

- `33_ERROR_RECOVERY_AND_IDEMPOTENCY_SPEC.md`
- `34_DATA_FLOW_AND_ARTIFACT_LIFECYCLE.md`
- `35_INTERFACE_AND_STAGE_CONTRACTS.md`
- `36_SECURITY_AND_FILE_SAFETY_MODEL.md`
- `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`
- `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md`
- `63_IMMUTABLE_TASK_INPUT_AND_M2_EXECUTOR_MAPPING_SPEC.md`
- ADR-017, ADR-019, ADR-020, ADR-024, ADR-026 and ADR-027
