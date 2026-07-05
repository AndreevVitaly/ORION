# Dataset Builder

Dataset Builder — официальное приложение платформы Profile.

Оно не является самостоятельным исследовательским ядром и не вычисляет landmark, Mesh, morphology, measurements, LIC или Report Pack самостоятельно. Для анализа каждого изображения используется официальный API:

```python
portrait_core.create_portrait_report(image_path)
```

## Запуск

```powershell
python -m apps.dataset_builder input_images output_dataset
```

Для видео:

```powershell
python -m apps.dataset_builder video.mp4 output_dataset --frame-step 24
```

Результат раскладывается по папкам `passed`, `warning`, `rejected`, а общая сводка сохраняется в `summary.json`.

## Архитектурное правило

Dataset Builder получает данные и передает их в `portrait_core`. Любая новая геометрическая логика должна добавляться в `portrait_core`, а не в приложение.
