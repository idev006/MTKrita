# MTKrita Error, Recovery and Idempotency Specification

## Status
SSOT — Recovery Baseline v1.0

## 1. Error Classes

### E1 — Input Error
Examples: unreadable/corrupt file, unsupported image condition, invalid dimensions.
Default: FAIL job before mutation.

### E2 — Geometry / Detection Ambiguity
Examples: non-divisible grid, uncertain border, uncertain metadata.
Default: REVIEW or fallback detector; never destructive guess.

### E3 — Processing Provider Error
Examples: OpenCV operation failure, mask generation error.
Default: retry permitted only if deterministic/safe; otherwise REVIEW/FAIL.

### E4 — Output / Filesystem Error
Examples: permission denied, disk full, path collision.
Default: preserve source/intermediate evidence; retry write when safe.

### E5 — Internal Invariant Error
Examples: frame identity mismatch, manifest corruption, impossible state transition.
Default: FAIL and block release of affected outputs.

## 2. Recovery Principles
- source is immutable
- every stage consumes a known upstream artifact
- retries do not stack transforms on prior failed output
- retry decisions are explicit and logged
- an error must never be converted to PASS merely because a later file exists

## 3. Idempotency
For deterministic stages:

`same source hash + same config hash + same engine version + same stage implementation => equivalent result`

A retry should either reuse a verified cached artifact or recompute from the same clean stage input.

## 4. Resume Algorithm

```text
Load manifest
  ↓
Verify source hash
  ↓
Verify config/engine compatibility
  ↓
Validate completed stage artifacts
  ↓
Find earliest incomplete/invalid stage
  ↓
Resume from clean upstream artifact
  ↓
Append new attempt evidence
```

## 5. Retry Policy
Each stage shall declare:
- retryable: yes/no
- maximum automatic attempts
- backoff if external/system resource related
- clean input artifact to restart from
- terminal failure code

Image-processing logic errors should not be blindly retried because identical deterministic input usually reproduces the same failure.

## 6. Crash Recovery
If application terminates unexpectedly:
- source remains untouched
- manifest should be recoverable from last atomic write
- partial output file must not be mistaken for verified output
- temporary files use explicit temp naming and atomic rename where practical
- running stages become interrupted/pending on next resume after artifact validation

## 7. Output Collision
Default behavior:
- deterministic job workspace prevents accidental overwrite
- exported filenames may be regenerated only inside authorized output target
- existing unrelated user files must never be silently overwritten

## 8. Manifest Integrity
Manifest updates should be atomic where practical. Each completed stage records:
- stage name
- attempt id
- status
- provider/strategy
- config/version
- findings/actions
- artifact reference/hash where appropriate

## 9. REVIEW Recovery
A frame in REVIEW can resume after:
- operator approval
- permitted parameter override
- provider strategy change
- manual correction on working copy

Every resolution must be recorded and re-QA'd.

## 10. Acceptance Tests
Mandatory cases:
- app termination during processing
- disk write failure
- retry after provider exception
- corrupted intermediate artifact
- source changed between initial run and resume
- repeated retry does not repeatedly resize/crop
- output collision does not overwrite unrelated file

References: `31_STATE_MACHINE_SPEC.md`, `34_DATA_FLOW_AND_ARTIFACT_LIFECYCLE.md`.
