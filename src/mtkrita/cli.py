from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .inspector import inspect_image
from .manifest import create_manifest, write_manifest
from .sheet_pipeline import process_sheet_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mtkrita", description="MTKrita sticker automation engine")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_cmd = sub.add_parser("inspect", help="Inspect an image without modifying it")
    inspect_cmd.add_argument("input", type=Path)
    inspect_cmd.add_argument("--json", action="store_true", dest="as_json")

    init_cmd = sub.add_parser("init-job", help="Create a job manifest for an input image")
    init_cmd.add_argument("input", type=Path)
    init_cmd.add_argument("--output", type=Path, required=True)

    sheet_cmd = sub.add_parser(
        "process-sheet",
        help="Split a 2x5 sticker sheet, remove supported borders/background, and export frames",
    )
    sheet_cmd.add_argument("input", type=Path)
    sheet_cmd.add_argument("--output", type=Path, required=True)
    sheet_cmd.add_argument("--start-number", type=int, default=1)
    sheet_cmd.add_argument("--overwrite", action="store_true")

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

    if args.command == "process-sheet":
        result = process_sheet_file(
            args.input,
            args.output,
            start_number=args.start_number,
            allow_overwrite=args.overwrite,
        )
        print(json.dumps(asdict(result.summary), ensure_ascii=False, indent=2))
        return 0 if result.summary.review_count == 0 and result.summary.fail_count == 0 else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
