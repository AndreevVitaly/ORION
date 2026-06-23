# ПОРТРЕТ

Ранний прототип объективного морфологического анализа лица. Текущий этап
измеряет геометрические пропорции и не формирует психологических выводов.

## Архитектура сетки

Внутренний контракт проекта не привязан к индексам MediaPipe. Любой детектор
должен вернуть данные в формате `portrait-mesh/1`:

```text
изображение
→ адаптер детектора
→ полная сетка Portrait Mesh
→ семантические точки
→ измерения
→ морфологический профиль
```

Сетка содержит все вершины детектора, размер изображения, систему координат,
название адаптера, исходную топологию и семантическую карту ориентиров.

MediaPipe сейчас является одним из поставщиков сетки. Его 478 вершин
сохраняются в отчете полностью, а существующее измерительное ядро получает
22 именованные точки через семантическую проекцию. Будущая собственная модель
сможет заменить адаптер без изменения формул измерений и формата отчета.

После извлечения сетки конвейер:

1. оценивает положение головы;
2. устраняет перенос, масштаб и roll;
3. выделяет анатомические зоны в канонических координатах;
4. рассчитывает признаки плотной геометрии;
5. формирует профиль с уверенностью и ограничениями.

Для топологии MediaPipe используются проектные контуры овала, челюсти, глаз,
бровей, носа и губ. Измерения губ строятся по полным внешнему и внутреннему
контурам, а не по одной паре точек.

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
По умолчанию команда выводит короткую сводку. Полный технический отчет:

```powershell
python -m portrait_core.main path\to\photo.jpg --json
python -m portrait_core.main path\to\photo.jpg --output report.json
```

При запуске без аргументов открывается графический интерфейс:

```powershell
python portrait_core\main.py
```

Тестовые координаты доступны отдельно:

```powershell
python portrait_core\main.py --demo
```

Через собственную ONNX-модель:

```powershell
python -m pip install -r requirements-model.txt
python -m portrait_core.main photo.jpg `
  --backend onnx `
  --model models\portrait.onnx `
  --topology models\portrait.onnx.json
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

Полную сетку можно получить отдельно:

```python
mesh = adapter.extract_mesh("photo.jpg")
```

Конвейер принимает любой адаптер, реализующий `extract_mesh()`:

```python
from portrait_core.pipeline import analyze_photo_with_adapter

points, report = analyze_photo_with_adapter("photo.jpg", adapter)
```

## Графический интерфейс

```powershell
python -m portrait_core.gui
```

В интерфейсе можно выбрать фотографию, выполнить анализ, проверить положение
точек, вручную перетащить семантические точки и сохранить JSON-отчет,
размеченное изображение или аннотацию для собственного датасета.

Приложение отдельно показывает пригодность кадра: наклон и поворот головы,
резкость, яркость, контраст, размер лица и нейтральность выражения.

## Пакетная проверка

```powershell
python -m portrait_core.batch photos reports
```

Для каждого изображения создается JSON-отчет. В папке результатов также
появляются `summary.csv` и `summary.json` с ошибками и предупреждениями.

## Стабильность серии

После создания нескольких отчетов одного человека:

```powershell
python -m portrait_core.series reports `
  --subject person_01 `
  --output stability.json
```

Команда рассчитывает среднее, стандартное отклонение и коэффициент вариации
каждого общего плотного признака.

До загрузки серии поле `stability` в confidence остается `null`. Остальные
компоненты показываются отдельно: валидность точек, ракурс, покрытие зоны и
качество фотографии.

## Документы разработки

- `portrait_mesh_schema.md` — внутренний контракт сетки;
- `feature_catalog.md` — формулы и условия признаков;
- `model_development.md` — путь к собственной landmark-модели;
- `dataset_annotation_schema.json` — формат разметки датасета;
- `model_contract.example.json` — sidecar-контракт ONNX-модели.

## Ограничения

Пороговые значения пока предварительные и вынесены в
`portrait_core/config.py`. Индикатор визуального напряжения является только
геометрическим описанием положения губ и бровей, а не оценкой эмоций или
психологического состояния.
