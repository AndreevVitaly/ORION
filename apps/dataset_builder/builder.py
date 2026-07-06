"""Dataset Builder: подготовка кадров и запуск portrait_core.

Модуль намеренно не вычисляет landmarks, morphology, measurements, LIC или
quality самостоятельно. Единственный источник геометрической истины —
portrait_core.create_portrait_report().
"""

import argparse
import json
import shutil
from pathlib import Path
from typing import Callable, Iterable

from portrait_core import create_portrait_report


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
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



def _extract_video_frames(
    video_path: Path,
    frames_dir: Path,
    frame_step: int,
    *,
    log: LogCallback | None = None,
    should_stop: StopCallback | None = None,
) -> list[Path]:
    """Извлечь кадры из видео без анализа лица.

    Это техническая подготовка входных изображений. Геометрия лица остается в
    portrait_core.
    """
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
    log: LogCallback | None = None,
    should_stop: StopCallback | None = None,
) -> list[Path]:
    """Получить список изображений из файла, папки или видео."""
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Источник не найден: {source}")
    if source.is_file() and source.suffix.lower() in VIDEO_SUFFIXES:
        if log:
            log(f"Извлечение кадров из видео: {source}")
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



def _write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")



def build_dataset(
    input_path: str,
    output_dir: str,
    *,
    backend: str = "mediapipe",
    model_path: str | None = None,
    topology_path: str | None = None,
    frame_step: int = 24,
    copy_images: bool = True,
    log: LogCallback | None = None,
    progress: ProgressCallback | None = None,
    should_stop: StopCallback | None = None,
) -> dict:
    """Создать датасет отчетов через официальный API portrait_core."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if log:
        log(f"Источник: {input_path}")
        log(f"Папка результата: {output}")
    images = collect_input_images(
        input_path,
        output_dir,
        frame_step=frame_step,
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
        try:
            report = create_portrait_report(
                str(image_path),
                backend=backend,
                model_path=model_path,
                topology_path=topology_path,
            )
            status, issues = _quality_status(report)
            status_dir = output / status
            status_dir.mkdir(parents=True, exist_ok=True)
            report_path = status_dir / f"{image_path.stem}_portrait.json"
            _write_json(report_path, report)
            copied_image = status_dir / image_path.name
            if copy_images:
                shutil.copy2(image_path, copied_image)
            rows.append(
                {
                    "image": str(copied_image if copy_images else image_path),
                    "report": str(report_path),
                    "status": status,
                    "issues": issues,
                }
            )
            if log:
                log(f"{status}: {image_path.name}")
        except Exception as error:  # noqa: BLE001 - Dataset Builder должен продолжать серию.
            error_dir = output / "rejected"
            error_dir.mkdir(parents=True, exist_ok=True)
            rows.append(
                {
                    "image": str(image_path),
                    "report": None,
                    "status": "rejected",
                    "issues": [str(error)],
                }
            )
            if log:
                log(f"rejected: {image_path.name}: {error}")
        if progress:
            progress(index, total)

    summary = {
        "schema": "profile-dataset-builder/1",
        "input": str(input_path),
        "output_dir": str(output),
        "total_images": total,
        "created_reports": sum(1 for row in rows if row["report"]),
        "statuses": {
            status: sum(1 for row in rows if row["status"] == status)
            for status in ["passed", "warning", "rejected"]
        },
        "rows": rows,
        "architecture": {
            "application": "apps.dataset_builder",
            "scientific_engine": "portrait_core",
            "rule": "Dataset Builder does not compute face geometry; it calls portrait_core.create_portrait_report.",
        },
    }
    _write_json(output / "summary.json", summary)
    if log:
        log("summary.json сохранен")
    return summary



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dataset Builder приложения Profile"
    )
    parser.add_argument("input_path", help="Папка изображений, файл изображения или видео")
    parser.add_argument("output_dir", help="Папка результата")
    parser.add_argument("--backend", choices=("mediapipe", "onnx"), default="mediapipe")
    parser.add_argument("--model", dest="model_path")
    parser.add_argument("--topology", dest="topology_path")
    parser.add_argument("--frame-step", type=int, default=24)
    parser.add_argument("--no-copy", action="store_true", help="Не копировать исходные изображения")
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
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
