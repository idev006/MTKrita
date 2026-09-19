import hashlib
from pathlib import Path

from mtkrita.path_manager import PathManager
from mtkrita.resource_broker import ResourceBroker


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_broker_promotes_worker_file_to_output(tmp_path: Path) -> None:
    manager = PathManager(tmp_path)
    manager.prepare_job("job-1")
    manager.prepare_worker_scratch("job-1", "worker-1")
    source = manager.worker_file("job-1", "worker-1", "candidate.png")
    target = manager.output("job-1", "01.png")
    payload = b"png-candidate-bytes"
    source.path.write_bytes(payload)

    artifact = ResourceBroker(manager).commit_worker_file(
        source,
        target,
        expected_sha256=_sha256(payload),
    )

    assert not source.path.exists()
    assert target.path.read_bytes() == payload
    assert artifact.sha256 == _sha256(payload)
    assert artifact.byte_size == len(payload)
    assert artifact.worker_id == "worker-1"


def test_broker_rejects_cross_job_commit(tmp_path: Path) -> None:
    manager = PathManager(tmp_path)
    manager.prepare_job("job-1")
    manager.prepare_job("job-2")
    manager.prepare_worker_scratch("job-1", "worker-1")
    source = manager.worker_file("job-1", "worker-1", "candidate.bin")
    target = manager.output("job-2", "01.png")
    source.path.write_bytes(b"data")

    try:
        ResourceBroker(manager).commit_worker_file(source, target)
    except ValueError as exc:
        assert "cross-job" in str(exc)
    else:
        raise AssertionError("expected cross-job commit rejection")


def test_broker_rejects_hash_mismatch_without_moving_file(tmp_path: Path) -> None:
    manager = PathManager(tmp_path)
    manager.prepare_job("job-1")
    manager.prepare_worker_scratch("job-1", "worker-1")
    source = manager.worker_file("job-1", "worker-1", "candidate.bin")
    target = manager.output("job-1", "01.png")
    source.path.write_bytes(b"data")

    try:
        ResourceBroker(manager).commit_worker_file(source, target, expected_sha256="0" * 64)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("expected hash mismatch rejection")

    assert source.path.exists()
    assert not target.path.exists()


def test_broker_refuses_existing_authoritative_target(tmp_path: Path) -> None:
    manager = PathManager(tmp_path)
    manager.prepare_job("job-1")
    manager.prepare_worker_scratch("job-1", "worker-1")
    source = manager.worker_file("job-1", "worker-1", "candidate.bin")
    target = manager.output("job-1", "01.png")
    source.path.write_bytes(b"new")
    target.path.write_bytes(b"old")

    try:
        ResourceBroker(manager).commit_worker_file(source, target)
    except FileExistsError:
        pass
    else:
        raise AssertionError("expected existing-target rejection")

    assert source.path.read_bytes() == b"new"
    assert target.path.read_bytes() == b"old"
