from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .inspector import inspect_image
from .manifest import create_manifest, write_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mtkrita", description="MTKrita sticker automation engine")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_cmd = sub.add_parser("inspect", help="Inspect an image without modifying it")
    inspect_cmd.add_argument("input", type=Path)
    inspect_cmd.add_argument("--json", action="store_true", dest="as_json")

    init_cmd = sub.add_parser("init-job", help="Create a job manifest for an input image")
    init_cmd.add_argument("input", type=Path)
    init_cmd.add_argument("--output", type=Path, required=True)

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "inspect":
        result = inspect_image(args.input)
        payload = asdict(result)
        payload["path"] = str(payload["path"])
        if args.as_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for key, value in payload.items():
                print(f"{key}: {value}")
        return 0

    if args.command == "init-job":
        manifest = create_manifest(args.input)
        target = write_manifest(manifest, args.output)
        print(target)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
