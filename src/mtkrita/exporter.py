from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image


@dataclass(frozen=True)
class ExportArtifact:
    path: Path
    sha256: str
    byte_size: int


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_png_atomic(
    image: Image.Image,
    target_path: str | Path,
    *,
    allow_overwrite: bool = False,
) -> ExportArtifact:
    """Write a PNG atomically to a pre-resolved target path.

    Path selection/ownership belongs to PathManager/ResourceBroker. This function
    only commits bytes to the supplied final target and refuses overwrite by default.
    """
    target = Path(target_path)
    if target.suffix.lower() != ".png":
        raise ValueError("target path must use .png extension")
    if not target.parent.exists() or not target.parent.is_dir():
        raise ValueError("target parent directory must already exist")
    if target.exists() and not allow_overwrite:
        raise FileExistsError(target)

    temp = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    try:
        image.convert("RGBA").save(temp, format="PNG")
        artifact_hash = _sha256_file(temp)
        byte_size = temp.stat().st_size
        if target.exists() and not allow_overwrite:
            raise FileExistsError(target)
        os.replace(temp, target)
        return ExportArtifact(path=target, sha256=artifact_hash, byte_size=byte_size)
    finally:
        if temp.exists():
            temp.unlink()


def bind_export_artifact(frame_result: object, artifact: ExportArtifact) -> None:
    """Attach final artifact lineage to a mutable FrameResult-like object."""
    if not hasattr(frame_result, "output_file") or not hasattr(frame_result, "output_sha256"):
        raise TypeError("frame_result does not expose output lineage fields")
    frame_result.output_file = str(artifact.path)
    frame_result.output_sha256 = artifact.sha256
