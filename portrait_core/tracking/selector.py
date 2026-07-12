"""Geometry-only face-track grouping.

This module does not identify a person. It groups repeated face detections
inside a single video by bounding-box continuity, size and centrality.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FaceObservation:
    frame_index: int
    bbox: tuple[float, float, float, float]
    frame_size: tuple[int, int]
    confidence: float = 1.0

    @property
    def area(self) -> float:
        return max(0.0, self.bbox[2]) * max(0.0, self.bbox[3])

    @property
    def center(self) -> tuple[float, float]:
        x, y, width, height = self.bbox
        return x + width / 2.0, y + height / 2.0

    @property
    def normalized_area(self) -> float:
        width, height = self.frame_size
        frame_area = max(1, width * height)
        return self.area / frame_area

    @property
    def centrality(self) -> float:
        width, height = self.frame_size
        cx, cy = self.center
        dx = abs(cx - width / 2.0) / max(1.0, width / 2.0)
        dy = abs(cy - height / 2.0) / max(1.0, height / 2.0)
        return max(0.0, 1.0 - (dx + dy) / 2.0)


@dataclass
class FaceTrack:
    track_id: str
    observations: list[FaceObservation] = field(default_factory=list)

    @property
    def last(self) -> FaceObservation:
        return self.observations[-1]

    @property
    def count(self) -> int:
        return len(self.observations)

    @property
    def mean_area(self) -> float:
        return _mean([item.normalized_area for item in self.observations])

    @property
    def mean_centrality(self) -> float:
        return _mean([item.centrality for item in self.observations])

    @property
    def continuity(self) -> float:
        frames = [item.frame_index for item in self.observations]
        if len(frames) < 2:
            return 1.0
        span = max(frames) - min(frames) + 1
        return len(set(frames)) / max(1, span)

    @property
    def score(self) -> float:
        return self.count * 4.0 + self.mean_area * 100.0 + self.mean_centrality * 2.0 + self.continuity


def select_dominant_track(
    observations: list[FaceObservation],
    *,
    max_frame_gap: int = 3,
    min_iou: float = 0.08,
    min_count: int = 3,
) -> FaceTrack | None:
    """Select the most repeated geometry-only face track."""
    tracks = build_tracks(observations, max_frame_gap=max_frame_gap, min_iou=min_iou)
    candidates = [track for track in tracks if track.count >= min_count]
    if not candidates:
        return None
    return max(candidates, key=lambda track: (track.score, track.count, track.mean_area))


def build_tracks(
    observations: list[FaceObservation],
    *,
    max_frame_gap: int = 3,
    min_iou: float = 0.08,
) -> list[FaceTrack]:
    tracks: list[FaceTrack] = []
    for observation in sorted(observations, key=lambda item: item.frame_index):
        best_track = None
        best_score = 0.0
        for track in tracks:
            if observation.frame_index - track.last.frame_index > max_frame_gap:
                continue
            score = _iou(observation.bbox, track.last.bbox)
            if score >= min_iou and score > best_score:
                best_track = track
                best_score = score
        if best_track is None:
            best_track = FaceTrack(track_id=f"track-{len(tracks) + 1:03d}")
            tracks.append(best_track)
        best_track.observations.append(observation)
    return tracks


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    left = max(ax, bx)
    top = max(ay, by)
    right = min(ax + aw, bx + bw)
    bottom = min(ay + ah, by + bh)
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    union = aw * ah + bw * bh - intersection
    return intersection / union if union > 0 else 0.0
