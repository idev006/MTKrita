from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from . import __version__
from .inspector import inspect_image
from .models import JobManifest


def stable_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def create_manifest(input_path: str | Path, config_text: str = "") -> JobManifest:
    inspection = inspect_image(input_path)
    return JobManifest(
        job_id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        input_file=str(inspection.path),
        input_hash=inspection.sha256,
        engine_version=__version__,
        config_hash=stable_text_hash(config_text) if config_text else None,
    )


def write_manifest(manifest: JobManifest, output_dir: str | Path) -> Path:
    target_dir = Path(output_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "manifest.json"
    target.write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return target
