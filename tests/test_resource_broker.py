import hashlib
from pathlib import Path

import pytest

from mtkrita.path_manager import PathManager
from mtkrita.resource_broker import ResourceBroker


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_broker_stages_input_without_mutating_external_source(tmp_path: Path) -> None:
    manager = PathManager(tmp_path / "workspace")
    manager.prepare_job("job-1")
    external = tmp_path / "source.png"
    payload = b"source-png-bytes"
    external.write_bytes(payload)
    target = manager.input("job-1", "frame-001.png")

    staged = ResourceBroker(manager).stage_input_file(
        external,
        target,
        expected_sha256=_sha256(payload),
    )

    assert external.read_bytes() == payload
    assert target.path.read_bytes() == payload
    assert staged.target == target
    assert staged.sha256 == _sha256(payload)
    assert staged.byte_size == len(payload)


def test_broker_refuses_staged_input_overwrite(tmp_path: Path) -> None:
    manager = PathManager(tmp_path / "workspace")
    manager.prepare_job("job-1")
    external = tmp_path / "source.png"
    external.write_bytes(b"new")
    target = manager.input("job-1", "frame-001.png")
    target.path.write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        ResourceBroker(manager).stage_input_file(external, target)

    assert external.read_bytes() == b"new"
    assert target.path.read_bytes() == b"existing"


def test_broker_rejects_input_hash_mismatch_without_staging(tmp_path: Path) -> None:
    manager = PathManager(tmp_path / "workspace")
    manager.prepare_job("job-1")
    external = tmp_path / "source.png"
    external.write_bytes(b"source")
    target = manager.input("job-1", "frame-001.png")

    with pytest.raises(ValueError, match="input hash mismatch"):
        ResourceBroker(manager).stage_input_file(external, target, expected_sha256="0" * 64)

    assert external.read_bytes() == b"source"
    assert not target.path.exists()


def test_broker_verifies_staged_input_hash_and_size(tmp_path: Path) -> None:
    manager = PathManager(tmp_path / "workspace")
    manager.prepare_job("job-1")
    payload = b"input"
    target = manager.input("job-1", "frame-001.png")
    target.path.write_bytes(payload)
    broker = ResourceBroker(manager)

    verified = broker.verify_input_file(
        target,
        expected_sha256=_sha256(payload),
        expected_byte_size=len(payload),
    )

    assert verified.sha256 == _sha256(payload)
    assert verified.byte_size == len(payload)
    with pytest.raises(ValueError, match="byte-size"):
        broker.verify_input_file(
            target,
            expected_sha256=_sha256(payload),
            expected_byte_size=len(payload) + 1,
        )
    with pytest.raises(ValueError, match="hash mismatch"):
        broker.verify_input_file(target, expected_sha256="f" * 64)


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

    with pytest.raises(ValueError, match="cross-job"):
        ResourceBroker(manager).commit_worker_file(source, target)


def test_broker_rejects_hash_mismatch_without_moving_file(tmp_path: Path) -> None:
    manager = PathManager(tmp_path)
    manager.prepare_job("job-1")
    manager.prepare_worker_scratch("job-1", "worker-1")
    source = manager.worker_file("job-1", "worker-1", "candidate.bin")
    target = manager.output("job-1", "01.png")
    source.path.write_bytes(b"data")

    with pytest.raises(ValueError, match="hash mismatch"):
        ResourceBroker(manager).commit_worker_file(source, target, expected_sha256="0" * 64)

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

    with pytest.raises(FileExistsError):
        ResourceBroker(manager).commit_worker_file(source, target)

    assert source.path.read_bytes() == b"new"
    assert target.path.read_bytes() == b"old"
