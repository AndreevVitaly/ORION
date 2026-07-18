"""Dataset Builder: подготовка кадров и запуск portrait_core.

Модуль намеренно не вычисляет landmarks, morphology, measurements, LIC или
quality самостоятельно. Единственный источник геометрической истины —
portrait_core.create_portrait_report().
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urlparse

from portrait_core import create_portrait_report
from portrait_core.archive.common import as_posix, make_record_id, new_uuid, write_json
from portrait_core.archive.dataset import create_dataset_archive, write_dataset_files


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
URL_SCHEMES = {"http", "https"}
LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int], None]
StopCallback = Callable[[], bool]


class StopRequested(RuntimeError):
    """Остановка сборки датасета по запросу пользователя."""


def _iter_images(path: Path) -> Iterable[Path]:
    if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
        yield path
        return
    if path.is_dir():
        for file_path in sorted(path.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_SUFFIXES:
                yield file_path



def is_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme.lower() in URL_SCHEMES and bool(parsed.netloc)


def download_video_source(
    url: str,
    downloads_dir: Path,
    *,
    log: LogCallback | None = None,
    should_stop: StopCallback | None = None,
) -> Path:
    if should_stop and should_stop():
        raise StopRequested("Остановлено пользователем")

    downloads_dir.mkdir(parents=True, exist_ok=True)
    token = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    output_template = downloads_dir / f"source-{token}.%(ext)s"
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--newline",
        "--progress",
        "--socket-timeout",
        "30",
        "--retries",
        "3",
        "-f",
        "bestvideo[height<=720][ext=mp4]/best[height<=720][ext=mp4]/bestvideo[height<=720]/best[height<=720]/bestvideo[ext=mp4]/bestvideo/best",
        "-o",
        str(output_template),
        url,
    ]
    if log:
        log(f"Скачивание видео по URL: {url}")

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output_lines: list[str] = []
    try:
        assert process.stdout is not None
        for line in process.stdout:
            line = line.strip()
            if line:
                output_lines.append(line)
                if log:
                    log(line)
            if should_stop and should_stop():
                process.terminate()
                raise StopRequested("Остановлено пользователем")
        return_code = process.wait()
    finally:
        if process.poll() is None:
            process.terminate()

    if return_code != 0:
        output = "\n".join(output_lines[-20:]).strip()
        if "No module named yt_dlp" in output:
            raise RuntimeError(
                "Для скачивания URL требуется yt-dlp. Установите зависимости: "
                "python -m pip install -r requirements.txt"
            )
        raise RuntimeError(f"Не удалось скачать видео по URL: {output or url}")

    candidates = sorted(
        (
            path
            for path in downloads_dir.glob(f"source-{token}.*")
            if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
        ),
        key=lambda path: (path.suffix.lower() != ".mp4", -path.stat().st_mtime),
    )
    for candidate in candidates:
        if not _is_readable_video(candidate):
            if log:
                log(f"Пропуск не-видео потока: {candidate.name}")
            continue
        write_json(
            downloads_dir / f"source-{token}.json",
            {
                "source_url": url,
                "downloaded_path": str(candidate),
                "tool": "yt-dlp",
                "format": "video-only mp4 up to 720p preferred",
            },
        )
        if log:
            log(f"Видео скачано: {candidate.name}")
        return candidate

    raise RuntimeError("Видео скачано, но итоговый видеофайл не найден.")


def _is_readable_video(path: Path) -> bool:
    try:
        import cv2
    except ImportError:
        return path.suffix.lower() in VIDEO_SUFFIXES

    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            return False
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if frame_count > 0:
            return True
        ok, _frame = capture.read()
        return bool(ok)
    finally:
        capture.release()

def _extract_video_frames(
    video_path: Path,
    frames_dir: Path,
    frame_step: int,
    *,
    log: LogCallback | None = None,
    should_stop: StopCallback | None = None,
) -> list[Path]:
    """Извлечь кадры из видео без анализа лица."""
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError(
            "Для извлечения кадров из видео требуется opencv-contrib-python"
        ) from error

    frames_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Не удалось открыть видео: {video_path}")

    frame_paths = []
    frame_index = 0
    try:
        while True:
            if should_stop and should_stop():
                raise StopRequested("Остановлено пользователем")
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % frame_step == 0:
                frame_path = frames_dir / f"frame{frame_index:06d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                frame_paths.append(frame_path)
                if log:
                    log(f"Кадр извлечен: {frame_path.name}")
            frame_index += 1
    finally:
        capture.release()
    return frame_paths


def collect_input_images(
    input_path: str,
    output_dir: str,
    frame_step: int = 24,
    *,
    dominant_face_track: bool = False,
    min_track_length: int = 3,
    log: LogCallback | None = None,
    should_stop: StopCallback | None = None,
) -> list[Path]:
    """Получить список изображений из файла, папки или видео."""
    if is_url(input_path):
        source = download_video_source(
            input_path,
            Path(output_dir) / "downloads",
            log=log,
            should_stop=should_stop,
        )
    else:
        source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Источник не найден: {source}")
    if source.is_file() and source.suffix.lower() in VIDEO_SUFFIXES:
        if log:
            log(f"Извлечение кадров из видео: {source}")
        if dominant_face_track:
            from portrait_core.tracking import select_dominant_face_track

            selected = select_dominant_face_track(
                source,
                Path(output_dir) / "dominant_face_track",
                frame_step=max(1, frame_step),
                min_track_length=min_track_length,
                log=log,
                should_stop=should_stop,
            )
            if not selected:
                raise ValueError(
                    "Dominant geometry-only face-track was not found in video"
                )
            return selected
        return _extract_video_frames(
            source,
            Path(output_dir) / "frames",
            max(1, frame_step),
            log=log,
            should_stop=should_stop,
        )
    images = list(_iter_images(source))
    if not images:
        raise ValueError(f"В источнике нет поддерживаемых изображений: {source}")
    return images


def _quality_status(report: dict) -> tuple[str, list[str]]:
    quality = report.get("quality") or {}
    status = quality.get("status") or "warning"
    issues = quality.get("issues") or []
    if not isinstance(issues, list):
        issues = [str(issues)]
    if status not in {"passed", "warning", "rejected"}:
        status = "warning"
    return status, [str(issue) for issue in issues]


def _frame_index(path: Path) -> int | None:
    match = re.search(r"frame(\d+)", path.stem, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _timestamp_seconds(frame_index: int | None, frame_step: int) -> float | None:
    if frame_index is None:
        return None
    # Без fps мы не знаем точное время, поэтому фиксируем техническую оценку по шагу.
    return float(frame_index) if frame_step <= 0 else None


def _unique_name(index: int, image_path: Path) -> str:
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", image_path.stem).strip("_") or "image"
    return f"{index:04d}_{safe_stem}{image_path.suffix.lower()}"


def _ensure_pfr_identity(report: dict, dataset_id: str) -> tuple[str, str]:
    pfr_id = report.get("id") or make_record_id("PFR")
    pfr_uuid = report.get("uuid") or new_uuid()
    report["id"] = pfr_id
    report["uuid"] = pfr_uuid
    report["dataset_id"] = report.get("dataset_id") or dataset_id
    metadata = report.setdefault("metadata", {})
    metadata.update({"pfr_id": pfr_id, "pfr_uuid": pfr_uuid, "dataset_id": report["dataset_id"]})
    return pfr_id, pfr_uuid


def build_dataset(
    input_path: str,
    output_dir: str,
    *,
    backend: str = "mediapipe",
    model_path: str | None = None,
    topology_path: str | None = None,
    frame_step: int = 24,
    copy_images: bool = True,
    build_invariants: bool = False,
    dominant_face_track: bool = False,
    min_track_length: int = 3,
    log: LogCallback | None = None,
    progress: ProgressCallback | None = None,
    should_stop: StopCallback | None = None,
) -> dict:
    """Создать Dataset Archive через официальный API portrait_core."""
    settings = {
        "backend": backend,
        "model_path": model_path,
        "topology_path": topology_path,
        "frame_step": frame_step,
        "copy_images": copy_images,
        "build_invariants": build_invariants,
        "dominant_face_track": dominant_face_track,
        "min_track_length": min_track_length,
    }
    dataset_dir, dataset = create_dataset_archive(
        output_dir,
        source=str(input_path),
        settings={key: value for key, value in settings.items() if value is not None},
    )
    if log:
        log(f"Источник: {input_path}")
        log(f"Dataset Archive: {dataset_dir}")

    images = collect_input_images(
        input_path,
        str(dataset_dir / "_frames"),
        frame_step=frame_step,
        dominant_face_track=dominant_face_track,
        min_track_length=min_track_length,
        log=log,
        should_stop=should_stop,
    )
    rows = []
    total = len(images)
    if log:
        log(f"К анализу изображений: {total}")

    for index, image_path in enumerate(images, start=1):
        if should_stop and should_stop():
            raise StopRequested("Остановлено пользователем")
        if log:
            log(f"[{index}/{total}] portrait_core: {image_path.name}")

        frame_index = _frame_index(image_path)
        copied_image = dataset_dir / "images" / _unique_name(index, image_path)
        if copy_images:
            copied_image.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, copied_image)
        image_for_item = copied_image if copy_images else image_path
        item = {
            "pfr_id": None,
            "pfr_uuid": None,
            "image_path": as_posix(image_for_item, dataset_dir),
            "pfr_path": None,
            "invariants_path": None,
            "status": "rejected",
            "issues": [],
            "source_frame": image_path.name,
            "frame_index": frame_index,
            "timestamp_seconds": _timestamp_seconds(frame_index, frame_step),
        }

        try:
            report = create_portrait_report(
                str(image_path),
                backend=backend,
                model_path=model_path,
                topology_path=topology_path,
                input_metadata={
                    "dataset_id": dataset["id"],
                    "source_type": "video_frame" if frame_index is not None else "image",
                    "source_frame": image_path.name,
                    "frame": frame_index,
                    "timestamp": item["timestamp_seconds"],
                },
            )
            status, issues = _quality_status(report)
            pfr_id, pfr_uuid = _ensure_pfr_identity(report, dataset["id"])
            pfr_path = dataset_dir / "pfr" / f"{Path(item['image_path']).stem}_portrait.json"
            write_json(pfr_path, report)
            invariants_path = None
            if build_invariants:
                from portrait_core.invariants import build_invariants_for_portrait

                invariants_path = (
                    dataset_dir / "invariants" / f"{pfr_path.stem}_invariants.json"
                )
                build_invariants_for_portrait(pfr_path, invariants_path)
            item.update(
                {
                    "pfr_id": pfr_id,
                    "pfr_uuid": pfr_uuid,
                    "pfr_path": as_posix(pfr_path, dataset_dir),
                    "invariants_path": (
                        as_posix(invariants_path, dataset_dir)
                        if invariants_path is not None
                        else None
                    ),
                    "status": status,
                    "issues": issues,
                }
            )
            if log:
                log(f"{status}: {image_path.name}")
        except Exception as error:  # noqa: BLE001 - Dataset Builder должен продолжать серию.
            item["issues"] = [str(error)]
            if log:
                log(f"rejected: {image_path.name}: {error}")

        dataset["items"].append(item)
        rows.append(
            {
                "image": item["image_path"],
                "report": item["pfr_path"],
                "status": item["status"],
                "issues": "; ".join(item["issues"]),
                "pfr_id": item["pfr_id"],
                "pfr_uuid": item["pfr_uuid"],
            }
        )
        if progress:
            progress(index, total)

    write_dataset_files(dataset_dir, dataset)
    summary = {
        "schema": "profile-dataset-builder/2",
        "dataset_id": dataset["id"],
        "dataset_uuid": dataset["uuid"],
        "dataset_dir": str(dataset_dir),
        "input": str(input_path),
        "output_dir": str(dataset_dir),
        "total_images": total,
        "created_reports": sum(1 for row in rows if row["report"]),
        "statuses": {
            status: sum(1 for row in rows if row["status"] == status)
            for status in ["passed", "warning", "rejected"]
        },
        "rows": rows,
        "items": dataset["items"],
        "architecture": {
            "application": "apps.dataset_builder",
            "scientific_engine": "portrait_core",
            "rule": "Dataset Builder does not compute face geometry; it calls portrait_core.create_portrait_report.",
        },
    }
    write_json(dataset_dir / "summary.json", summary)
    if log:
        log("dataset.json и summary.json сохранены")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dataset Builder приложения Profile")
    parser.add_argument("input_path", help="Папка изображений, файл изображения или видео")
    parser.add_argument("output_dir", help="Папка результата или DS-* архив")
    parser.add_argument("--backend", choices=("mediapipe", "onnx"), default="mediapipe")
    parser.add_argument("--model", dest="model_path")
    parser.add_argument("--topology", dest="topology_path")
    parser.add_argument("--frame-step", type=int, default=24)
    parser.add_argument(
        "--dominant-face-track",
        action="store_true",
        help="For video: select a repeated geometry-only face-track before analysis",
    )
    parser.add_argument(
        "--min-track-length",
        type=int,
        default=3,
        help="Minimum observations required for dominant face-track",
    )
    parser.add_argument("--no-copy", action="store_true", help="Не копировать исходные изображения")
    parser.add_argument(
        "--build-invariants",
        action="store_true",
        help="Дополнительно построить invariants.json для каждого PFR",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = build_dataset(
        args.input_path,
        args.output_dir,
        backend=args.backend,
        model_path=args.model_path,
        topology_path=args.topology_path,
        frame_step=args.frame_step,
        copy_images=not args.no_copy,
        build_invariants=args.build_invariants,
        dominant_face_track=args.dominant_face_track,
        min_track_length=args.min_track_length,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
