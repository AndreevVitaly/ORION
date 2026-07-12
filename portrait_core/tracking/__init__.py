"""Non-identifying face-track selection for video preprocessing."""

from portrait_core.tracking.selector import (
    FaceObservation,
    FaceTrack,
    select_dominant_track,
)
from portrait_core.tracking.video import select_dominant_face_track

__all__ = [
    "FaceObservation",
    "FaceTrack",
    "select_dominant_face_track",
    "select_dominant_track",
]
