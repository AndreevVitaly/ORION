"""CLI entrypoint for Profile geometric invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from portrait_core.invariants.invariant_export import build_invariants_for_portrait
from portrait_core.invariants.invariant_stats import build_invariant_stats


def _collect_inputs(input_path: str) -> list[Path]:
    path = Path(input_path)
    if path.is_dir():
        return sorted(item for item in path.glob("*.json") if item.is_file())
    return [path]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Profile geometric invariant engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build invariants.json from PFR")
    build.add_argument("--pfr", required=True, help="Path to portrait.json/PFR")
    build.add_argument("--output", help="Output invariants.json path")

    stats = subparsers.add_parser("stats", help="Build invariant stability stats")
    stats.add_argument("--input", required=True, help="invariants.json path or directory")
    stats.add_argument("--output", help="Output stats JSON path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "build":
        payload = build_invariants_for_portrait(args.pfr, args.output)
    else:
        payload = build_invariant_stats(_collect_inputs(args.input), args.output)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
