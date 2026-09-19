from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image

from .models import FileInspection

_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_image(path: str | Path) -> FileInspection:
    source = Path(path).expanduser().resolve(strict=True)
    before_hash = sha256_file(source)

    with Image.open(source) as image:
        image.load()
        fmt = image.format or "UNKNOWN"
        width, height = image.size
        mode = image.mode

        has_alpha = "A" in image.getbands() or "transparency" in image.info
        alpha_min: int | None = None
        alpha_max: int | None = None
        transparent_ratio: float | None = None

        if has_alpha:
            alpha = image.convert("RGBA").getchannel("A")
            alpha_min, alpha_max = alpha.getextrema()
            histogram = alpha.histogram()
            pixel_count = width * height
            transparent_ratio = float((pixel_count - histogram[255]) / pixel_count)

    after_hash = sha256_file(source)
    if before_hash != after_hash:
        raise RuntimeError("Source file changed during inspection")

    return FileInspection(
        path=source,
        format=fmt,
        width=width,
        height=height,
        mode=mode,
        has_alpha=has_alpha,
        alpha_min=alpha_min,
        alpha_max=alpha_max,
        transparent_pixel_ratio=transparent_ratio,
        sha256=before_hash,
    )
