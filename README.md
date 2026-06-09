# ПОРТРЕТ

Ранний прототип объективного морфологического анализа лица. Текущий этап
измеряет геометрические пропорции и не формирует психологических выводов.

## Установка

```powershell
python -m pip install -r requirements.txt
```

Для анализа фотографии требуется модель MediaPipe Face Landmarker:

`portrait_core/models/face_landmarker.task`

Файл модели не хранится в git.

## Проверка ядра

```powershell
python -m unittest discover -s portrait_core\tests -v
python -m portrait_core.main
```

## Использование фотографии

Из командной строки:

```powershell
python -m portrait_core.main path\to\photo.jpg
```

Из Python:

```python
from portrait_core.adapters.mediapipe_adapter import MediaPipeAdapter
from portrait_core.analyzer import analyze_points

adapter = MediaPipeAdapter(
    "portrait_core/models/face_landmarker.task"
)
points = adapter.extract_points("photo.jpg")
result = analyze_points(points)
```

## Графический интерфейс

```powershell
python -m portrait_core.gui
```

В интерфейсе можно выбрать фотографию, выполнить анализ, проверить положение
точек и сохранить JSON-отчет или размеченное изображение.
