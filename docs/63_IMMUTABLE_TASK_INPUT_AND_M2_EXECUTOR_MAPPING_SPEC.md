# MTKrita Immutable Task Input and M2 Executor Mapping Specification

## Status
SSOT — Integration Baseline v1.0

## Purpose
Define how frame-level M2 image-processing work crosses the MainBoard/worker boundary without allowing a worker to consume arbitrary filesystem paths or publish final output directly.

This document connects the platform-control contracts in `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`, `61_WINDOWS_WORKER_PROCESS_AND_IPC_SPEC.md`, and `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md` to the headless M2 `FramePipeline` implemented in PR #9.

## 1. Core Principle

> MainBoard stages immutable input; worker computes from staged input; worker writes only private scratch; MainBoard commits final output.

A worker must never obtain execution authority from an arbitrary path embedded in user/UI/domain payloads.

## 2. Integration Finding

The M2 frame pipeline is headless and suitable for a `TaskExecutor`, but it needs an image input path. The current platform implementation originally exposed worker scratch/output/evidence/log paths but did not yet implement the SSOT `SourceRef`/immutable-input path class described in `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`.

Passing an external absolute path directly in a durable task descriptor would violate the path/resource ownership model. Therefore an explicit immutable input staging layer is mandatory before M2 worker integration.

## 3. Job Input Root

Each job has a control-plane-owned immutable input namespace:

```text
WorkspaceRoot/
  jobs/
    <job_id>/
      inputs/
      scratch/
      outputs/
      evidence/
      logs/
```

`inputs/` is not worker-owned scratch. It is written only by MainBoard/ResourceBroker staging operations and is read-only by policy after successful staging.

## 4. Typed Input Reference

`PathManager` shall expose a typed `PathRef` with logical kind `INPUT` (equivalent to the previously documented SourceRef/immutable ArtifactRef concept).

An input reference carries:
- `job_id`
- canonical workspace-owned path
- logical filename / input identity
- no worker ownership
- immutable/read-only policy after staging

Workers may read this path only when it is supplied through an approved `ExecuteTask` command built by MainBoard.

## 5. Input Staging

`ResourceBroker.stage_input_file()` is the control-plane boundary for bringing a file into the immutable job-input namespace.

Required behavior:
1. accept an explicitly selected/readable external source file;
2. resolve the destination using `PathManager.input()`;
3. refuse overwrite of an existing staged input;
4. copy to a private temporary file under the destination directory;
5. flush/close the temporary file;
6. compute SHA-256 and byte size;
7. atomically promote the temporary file to the staged input path;
8. return immutable input evidence containing typed reference/hash/size.

The external source is read-only. Staging must never rename, overwrite, delete or mutate the original source.

## 6. Durable M2 Frame Task Descriptor

M2 frame tasks use descriptor schema version 1 with no absolute filesystem paths.

Required fields:

```json
{
  "task_type": "m2.frame",
  "input_name": "frame-001.png",
  "input_sha256": "<64 lowercase hex>",
  "output_name": "01.png",
  "frame_index": 1,
  "row": 0,
  "column": 0,
  "extraction_rect": [0, 0, 512, 512],
  "extraction_method": "exact-grid",
  "extraction_confidence": 1.0,
  "pipeline_config": {
    "target_width": 370,
    "target_height": 320,
    "margin": 10,
    "remove_border": true,
    "remove_metadata": true,
    "border_auto_threshold": 0.995,
    "metadata_auto_threshold": 0.72
  }
}
```

Rules:
- `input_name` is a safe single path component, never an absolute path;
- `input_sha256` binds the task to the exact staged input bytes;
- `output_name` is a logical final filename used only by a MainBoard target resolver; the worker does not receive a final output path;
- frame geometry/provenance fields preserve M2 evidence lineage;
- pipeline configuration is an immutable snapshot sufficient to reproduce the frame operation;
- unsupported or unknown critical descriptor fields fail validation rather than being ignored.

## 7. ExecuteTask Input Expansion

At dispatch time, `ExecuteTaskCommandBuilder` resolves the durable descriptor's `input_name` through `PathManager.input(job_id, input_name)` and validates the staged file through `ResourceBroker`/input evidence policy.

The command carries an explicit versioned immutable input reference containing:
- logical kind `INPUT`;
- staged canonical path;
- SHA-256;
- byte size.

