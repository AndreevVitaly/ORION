"""Анализ повторяемости по серии готовых JSON-отчетов."""

import argparse
import json
from pathlib import Path

from portrait_core.stability import build_series_profile


def analyze_report_directory(
    directory: str,
    subject_label: str | None = None,
) -> dict:
    """Загрузить отчеты из папки и рассчитать стабильность признаков."""
    source = Path(directory)
    reports = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(source.glob("*_portrait.json"))
    ]
    return build_series_profile(reports, subject_label=subject_label)


def main():
    parser = argparse.ArgumentParser(
        description="Оценка стабильности признаков по серии отчетов"
    )
    parser.add_argument("report_directory")
    parser.add_argument("--output")
    parser.add_argument("--subject")
    args = parser.parse_args()

    result = analyze_report_directory(args.report_directory, args.subject)
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(serialized, encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
