"""Пакетный анализ папки фотографий."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from portrait_core.pipeline import analyze_photo
from portrait_core.reporting import save_report


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def analyze_directory(
    input_directory: str,
    output_directory: str,
    model_path: str,
) -> list[dict]:
    """Проанализировать изображения и сохранить отчеты с общей сводкой."""
    source = Path(input_directory)
    destination = Path(output_directory)
    if not source.is_dir():
        raise NotADirectoryError(f"Папка не найдена: {source}")
    destination.mkdir(parents=True, exist_ok=True)

    rows = []
    seen_hashes = {}
    images = sorted(
        path for path in source.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES
    )
    for image_path in images:
        row = {
            "image": image_path.name,
            "status": "error",
            "issues": "",
            "duplicate_of": "",
        }
        digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if digest in seen_hashes:
            row.update(
                {
                    "status": "duplicate",
                    "issues": "точная копия другого файла",
                    "duplicate_of": seen_hashes[digest],
                }
            )
            rows.append(row)
            continue
        seen_hashes[digest] = image_path.name

        try:
            _, report = analyze_photo(str(image_path), model_path)
            report_path = destination / f"{image_path.stem}_portrait.json"
            save_report(report, report_path)
            quality = report["quality"]
            row.update(
                {
                    "status": quality["status"],
                    "issues": "; ".join(quality["issues"]),
                    "face_proportion": report["morphology"]["face_proportion"],
                    "symmetry": report["morphology"]["symmetry"],
                    "report": report_path.name,
                }
            )
        except Exception as error:
            row["issues"] = str(error)
        rows.append(row)

    (destination / "summary.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    fieldnames = [
        "image",
        "status",
        "issues",
        "duplicate_of",
        "face_proportion",
        "symmetry",
        "report",
    ]
    with (destination / "summary.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Пакетный анализ фотографий")
    parser.add_argument("input_directory", help="Папка с фотографиями")
    parser.add_argument("output_directory", help="Папка для отчетов")
    parser.add_argument(
        "--model",
        default="portrait_core/models/face_landmarker.task",
        help="Путь к модели MediaPipe",
    )
    return parser


def main():
    args = build_parser().parse_args()
    rows = analyze_directory(
        args.input_directory,
        args.output_directory,
        args.model,
    )
    successful = sum(bool(row.get("report")) for row in rows)
    print(f"Обработано: {len(rows)}; отчеты созданы: {successful}")


if __name__ == "__main__":
    main()
