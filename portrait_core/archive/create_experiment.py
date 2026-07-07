"""CLI: create a Profile Experiment record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from portrait_core.archive.experiment import create_experiment_record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a Profile Experiment record")
    parser.add_argument("datasets", nargs="*", help="Dataset ids or DS-* paths")
    parser.add_argument("--output", help="Output directory. Defaults to first dataset/experiments when possible.")
    parser.add_argument("--method", default="custom")
    parser.add_argument("--id", dest="experiment_id")
    parser.add_argument("--notes", default="")
    return parser


def _dataset_ids(values: list[str]) -> list[str]:
    result = []
    for value in values:
        path = Path(value)
        result.append(path.name if path.name.startswith("DS-") else value)
    return result


def _default_output(values: list[str], output: str | None) -> Path:
    if output:
        return Path(output)
    if values:
        first = Path(values[0])
        if first.exists() and first.is_dir():
            return first / "experiments"
    return Path("experiments")


def main() -> None:
    args = build_parser().parse_args()
    experiment_dir, experiment = create_experiment_record(
        _default_output(args.datasets, args.output),
        datasets=_dataset_ids(args.datasets),
        method=args.method,
        notes=args.notes,
        experiment_id=args.experiment_id,
    )
    print(json.dumps({"experiment_dir": str(experiment_dir), "experiment": experiment}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
