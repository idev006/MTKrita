from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from .path_manager import PathKind, PathManager, PathRef


@dataclass(frozen=True)
class CandidateArtifact:
    source: PathRef
    sha256: str
    byte_size: int
    worker_id: str


@dataclass(frozen=True)
class CommittedArtifact:
    target: PathRef
    sha256: str
    byte_size: int
    worker_id: str


@dataclass(frozen=True)
class StagedInput:
    target: PathRef
    sha256: str
    byte_size: int


class ResourceBroker:
    """Centralize immutable input staging and authoritative artifact promotion."""

    def __init__(self, path_manager: PathManager) -> None:
        self._paths = path_manager

    @staticmethod
    def _sha256(path: str | Path) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def stage_input_file(
        self,
        source_path: str | Path,
        target: PathRef,
        *,
        expected_sha256: str | None = None,
    ) -> StagedInput:
        """Copy an external/control-plane source into the immutable job input namespace."""
        if target.kind != PathKind.INPUT or target.worker_id is not None:
            raise ValueError("target must be a non-worker INPUT reference")
        source = Path(source_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.is_symlink():
            raise ValueError("staged input source must not be a symlink")

        target_path = self._paths.assert_owned(target.path)
        if not target_path.parent.is_dir():
            raise ValueError("input target parent directory is not prepared")
        if target_path.exists():
            raise FileExistsError(target_path)

        temp = target_path.with_name(f".{target_path.name}.{uuid4().hex}.staging")
        try:
            with source.open("rb") as reader, temp.open("xb") as writer:
                shutil.copyfileobj(reader, writer, length=1024 * 1024)
                writer.flush()
                os.fsync(writer.fileno())
            digest = self._sha256(temp)
            if expected_sha256 is not None and digest != expected_sha256:
                raise ValueError("input hash mismatch")
            byte_size = temp.stat().st_size
            if target_path.exists():
                raise FileExistsError(target_path)
            os.replace(temp, target_path)
            return StagedInput(target=target, sha256=digest, byte_size=byte_size)
        finally:
            if temp.exists():
                temp.unlink()

    def verify_input_file(
        self,
        source: PathRef,
        *,
        expected_sha256: str,
        expected_byte_size: int | None = None,
    ) -> StagedInput:
        if source.kind != PathKind.INPUT or source.worker_id is not None:
            raise ValueError("source must be a non-worker INPUT reference")
        source_path = self._paths.assert_owned(source.path)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        if source_path.is_symlink():
            raise ValueError("staged input must not be a symlink")
        byte_size = source_path.stat().st_size
        if expected_byte_size is not None and byte_size != expected_byte_size:
            raise ValueError("input byte-size mismatch")
        digest = self._sha256(source_path)
        if digest != expected_sha256:
            raise ValueError("input hash mismatch")
        return StagedInput(target=source, sha256=digest, byte_size=byte_size)

    def validate_worker_file(
        self,
        source: PathRef,
        *,
        expected_sha256: str | None = None,
    ) -> CandidateArtifact:
        if source.kind != PathKind.WORKER_SCRATCH or source.worker_id is None:
            raise ValueError("source must be a worker scratch file")
        source_path = self._paths.assert_owned(source.path)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        digest = self._sha256(source_path)
        if expected_sha256 is not None and digest != expected_sha256:
            raise ValueError("artifact hash mismatch")
        return CandidateArtifact(
            source=source,
            sha256=digest,
            byte_size=source_path.stat().st_size,
            worker_id=source.worker_id,
        )

    def verify_authoritative_file(
        self,
        target: PathRef,
        *,
        expected_sha256: str,
        expected_byte_size: int | None = None,
    ) -> CommittedArtifact:
        if target.kind not in {PathKind.OUTPUT, PathKind.EVIDENCE}:
            raise ValueError("target must be output or evidence")
        target_path = self._paths.assert_owned(target.path)
        if not target_path.is_file():
            raise FileNotFoundError(target_path)
        byte_size = target_path.stat().st_size
        if expected_byte_size is not None and byte_size != expected_byte_size:
            raise ValueError("artifact byte-size mismatch")
        digest = self._sha256(target_path)
        if digest != expected_sha256:
            raise ValueError("artifact hash mismatch")
        return CommittedArtifact(
            target=target,
            sha256=digest,
            byte_size=byte_size,
            worker_id="control-plane",
        )

    def commit_worker_file(
        self,
        source: PathRef,
        target: PathRef,
        *,
        expected_sha256: str | None = None,
    ) -> CommittedArtifact:
        candidate = self.validate_worker_file(source, expected_sha256=expected_sha256)
        if target.kind not in {PathKind.OUTPUT, PathKind.EVIDENCE}:
            raise ValueError("target must be output or evidence")
        if source.job_id != target.job_id:
            raise ValueError("cross-job artifact commit is prohibited")

        source_path = self._paths.assert_owned(source.path)
        target_path = self._paths.assert_owned(target.path)
        if target_path.exists():
            raise FileExistsError(target_path)
        if not target_path.parent.is_dir():
            raise ValueError("target parent directory is not prepared")

        os.replace(source_path, target_path)
        return CommittedArtifact(
            target=target,
            sha256=candidate.sha256,
            byte_size=candidate.byte_size,
            worker_id=candidate.worker_id,
        )
