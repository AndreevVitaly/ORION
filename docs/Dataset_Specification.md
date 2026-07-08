# Dataset Specification

Dataset Archive - официальный формат хранения коллекции PFR в Profile.

## Назначение

Dataset нужен, чтобы серия PFR была воспроизводимой: у каждого запуска есть идентичность, источник, настройки, список элементов и сводка качества.

## Структура

```text
DS-YYYYMMDD-HHMMSS/
├── dataset.json
├── images/
├── pfr/
├── invariants/
├── experiments/
└── summary.json
```

## dataset.json

Обязательные поля:

- `schema` - `{ "name": "profile-dataset", "version": "1.0" }`;
- `id` - стабильный идентификатор вида `DS-YYYYMMDD-HHMMSS`;
- `uuid` - глобальный UUID Dataset;
- `created_at` - время создания;
- `source` - исходная папка, файл, видео или описание источника;
- `settings` - настройки сборки;
- `items` - список элементов Dataset;
- `summary` - агрегированная сводка.

## item

Каждый item связывает изображение и PFR:

```json
{
  "pfr_id": "PFR-...",
  "pfr_uuid": "...",
  "image_path": "images/0001_frame.jpg",
  "pfr_path": "pfr/0001_frame_portrait.json",
  "invariants_path": "invariants/0001_frame_portrait_invariants.json",
  "status": "passed",
  "issues": [],
  "source_frame": "frame.jpg",
  "frame_index": null,
  "timestamp_seconds": null
}
```

Если анализ не выполнен, `pfr_id`, `pfr_uuid` и `pfr_path` могут быть `null`, а `status` должен объяснять причину через `issues`.

`invariants_path` заполняется только если для PFR был построен файл Phase 2 `invariants.json`. Этот слой не выполняет биометрическую идентификацию и хранит только отношения морфометрических измерений.

## Правила

- Dataset Builder создает Dataset Archive по умолчанию.
- PFR внутри Dataset создается только через `portrait_core`.
- `summary.json` может содержать legacy-поля `rows`, `statuses` и `created_reports` для совместимости со старыми инструментами.
- `datasets/` не коммитится в git, кроме `datasets/.gitkeep`.
