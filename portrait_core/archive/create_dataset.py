"""CLI: create a Profile Dataset Archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from portrait_core.archive.dataset import create_dataset_archive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an empty Profile Dataset Archive")
    parser.add_argument("output_root", help="Output root or explicit DS-* directory")
    parser.add_argument("--source")
    parser.add_argument("--id", dest="dataset_id")
    parser.add_argument("--setting", action="append", default=[], help="key=value setting")
    return parser


def _settings(values: list[str]) -> dict[str, str]:
    result = {}
    for value in values:
        if "=" in value:
            key, item = value.split("=", 1)
            result[key] = item
    return result


def main() -> None:
    args = build_parser().parse_args()
    dataset_dir, dataset = create_dataset_archive(
        args.output_root,
        source=args.source,
        settings=_settings(args.setting),
        dataset_id=args.dataset_id,
    )
    print(json.dumps({"dataset_dir": str(Path(dataset_dir)), "dataset": dataset}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
