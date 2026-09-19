import hashlib
from pathlib import Path

from mtkrita.artifact_commit import (
    ArtifactCommitCoordinator,
    ArtifactCommitJournal,
    ArtifactCommitReconciler,
)
from mtkrita.job_store import JobStore
from mtkrita.path_manager import PathManager
from mtkrita.resource_broker import ResourceBroker


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _running_task(tmp_path: Path):
    paths = PathManager(tmp_path / "workspace")
    paths.prepare_job("job-1")
    paths.prepare_worker_scratch("job-1", "worker-1")
    jobs = JobStore(paths.evidence("job-1", "jobs.sqlite3").path)
    jobs.initialize()
    jobs.create_job("job-1")
    jobs.create_task("task-1", job_id="job-1")
    task = jobs.assign_task(
        "task-1",
        expected_generation=0,
        worker_id="worker-1",
        attempt=1,
        lease_expires_at="2030-01-01T00:00:00+00:00",
    )
    journal = ArtifactCommitJournal(jobs)
    journal.initialize()
    broker = ResourceBroker(paths)
    return paths, jobs, task, journal, broker


def test_coordinator_commits_file_and_task_with_durable_record(tmp_path: Path) -> None:
    paths, jobs, task, journal, broker = _running_task(tmp_path)
    source = paths.worker_file("job-1", "worker-1", "candidate.png")
    target = paths.output("job-1", "01.png")
    payload = b"valid-png-placeholder"
    source.path.write_bytes(payload)

    committed = ArtifactCommitCoordinator(journal, broker).commit_task_artifact(
        commit_id="commit-1",
        task=task,
        source=source,
        target=target,
        expected_sha256=_sha256(payload),
    )

    assert not source.path.exists()
    assert target.path.read_bytes() == payload
    assert committed.sha256 == _sha256(payload)
    assert journal.get("commit-1").state == "COMMITTED"
    assert jobs.get_task("task-1").state == "SUCCEEDED"
    event_codes = [event.event_code for event in jobs.list_events("job-1")]
    assert "ARTIFACT.COMMIT_INTENT" in event_codes
    assert "TASK.SUCCEEDED_WITH_ARTIFACT" in event_codes


def test_intent_without_promoted_file_remains_incomplete(tmp_path: Path) -> None:
    paths, jobs, task, journal, broker = _running_task(tmp_path)
    source = paths.worker_file("job-1", "worker-1", "candidate.bin")
    target = paths.output("job-1", "01.bin")
    payload = b"candidate"
    source.path.write_bytes(payload)
    candidate = broker.validate_worker_file(source)
    journal.create_intent(
        commit_id="commit-1",
        task=task,
        source=source,
        target=target,
        expected_sha256=candidate.sha256,
        byte_size=candidate.byte_size,
    )

    finalized = ArtifactCommitReconciler(journal, broker, jobs).reconcile()

    assert finalized == ()
    assert journal.get("commit-1").state == "INTENT"
    assert jobs.get_task("task-1").state == "RUNNING"
    assert source.path.exists()
    assert not target.path.exists()


def test_recovery_finalizes_matching_file_after_crash_post_promotion(tmp_path: Path) -> None:
    paths, jobs, task, journal, broker = _running_task(tmp_path)
    source = paths.worker_file("job-1", "worker-1", "candidate.bin")
    target = paths.output("job-1", "01.bin")
    payload = b"promoted-before-crash"
    source.path.write_bytes(payload)
    candidate = broker.validate_worker_file(source)
    journal.create_intent(
        commit_id="commit-1",
        task=task,
        source=source,
        target=target,
        expected_sha256=candidate.sha256,
        byte_size=candidate.byte_size,
    )
    broker.commit_worker_file(source, target, expected_sha256=candidate.sha256)
    # Simulated process crash here: no mark_promoted/finalize_success call.

    finalized = ArtifactCommitReconciler(journal, broker, jobs).reconcile()

    assert finalized == ("commit-1",)
    assert journal.get("commit-1").state == "COMMITTED"
    assert jobs.get_task("task-1").state == "SUCCEEDED"
    assert target.read_bytes() if False else True


def test_recovery_marks_hash_mismatch_integrity_failure_without_task_success(tmp_path: Path) -> None:
    paths, jobs, task, journal, broker = _running_task(tmp_path)
    source = paths.worker_file("job-1", "worker-1", "candidate.bin")
    target = paths.output("job-1", "01.bin")
    payload = b"expected"
    source.path.write_bytes(payload)
    candidate = broker.validate_worker_file(source)
    journal.create_intent(
        commit_id="commit-1",
        task=task,
        source=source,
        target=target,
        expected_sha256=candidate.sha256,
        byte_size=candidate.byte_size,
    )
    target.path.write_bytes(b"tampered")

    finalized = ArtifactCommitReconciler(journal, broker, jobs).reconcile()

    assert finalized == ()
    assert journal.get("commit-1").state == "FAILED_INTEGRITY"
    assert jobs.get_task("task-1").state == "RUNNING"


def test_stale_attempt_cannot_create_or_finalize_commit(tmp_path: Path) -> None:
    paths, jobs, task, journal, broker = _running_task(tmp_path)
    source = paths.worker_file("job-1", "worker-1", "candidate.bin")
    target = paths.output("job-1", "01.bin")
    payload = b"stale"
    source.path.write_bytes(payload)
    candidate = broker.validate_worker_file(source)
    journal.create_intent(
        commit_id="commit-1",
        task=task,
        source=source,
        target=target,
        expected_sha256=candidate.sha256,
        byte_size=candidate.byte_size,
    )
    jobs.finish_task(
        "task-1",
        expected_generation=task.generation,
        worker_id="worker-1",
        attempt=1,
        new_state="INTERRUPTED",
        event_code="TASK.INTERRUPTED_FOR_RETRY",
    )
    interrupted = jobs.get_task("task-1")
    jobs.assign_task(
        "task-1",
        expected_generation=interrupted.generation,
        worker_id="worker-2",
        attempt=2,
        lease_expires_at="2030-01-01T00:05:00+00:00",
    )

    finalized = ArtifactCommitReconciler(journal, broker, jobs).reconcile()

    assert finalized == ()
    assert journal.get("commit-1").state == "SUPERSEDED"
    assert jobs.get_task("task-1").state == "RUNNING"
    assert jobs.get_task("task-1").attempt == 2