This path is not taken from the worker, UI, or arbitrary descriptor text. It is reconstructed by the control plane.

## 8. M2FrameTaskExecutor Boundary

`M2FrameTaskExecutor` implements the platform `TaskExecutor` protocol.

Worker-side sequence:

```text
parse ExecuteTask
  ↓
validate M2 descriptor schema
  ↓
validate staged input identity/hash before use
  ↓
open staged image read-only
  ↓
run headless process_frame(...)
  ↓
map FrameResult status/evidence to TaskCandidateResult
  ↓
if PASS/AUTO_FIXED:
    write exactly one provisional PNG to worker-private scratch
    return TaskSucceededCandidate(filename/hash/size/findings)
  ↓
if REVIEW:
    return TaskReviewCandidate(findings/evidence), no authoritative output
  ↓
if FAIL:
    return TaskFailed(error code/findings), no authoritative output
```

The executor never invokes final-output promotion.

## 9. M2 Status Mapping

M2 `FrameStatus` mapping:
- `PASS` → `TaskCandidateStatus.SUCCEEDED`
- `AUTO_FIXED` → `TaskCandidateStatus.SUCCEEDED`
- `REVIEW` → `TaskCandidateStatus.REVIEW`
- `FAIL` → `TaskCandidateStatus.FAILED`

For the current platform contract, successful frame execution yields exactly one primary PNG candidate. A future multi-artifact task requires an explicit commit-group design and must not be implemented by repeatedly finalizing the same task.

## 10. Scratch Export Rule

The existing M2 PNG export primitive may be reused only as a byte-writing implementation against a **PathManager-approved worker scratch path**.

Its old wording/usage as a final-target writer does not grant a worker authority over `outputs/`.

Final output remains:

```text
TaskSucceededCandidate
  ↓
CandidateResultCoordinator
  ↓
validate durable RUNNING / worker / attempt / lease
  ↓
validate worker scratch hash + size
  ↓
MainBoard CandidateTargetResolver resolves output_name
  ↓
ADR-024 durable commit intent + atomic promote + final verification
  ↓
SUCCEEDED
```

## 11. Security Rules

- durable M2 descriptor contains no external absolute paths;
- worker input path must resolve under the job `inputs/` namespace;
- worker input reference must have no worker ownership and cannot name output/evidence/log paths;
- staged input hash must match the descriptor/command evidence before image processing;
- scratch output filename must be a safe single component;
- worker never writes `outputs/`, JobStore, artifact journal, scheduler state or shared logs;
- no symlink/reparse-point escape is allowed to bypass workspace ownership checks;
- staging never mutates the original source.

## 12. Required Automated Tests

- PathManager creates and resolves typed INPUT paths;
- job preparation creates `inputs/`;
- staging copies bytes without altering source;
- staging refuses overwrite;
- staged hash/size verification passes and mismatch fails;
- ExecuteTask command reconstructs input path from logical input name, not from arbitrary descriptor path;
- malformed M2 descriptor/path fields are rejected;
- task input hash mismatch is rejected before processing;
- M2 executor PASS/AUTO_FIXED writes one scratch PNG and returns success candidate;
- REVIEW/FAIL produce no authoritative output;
- final output appears only through CandidateResultCoordinator + ADR-024;
- source and staged input remain unchanged after execution.

## 13. Branch Integration Strategy

PR #9 (`feat/m2-refresh`) remains the image-processing implementation source. PR #10 (`feat/platform-control-foundation`) remains the platform/control-plane source.

Do not duplicate M2 algorithms inside the platform layer. First land/verify the immutable input and descriptor boundary. Then integrate the actual M2 executor on a controlled integration branch or after both prerequisite branches are reconciled with `main`.

## 14. Related SSOT

- `35_INTERFACE_AND_STAGE_CONTRACTS.md`
- `46_PATH_AND_RESOURCE_MANAGER_ARCHITECTURE.md`
- `48_BATCH_MULTIWORKER_EXECUTION_MODEL.md`
- `61_WINDOWS_WORKER_PROCESS_AND_IPC_SPEC.md`
- `62_TASK_EXECUTION_AND_RESULT_COMMIT_SPEC.md`
- ADR-017, ADR-019, ADR-023, ADR-024, ADR-025, ADR-026
