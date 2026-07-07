# PFR Specification

PFR (Profile Face Record) — официальный стандарт данных проекта Profile для хранения результата анализа одного лица.

Файл может по-прежнему называться `portrait.json`, но логически он является документом стандарта PFR.

## Назначение

PFR нужен, чтобы все приложения платформы Profile работали с единым форматом данных:

- CLI;
- GUI;
- Dataset Builder;
- API;
- будущие приложения;
- исследовательские инструменты LIC, Report Pack и series analysis.

PFR хранит геометрию лица, измерения, LIC, morphology, quality и метаданные генерации. PFR не является психологическим, HR, криминалистическим или биометрическим выводом о человеке.

## Архитектурное правило

Только `portrait_core` имеет право создавать PFR.

Приложения не должны самостоятельно формировать структуру `portrait.json`. Они обязаны получать PFR через официальный API:

```python
import portrait_core

record = portrait_core.create_portrait_report("photo.jpg")
```

## Идентичность PFR

Каждый новый PFR содержит верхнеуровневые поля:

- `id` - идентификатор записи вида `PFR-*`;
- `uuid` - глобальный UUID записи;
- `dataset_id` - идентификатор Dataset, если PFR создан внутри Dataset Archive.

Эти поля добавляются мягко: старые PFR без `id` и `uuid` остаются читаемыми, но новые записи должны их иметь.

## Обязательные разделы

### schema

Описание стандарта данных.

```json
{
  "name": "profile-face-record",
  "version": "1.0"
}
```

### generator

Информация о генераторе PFR.

```json
{
  "name": "portrait_core",
  "version": "0.1.0",
  "backend": "mediapipe-face-landmarker"
}
```

### input

Описание происхождения изображения.

```json
{
  "image": "D:/PROFILE/photo.jpg",
  "source_type": "image",
  "frame": null,
  "timestamp": null
}
```

Для видео или Dataset Builder могут заполняться `frame`, `timestamp`, `source_frame` и `dataset_id`.

### quality

Единое место хранения оценок качества кадра: статус, предупреждения, проверки и метрики.

### geometry

Единое место хранения координат.

```json
{
  "points": {},
  "mesh": {},
  "image_size": {
    "width": 256,
    "height": 256
  },
  "coordinate_system": "image-pixels"
}
```

Все координаты должны храниться здесь. Для обратной совместимости текущий PFR также сохраняет старые верхнеуровневые поля `points` и `mesh`.

### measurements

Единое место хранения вычисленных размеров и отношений. Приложения не должны пересчитывать эти значения самостоятельно.

### lic

Раздел результатов LIC. Для обратной совместимости текущий PFR также сохраняет старое поле `lic_core` с тем же содержимым.

### morphology

Сводные геометрические классификации, построенные `portrait_core`.

### metadata

Технические метаданные создания PFR.

```json
{
  "created_at": "2026-07-07T10:00:00+00:00",
  "backend": "mediapipe-face-landmarker",
  "backend_version": null,
  "warnings": []
}
```

## Необязательные разделы

Текущий PFR может содержать дополнительные разделы:

- `canonical_mesh`;
- `zones`;
- `features`;
- `profile`;
- `interpretation`;
- `id`, `uuid`, `dataset_id` — идентичность PFR и связь с Dataset;
- `schema_version` — legacy-версия старого отчета;
- `lic_core` — legacy-алиас раздела `lic`;
- `points` и `mesh` — legacy-алиасы `geometry.points` и `geometry.mesh`.

## Правила совместимости

1. Новые поля добавляются без удаления старых ключей, если эти ключи используются существующими инструментами.
2. `schema.version` меняется только при изменении правил стандарта PFR.
3. Удаление legacy-полей возможно только после отдельной миграции и обновления инструментов.
4. Приложения должны читать данные из PFR, но не создавать собственные варианты `portrait.json`.

## Правила расширения

- Новые геометрические координаты добавляются в `geometry`.
- Новые измерения добавляются в `measurements`.
- Новые LIC-результаты добавляются в `lic`.
- Новые оценки качества добавляются в `quality`.
- Новые технические сведения добавляются в `metadata`.
- Исследовательские выводы и гипотезы не должны смешиваться с PFR; для них используется `research/`.

## Пример PFR

```json
{
  "schema_version": 3,
  "id": "PFR-abc123",
  "uuid": "12345678-1234-5678-1234-567812345678",
  "dataset_id": "DS-20260704-000901",
  "schema": {
    "name": "profile-face-record",
    "version": "1.0"
  },
  "generator": {
    "name": "portrait_core",
    "version": "0.1.0",
    "backend": "mediapipe-face-landmarker"
  },
  "input": {
    "image": "D:/PROFILE/photo.jpg",
    "source_type": "image",
    "frame": null,
    "timestamp": null
  },
  "quality": {
    "status": "passed",
    "issues": [],
    "checks": {},
    "metrics": {}
  },
  "geometry": {
    "points": {
      "left_eye_inner": [100.0, 120.0],
      "right_eye_inner": [150.0, 120.0]
    },
    "mesh": {
      "schema": "portrait-mesh",
      "schema_version": 1
    },
    "image_size": {
      "width": 256,
      "height": 256
    },
    "coordinate_system": "image-pixels"
  },
  "measurements": {
    "face": {},
    "eyes": {},
    "symmetry": {}
  },
  "lic": {
    "version": "lic-core/0.1",
    "base_candidates": {},
    "ratios": {},
    "recommended_base": "ipd",
    "limitations": []
  },
  "morphology": {
    "face_proportion": "среднее",
    "symmetry": "высокая симметрия"
  },
  "metadata": {
    "created_at": "2026-07-07T10:00:00+00:00",
    "backend": "mediapipe-face-landmarker",
    "backend_version": null,
    "warnings": []
  }
}
```
