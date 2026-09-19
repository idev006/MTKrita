# MTKrita Operational Runbook

## Status
SSOT — Operations and Troubleshooting Baseline v1.0

## Purpose
กำหนดขั้นตอนมาตรฐานสำหรับเริ่มงาน หยุดงาน pause/resume ตรวจสอบ worker ล้มเหลว กู้คืน job และรวบรวม diagnostics

## Normal Operation
1. validate TOML config
2. open/create JobStore
3. initialize PathManager and ArtifactStore
4. start MainBoard services
5. register workers
6. submit job
7. monitor events/heartbeats
8. commit outputs atomically
9. finalize manifest and evidence

## Pause
- stop scheduling new tasks
- allow or cancel in-flight tasks only at defined safe boundary
- persist state/checkpoints
- mark job PAUSED only after durable state commit

## Resume
- reload persisted job/config/provider versions
- validate source/config hashes
- validate checkpoints/artifacts
- reject stale leases/attempts
- schedule only unfinished/retryable work

## Stop
Graceful stop must persist durable state and prevent new dispatch. Forced termination is recovered on next startup through JobStore reconciliation.

## Worker Lost
- detect heartbeat/lease expiry
- mark attempt abandoned
- release broker-managed resources
- create new attempt if retry policy allows
- reject late stale result from old attempt

## Disk Full / Write Failure
- stop new commits
- preserve existing valid artifacts
- mark affected task retryable/failed with stable error code
- do not publish partial final output

## Provider Failure
- capture provider ID/version, exception class, task/stage context
- classify retryable vs non-retryable
- route unsafe/ambiguous image outcome to REVIEW, not silent fallback

## Recovery Startup
On application startup after abnormal termination:
1. inspect incomplete jobs
2. reconcile leases and attempts
3. verify artifact hashes/checkpoints
4. quarantine incomplete temporary files
5. restore resumable jobs to PAUSED/RECOVERABLE state
6. require explicit/automatic resume according to policy

## Diagnostics
Support bundle should include effective config, manifest, state/event history, errors, provider/dependency versions and artifact hashes. Source artwork is excluded unless explicitly authorized.

## Incident Triage
Priority order:
1. source/artwork integrity
2. shared-state consistency
3. recoverability
4. output correctness
5. throughput

References: `33_ERROR_RECOVERY_AND_IDEMPOTENCY_SPEC.md`, `49_RELIABILITY_RECOVERY_OBSERVABILITY_SPEC.md`.
