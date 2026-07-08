# Profile Phase 2: Invariant Engine

Phase 2 adds a research layer for geometric invariant candidates.

The engine reads PFR/`portrait.json`, takes existing `measurements`, and builds dimensionless ratios such as `ipd / face_width`, `nose_length / face_height`, and `mouth_width / face_width`. These values are intended only for morphometric stability research.

The module does not identify people, compare a person with a database, or infer personality traits.

```powershell
python -m portrait_core.invariants build --pfr path\to\portrait.json
python -m portrait_core.invariants stats --input path\to\invariants
```

Inside a DS archive, invariant files are stored in `invariants/` and reference their source PFR.
