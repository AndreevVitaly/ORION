"""Video preprocessing for dominant non-identifying face tracks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from portrait_core.tracking.selector import FaceObservation, select_dominant_track


def select_dominant_face_track(
    video_path: str | Path,
    output_dir: str | Path,
    *,
    frame_step: int = 24,
    min_track_length: int = 3,
    crop_padding: float = 0.35,
    log: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> list[Path]:
    """Detect repeated face boxes and save crops from the dominant track.

    The output is a technical observation series. It is not identity
    recognition and it does not compare faces with any external database.
    """
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError("opencv-contrib-python is required for video face-track selection") from error

    video = Path(video_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video}")

    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    frames: dict[int, object] = {}
    observations: list[FaceObservation] = []
    frame_index = 0
    frame_step = max(1, frame_step)
    try:
        while True:
            if should_stop and should_stop():
                break
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % frame_step == 0:
                height, width = frame.shape[:2]
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detections = cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(40, 40),
                )
                if len(detections):
                    frames[frame_index] = frame.copy()
                for x, y, box_width, box_height in detections:
                    observations.append(
                        FaceObservation(
                            frame_index=frame_index,
                            bbox=(float(x), float(y), float(box_width), float(box_height)),
                            frame_size=(width, height),
                        )
                    )
            frame_index += 1
    finally:
        capture.release()

    track = select_dominant_track(observations, min_count=min_track_length)
    if track is None:
        if log:
            log("dominant face-track was not found")
        _write_manifest(target, video, None, observations, [])
        return []

    output_paths: list[Path] = []
    for order, observation in enumerate(track.observations, start=1):
        frame = frames.get(observation.frame_index)
        if frame is None:
            continue
        crop = _crop_with_padding(frame, observation.bbox, crop_padding)
        output_path = target / f"{order:04d}_track_{track.track_id}_frame{observation.frame_index:06d}.jpg"
        cv2.imwrite(str(output_path), crop)
        output_paths.append(output_path)
        if log:
            log(f"dominant face-track crop saved: {output_path.name}")

    _write_manifest(target, video, track, observations, output_paths)
    return output_paths


def _crop_with_padding(frame, bbox: tuple[float, float, float, float], padding: float):
    x, y, width, height = bbox
    frame_height, frame_width = frame.shape[:2]
    pad_x = width * padding
    pad_y = height * padding
    left = max(0, int(round(x - pad_x)))
    top = max(0, int(round(y - pad_y)))
    right = min(frame_width, int(round(x + width + pad_x)))
    bottom = min(frame_height, int(round(y + height + pad_y)))
    return frame[top:bottom, left:right]


def _write_manifest(
    output_dir: Path,
    video_path: Path,
    track,
    observations: list[FaceObservation],
    output_paths: list[Path],
) -> None:
    payload = {
        "schema": "profile.face_track_selection.v1",
        "source_video": str(video_path),
        "policy": "geometry-only dominant track selection; no identity recognition",
        "detections": len(observations),
        "selected_track": None
        if track is None
        else {
            "track_id": track.track_id,
            "count": track.count,
            "score": round(track.score, 6),
            "mean_area": round(track.mean_area, 6),
            "mean_centrality": round(track.mean_centrality, 6),
            "continuity": round(track.continuity, 6),
        },
        "frames": [path.name for path in output_paths],
    }
    (output_dir / "face_track_selection.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
