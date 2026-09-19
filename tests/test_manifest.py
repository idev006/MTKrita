import json
from pathlib import Path

from PIL import Image

from mtkrita.manifest import create_manifest, write_manifest


def test_manifest_captures_input_hash_and_writes_json(tmp_path: Path) -> None:
    source = tmp_path / "sheet.png"
    Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(source)

    manifest = create_manifest(source, config_text="mode: auto\n")
    target = write_manifest(manifest, tmp_path / "job")

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["input_file"] == str(source.resolve())
    assert len(payload["input_hash"]) == 64
    assert len(payload["config_hash"]) == 64
    assert payload["frames"] == []
