from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from .path_manager import PathKind, PathManager, PathRef


@dataclass(frozen=True)
class CommittedArtifact:
    target: PathRef
    sha256: str
    byte_size: int
    worker_id: str


class ResourceBroker:
    """Centralize promotion of worker artifacts into shared authoritative locations."""

    def __init__(self, path_manager: PathManager) -> None:
        self._paths = path_manager

    @staticmethod
    def _sha256(path: str) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def commit_worker_file(
        self,
        source: PathRef,
        target: PathRef,
        *,
        expected_sha256: str | None = None,
    ) -> CommittedArtifact:
        if source.kind != PathKind.WORKER_SCRATCH or source.worker_id is None:
            raise ValueError("source must be a worker scratch file")
        if target.kind not in {PathKind.OUTPUT, PathKind.EVIDENCE}:
            raise ValueError("target must be output or evidence")
        if source.job_id != target.job_id:
            raise ValueError("cross-job artifact commit is prohibited")

        source_path = self._paths.assert_owned(source.path)
        target_path = self._paths.assert_owned(target.path)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        if target_path.exists():
            raise FileExistsError(target_path)
        if not target_path.parent.is_dir():
            raise ValueError("target parent directory is not prepared")

        digest = self._sha256(str(source_path))
        if expected_sha256 is not None and digest != expected_sha256:
            raise ValueError("artifact hash mismatch")

        byte_size = source_path.stat().st_size
        os.replace(source_path, target_path)
        return CommittedArtifact(
            target=target,
            sha256=digest,
            byte_size=byte_size,
            worker_id=source.worker_id,
        )
