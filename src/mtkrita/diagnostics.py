from __future__ import annotations

import json
import platform
import sys
import zipfile
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from .job_store import JobStore
from .path_manager import PathManager, PathRef

_SENSITIVE_KEY_PARTS = ("password", "passwd", "secret", "token", "api_key", "apikey", "credential")


@dataclass(frozen=True)
class DiagnosticBundleResult:
    target: PathRef
    included_files: tuple[str, ...]


class DiagnosticBundleBuilder:
    """Build a read-only, non-secret diagnostic ZIP without including source images."""

    def __init__(self, paths: PathManager, jobs: JobStore) -> None:
        self._paths = paths
        self._jobs = jobs

    def build(
        self,
        job_id: str,
        *,
        filename: str = "diagnostics.zip",
        effective_config: dict[str, Any] | None = None,
    ) -> DiagnosticBundleResult:
        job = self._jobs.get_job(job_id)
        tasks = self._jobs.list_tasks(job_id)
        events = self._jobs.list_events(job_id)
        target = self._paths.evidence(job_id, filename)
        target_path = self._paths.assert_owned(target.path)
        if not target_path.parent.is_dir():
            raise ValueError("job evidence directory is not prepared")
        if target_path.exists():
            raise FileExistsError(target_path)

        entries: dict[str, bytes] = {
            "job.json": self._json_bytes(asdict(job)),
            "tasks.json": self._json_bytes([asdict(task) for task in tasks]),
            "events.json": self._json_bytes([asdict(event) for event in events]),
            "environment.json": self._json_bytes(self._environment_summary()),
        }
        if effective_config is not None:
            entries["effective_config_redacted.json"] = self._json_bytes(
                self._redact(effective_config)
            )

        log_path = self._paths.log(job_id).path
        if log_path.is_file():
            entries["events.jsonl"] = log_path.read_bytes()

        with zipfile.ZipFile(
            target_path,
            mode="x",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as archive:
            for name in sorted(entries):
                archive.writestr(name, entries[name])

        return DiagnosticBundleResult(
            target=target,
            included_files=tuple(sorted(entries)),
        )

    @classmethod
    def _redact(cls, value: Any, key: str | None = None) -> Any:
        if key is not None and any(part in key.lower() for part in _SENSITIVE_KEY_PARTS):
            return "<redacted>"
        if isinstance(value, dict):
            return {str(k): cls._redact(v, str(k)) for k, v in value.items()}
        if isinstance(value, list):
            return [cls._redact(item) for item in value]
        if isinstance(value, tuple):
            return [cls._redact(item) for item in value]
        return value

    @staticmethod
    def _json_bytes(value: Any) -> bytes:
        return (
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n"
        ).encode("utf-8")

    @staticmethod
    def _environment_summary() -> dict[str, Any]:
        try:
            app_version = version("mtkrita")
        except PackageNotFoundError:
            app_version = "unknown"
        return {
            "mtkrita_version": app_version,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "python_implementation": platform.python_implementation(),
        }
