from __future__ import annotations

import hashlib
import sys
from contextlib import suppress
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from mtkrita.artifact_commit import ArtifactCommitCoordinator, ArtifactCommitJournal
from mtkrita.dispatch import DispatchCoordinator
from mtkrita.event_bus import InProcessEventBus
from mtkrita.job_store import JobStore
from mtkrita.m2_task_descriptor import M2FrameTargetResolver
from mtkrita.path_manager import PathManager
from mtkrita.resource_broker import ResourceBroker
from mtkrita.scheduler import BoundedFairScheduler, ScheduledTask
from mtkrita.task_leases import TaskLeaseRegistry
from mtkrita.task_results import CandidateResultCoordinator
from mtkrita.worker_events import WorkerEventRouter
from mtkrita.worker_manager import WorkerManager, WorkerState
from mtkrita.worker_process import WindowsSpawnWorkerFactory
from mtkrita.worker_tasks import ExecuteTaskCommandBuilder, parse_candidate_event

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows real-process M2 E2E")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_transparent_source(path: Path) -> None:
    image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 87, 87), fill=(220, 30, 30, 255))
    image.save(path, format="PNG")


def _descriptor(*, digest: str) -> dict[str, object]:
    return {
        "task_type": "m2.frame",
        "input_name": "frame-001.png",
        "input_sha256": digest,
        "output_name": "01.png",
        "frame_index": 1,
        "row": 0,
        "column": 0,
        "extraction_rect": [0, 0, 128, 128],
        "extraction_method": "single-frame-e2e",
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


def test_real_windows_worker_m2_success_reaches_final_output_only_via_commit(
    tmp_path: Path,
) -> None:
    paths = PathManager(tmp_path / "workspace")
    paths.prepare_job("job-1")
    external = tmp_path / "original-source.png"
    _write_transparent_source(external)
    original_bytes = external.read_bytes()

    resources = ResourceBroker(paths)
    staged_ref = paths.input("job-1", "frame-001.png")
    staged = resources.stage_input_file(external, staged_ref, expected_sha256=_sha256(external))
    staged_bytes = staged_ref.path.read_bytes()

    jobs = JobStore(paths.evidence("job-1", "jobs.sqlite3").path)
    jobs.initialize()
    jobs.create_job("job-1")
    jobs.create_task(
        "task-1",
        job_id="job-1",
        descriptor=_descriptor(digest=staged.sha256),
        descriptor_version=1,
    )

    scheduler = BoundedFairScheduler(max_inflight_tasks=1, max_queued_tasks=2)
    scheduler.submit(ScheduledTask("task-1", "job-1"))
    leases = TaskLeaseRegistry()
    workers = WorkerManager()
    bus = InProcessEventBus()
    routed_types: list[str] = []
    bus.subscribe_all(lambda message: routed_types.append(message.message_type))
    router = WorkerEventRouter(workers=workers, events=bus)

    session = WindowsSpawnWorkerFactory().spawn("worker-1")
    try:
        workers.register("worker-1", session.handle)
        ready = session.receive_event(timeout_seconds=10)
        router.route(ready)
        assert workers.get("worker-1").state == WorkerState.READY

        assignment = DispatchCoordinator(
            scheduler=scheduler,
            jobs=jobs,
            leases=leases,
            workers=workers,
        ).dispatch_next(worker_id="worker-1", lease_seconds=120)
        assert assignment is not None
        assert jobs.get_task("task-1").state == "RUNNING"
        assert workers.get("worker-1").state == WorkerState.BUSY

        command = ExecuteTaskCommandBuilder(
            jobs=jobs,
            paths=paths,
            resources=resources,
        ).build("task-1")
        session.send_command(command)

        started = session.receive_event(timeout_seconds=10)
        router.route(started)
        candidate = session.receive_event(timeout_seconds=20)
        router.route(candidate)
        parsed = parse_candidate_event(candidate)

        assert started.message_type == "TaskStarted"
        assert candidate.message_type == "TaskSucceededCandidate"
        assert len(parsed.artifacts) == 1
        assert jobs.get_task("task-1").state == "RUNNING"
        assert workers.get("worker-1").state == WorkerState.BUSY
        assert not paths.output("job-1", "01.png").path.exists()

        journal = ArtifactCommitJournal(jobs)
        journal.initialize()
        outcome = CandidateResultCoordinator(
            jobs=jobs,
            paths=paths,
            resources=resources,
            commits=ArtifactCommitCoordinator(journal, resources),
            leases=leases,
            workers=workers,
            targets=M2FrameTargetResolver(paths),
            inflight=scheduler,
        ).accept(candidate)

        final_path = paths.output("job-1", "01.png").path
        assert outcome.task.state == "SUCCEEDED"
        assert final_path.is_file()
        assert scheduler.inflight_count == 0
        assert workers.get("worker-1").state == WorkerState.READY
        assert external.read_bytes() == original_bytes
        assert staged_ref.path.read_bytes() == staged_bytes

        with Image.open(final_path) as final_image:
            assert final_image.format == "PNG"
            assert final_image.size == (370, 320)
            rgba = final_image.convert("RGBA")
            alpha_min, alpha_max = rgba.getchannel("A").getextrema()
            assert alpha_min == 0
            assert alpha_max == 255

        assert routed_types[:3] == ["WorkerReady", "TaskStarted", "TaskSucceededCandidate"]
    finally:
        current = workers.get("worker-1")
        if current.state not in {WorkerState.STOPPED, WorkerState.LOST}:
            with suppress(BrokenPipeError, OSError):
                workers.request_stop("worker-1")
            with suppress(TimeoutError, EOFError, OSError, RuntimeError):
                while workers.get("worker-1").state == WorkerState.STOPPING:
                    router.route(session.receive_event(timeout_seconds=2))
            session.wait_for_exit(5)
        if session.handle.is_alive():
            session.handle.terminate()
            session.handle.join(5)
        session.close()
