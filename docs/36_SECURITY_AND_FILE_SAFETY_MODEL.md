# MTKrita Security and File Safety Model

## Status
SSOT — Security/File Safety Baseline v1.0

## Purpose
กำหนด minimum security and file-safety controls สำหรับ desktop image-processing application ที่รับไฟล์จากผู้ใช้และเขียน output อัตโนมัติ

## 1. Trust Boundary
User-provided images are untrusted input. Parsing, metadata, dimensions and encoded content must not be assumed valid solely from filename or extension.

## 2. File Validation
System shall:
- inspect real file format/signature through image library parsing
- reject unreadable/corrupt input safely
- impose configurable sanity limits on dimensions/pixel count where appropriate
- avoid executing embedded content/macros/scripts
- normalize paths before use

## 3. Source Protection
- source is read-only by default
- no in-place overwrite
- source SHA-256 recorded before processing
- recheck source identity before resume/recovery where relevant

## 4. Output Path Safety
- output paths must remain within authorized workspace/export target
- path traversal (`..`) from config/user-supplied metadata must not escape target root
- deterministic generated filenames must be sanitized
- unrelated existing user files must not be overwritten silently

## 5. Temporary File Safety
- partial writes use temp files where practical
- atomic rename/replace used for committed artifacts where supported
- abandoned temp files must not be interpreted as successful output

## 6. Resource Exhaustion
Potentially hostile or malformed images may have extreme dimensions or decompression cost. The application should define guards for:
- maximum practical pixel count
- memory estimation
- batch concurrency
- recursion/loop limits in detection
- provider timeouts where external processes are introduced

## 7. External Providers
MVP is local-first. If a future provider sends images/data to an external service, this requires:
- new ADR
- explicit user-facing disclosure/consent model
- data-flow update
- security/privacy review
- configuration to disable external processing

## 8. External Executables
If ImageMagick, Krita or other executables are invoked:
- use fixed executable paths/configured trusted locations
- avoid shell string concatenation
- pass arguments as structured process parameters
- quote/validate file paths
- capture exit code/stdout/stderr
- do not treat launch success as processing success

## 9. Logging
Logs must avoid unnecessary exposure of private image content. Paths may be recorded for local traceability, but future telemetry/cloud features require separate approval.

## 10. Dependency Safety
Release process must maintain dependency inventory and review known critical vulnerabilities/licensing before G4.

## 11. Security-Relevant Failure Behavior
Security/file integrity uncertainty must fail closed:
- invalid path → reject
- source mismatch on resume → stop/review
- manifest integrity inconsistency → fail job
- untrusted external provider unavailable → do not silently change to a lower-safety behavior

## 12. Acceptance Tests
- corrupt image
- extension/signature mismatch
- path traversal attempt
- output collision
- source changed during job/resume
- extremely large image sanity guard
- partial output after crash not accepted as verified artifact

References: `33_ERROR_RECOVERY_AND_IDEMPOTENCY_SPEC.md`, `32_DEPLOYMENT_AND_RUNTIME_ARCHITECTURE.md`, `19_AUDIT_AND_COMPLIANCE_PLAN.md`.
