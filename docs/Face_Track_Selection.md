# Face Track Selection

Face Track Selection is a video preprocessing step for Profile datasets.

It does not recognize a person and does not compare faces with any external database. It only groups repeated face detections inside one video by bounding-box continuity, size, centrality, and frequency.

The goal is to build a cleaner research sample:

```text
video
-> face detections per sampled frame
-> geometry-only tracks
-> dominant repeated track
-> cropped observation frames
-> Dataset Builder / portrait_core
```

CLI usage through Dataset Builder:

```powershell
python -m apps.dataset_builder video.mp4 datasets --dominant-face-track --frame-step 24
```

The selector writes `face_track_selection.json` next to extracted crops. The manifest explicitly records the policy: geometry-only dominant track selection, no identity recognition.
