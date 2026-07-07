"""CLI: validate a Profile Dataset Archive."""

from __future__ import annotations

import argparse
import json
import sys

from portrait_core.archive.validation import validate_dataset_archive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a Profile Dataset Archive")
    parser.add_argument("dataset", help="DS-* directory or dataset.json")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = validate_dataset_archive(args.dataset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("valid") else 1)


if __name__ == "__main__":
    main()
