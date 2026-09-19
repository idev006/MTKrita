from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

import pytest
from PIL import Image

from mtkrita.m2_executor import M2FrameExecutorError, M2FrameTaskExecutor
from mtkrita.worker_tasks import ExecuteTaskRequest, TaskCandidateStatus, TaskInput


class FakeStatus(StrEnum):
    PASS = "PASS"
    AUTO_FIXED = "AUTO_FIXED"
    REVIEW = "REVIEW"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FakeFinding:
    code: str
    severity: str = "REVIEW"
    message: str = "message"
    measurements: dict[str, object] = field(default_factory=dict)


@dataclass
class FakeFrameResult:
    status: FakeStatus
    findings: list[FakeFinding] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    processing_mode: str | None = "transparent"
    content_bbox: tuple[int, int, int, int] | None = (1, 2, 7, 8)
    evidence: dict[str, object] = field(default_factory=lambda: {"bbox": (1, 2, 7, 8)})


@dataclass
class FakePipelineOutput:
    image: Image.Image
    result: FakeFrameResult


def _descriptor(*, digest: str) -> dict[str, object]:
    return {
        "task_type": "m2.frame",
        "input_name": "frame-001.png",
        "input_sha256": digest,
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
            "remove_border": True,
            "remove_metadata": True,
            "border_auto_threshold": 0.995,
            "metadata_auto_threshold": 0.72,
        },
    }


def _request(tmp_path: Path) -> tuple[ExecuteTaskRequest, Path]:
    staged = tmp_path / "inputs" / "frame-001.png"
    staged.parent.mkdir(parents=True)
    payload = b"immutable-input"
    staged.write_bytes(payload)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    digest = hashlib.sha256(payload).hexdigest()
    return (
        ExecuteTaskRequest(
            job_id="job-1",
            task_id="task-1",
            worker_id="worker-1",
            attempt=2,
            descriptor_version=1,
            descriptor=_descriptor(digest=digest),
            inputs=(
                TaskInput(
                    name="frame-001.png",
                    path=str(staged),
                    sha256=digest,
                    byte_size=len(payload),
                ),
            ),
            scratch_path=str(scratch),
        ),
        staged,
    )


def _executor(result: FakeFrameResult, calls: dict[str, object]) -> M2FrameTaskExecutor:
    def process(image: Image.Image, **kwargs: object) -> FakePipelineOutput:
        calls["process"] = kwargs
        return FakePipelineOutput(image=image.copy(), result=result)

    def config_factory(snapshot: object) -> object:
        calls["config"] = snapshot
        return {"config": "built"}

    def writer(
        image: Image.Image,
        target_path: str | Path,
        *,
        allow_overwrite: bool = False,
    ) -> object:
        calls["writer_allow_overwrite"] = allow_overwrite
        calls["writer_image_size"] = image.size
        Path(target_path).write_bytes(b"provisional-png")
        return object()

    return M2FrameTaskExecutor(
        frame_processor=process,
        config_factory=config_factory,
        png_writer=writer,
        image_loader=lambda _path: Image.new("RGBA", (8, 8), (255, 0, 0, 255)),
    )


@pytest.mark.parametrize("status", [FakeStatus.PASS, FakeStatus.AUTO_FIXED])
def test_m2_executor_success_writes_one_private_candidate(
    tmp_path: Path,
    status: FakeStatus,
) -> None:
    request, staged = _request(tmp_path)
    calls: dict[str, object] = {}
    result = FakeFrameResult(
        status=status,
        findings=[FakeFinding(code="QA.OK", severity="INFO")],
        actions=["SMART_FIT"],
    )

    outcome = _executor(result, calls).execute(request)

    assert outcome.status == TaskCandidateStatus.SUCCEEDED
    assert len(outcome.artifacts) == 1
    artifact = outcome.artifacts[0]
    candidate = Path(request.scratch_path) / artifact.filename
    assert candidate.read_bytes() == b"provisional-png"
    assert artifact.sha256 == hashlib.sha256(b"provisional-png").hexdigest()
    assert artifact.byte_size == len(b"provisional-png")
    assert staged.read_bytes() == b"immutable-input"
    assert calls["writer_allow_overwrite"] is False
    process_args = calls["process"]
    assert isinstance(process_args, dict)
    assert process_args["index"] == 1
    assert process_args["extraction_rect"] == (0, 0, 512, 512)
    assert outcome.findings[-1]["code"] == "M2.FRAME_EVIDENCE"
    assert outcome.findings[-1]["evidence"]["bbox"] == [1, 2, 7, 8]


def test_m2_executor_review_produces_no_artifact(tmp_path: Path) -> None:
    request, _ = _request(tmp_path)
    calls: dict[str, object] = {}
    result = FakeFrameResult(
        status=FakeStatus.REVIEW,
        findings=[FakeFinding(code="BORDER.CONTACT_RISK")],
    )

    outcome = _executor(result, calls).execute(request)

    assert outcome.status == TaskCandidateStatus.REVIEW
    assert outcome.artifacts == ()
    assert "writer_allow_overwrite" not in calls
    assert outcome.findings[0]["code"] == "BORDER.CONTACT_RISK"


def test_m2_executor_fail_uses_pipeline_finding_as_failure_identity(tmp_path: Path) -> None:
    request, _ = _request(tmp_path)
    result = FakeFrameResult(
        status=FakeStatus.FAIL,
        findings=[FakeFinding(code="CONTENT.EMPTY", severity="FAIL", message="empty")],
    )

    outcome = _executor(result, {}).execute(request)

    assert outcome.status == TaskCandidateStatus.FAILED
    assert outcome.artifacts == ()
    assert outcome.error_code == "CONTENT.EMPTY"
    assert outcome.error_message == "empty"


def test_m2_executor_rejects_tampered_staged_input_before_processing(tmp_path: Path) -> None:
    request, staged = _request(tmp_path)
    staged.write_bytes(b"tampered")
    calls: dict[str, object] = {}

    with pytest.raises(M2FrameExecutorError, match="byte-size mismatch|hash mismatch"):
        _executor(FakeFrameResult(status=FakeStatus.PASS), calls).execute(request)

    assert "process" not in calls
    assert "writer_allow_overwrite" not in calls


def test_m2_executor_rejects_input_identity_mismatch(tmp_path: Path) -> None:
    request, _ = _request(tmp_path)
    wrong_input = TaskInput(
        name="other.png",
        path=request.inputs[0].path,
        sha256=request.inputs[0].sha256,
        byte_size=request.inputs[0].byte_size,
    )
    mismatched = ExecuteTaskRequest(
        job_id=request.job_id,
        task_id=request.task_id,
        worker_id=request.worker_id,
        attempt=request.attempt,
        descriptor_version=request.descriptor_version,
        descriptor=request.descriptor,
        inputs=(wrong_input,),
        scratch_path=request.scratch_path,
    )

    with pytest.raises(M2FrameExecutorError, match="identity"):
        _executor(FakeFrameResult(status=FakeStatus.PASS), {}).execute(mismatched)


def test_m2_executor_rejects_unknown_frame_status(tmp_path: Path) -> None:
    request, _ = _request(tmp_path)

    with pytest.raises(M2FrameExecutorError, match="unsupported M2 frame status"):
        _executor(FakeFrameResult(status=FakeStatus.UNKNOWN), {}).execute(request)
