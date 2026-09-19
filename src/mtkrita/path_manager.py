from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


_SAFE_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)


class PathKind(StrEnum):
    JOB_ROOT = "job_root"
    WORKER_SCRATCH = "worker_scratch"
    OUTPUT = "output"
    EVIDENCE = "evidence"
    LOG = "log"


@dataclass(frozen=True)
class PathRef:
    kind: PathKind
    path: Path
    job_id: str
    worker_id: str | None = None


class PathManager:
    """Resolve MTKrita-owned runtime paths from one trusted workspace root."""

    def __init__(self, workspace_root: str | Path) -> None:
        self._root = Path(workspace_root).expanduser().resolve()

    @property
    def workspace_root(self) -> Path:
        return self._root

    @staticmethod
    def _validate_id(value: str, label: str) -> str:
        if not value or value in {".", ".."} or any(ch not in _SAFE_ID_CHARS for ch in value):
            raise ValueError(f"invalid {label}")
        return value

    @staticmethod
    def _validate_filename(filename: str) -> str:
        candidate = Path(filename)
        if not filename or candidate.name != filename or filename in {".", ".."}:
            raise ValueError("filename must be a single path component")
        if "\x00" in filename:
            raise ValueError("filename contains NUL")
        return filename

    def _job_root_path(self, job_id: str) -> Path:
        safe_job = self._validate_id(job_id, "job_id")
        return self._root / "jobs" / safe_job

    def job_root(self, job_id: str) -> PathRef:
        return PathRef(PathKind.JOB_ROOT, self._job_root_path(job_id), job_id)

    def worker_scratch(self, job_id: str, worker_id: str) -> PathRef:
        safe_worker = self._validate_id(worker_id, "worker_id")
        return PathRef(
            PathKind.WORKER_SCRATCH,
            self._job_root_path(job_id) / "scratch" / safe_worker,
            job_id,
            safe_worker,
        )

    def worker_file(self, job_id: str, worker_id: str, filename: str) -> PathRef:
        directory = self.worker_scratch(job_id, worker_id)
        safe_name = self._validate_filename(filename)
        return PathRef(
            PathKind.WORKER_SCRATCH,
            directory.path / safe_name,
            job_id,
            directory.worker_id,
        )

    def output(self, job_id: str, filename: str) -> PathRef:
        safe_name = self._validate_filename(filename)
        return PathRef(PathKind.OUTPUT, self._job_root_path(job_id) / "outputs" / safe_name, job_id)

    def evidence(self, job_id: str, filename: str) -> PathRef:
        safe_name = self._validate_filename(filename)
        return PathRef(
            PathKind.EVIDENCE,
            self._job_root_path(job_id) / "evidence" / safe_name,
            job_id,
        )

    def log(self, job_id: str, filename: str = "events.jsonl") -> PathRef:
        safe_name = self._validate_filename(filename)
        return PathRef(PathKind.LOG, self._job_root_path(job_id) / "logs" / safe_name, job_id)

    def prepare_job(self, job_id: str) -> PathRef:
        root = self.job_root(job_id)
        for name in ("outputs", "evidence", "logs", "scratch"):
            (root.path / name).mkdir(parents=True, exist_ok=True)
        return root

    def prepare_worker_scratch(self, job_id: str, worker_id: str) -> PathRef:
        ref = self.worker_scratch(job_id, worker_id)
        ref.path.mkdir(parents=True, exist_ok=True)
        return ref

    def assert_owned(self, path: str | Path) -> Path:
        resolved = Path(path).expanduser().resolve()
        try:
            resolved.relative_to(self._root)
        except ValueError as exc:
            raise ValueError("path is outside MTKrita workspace") from exc
        return resolved
