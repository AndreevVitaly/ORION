# ПОРТРЕТ

Profile — исследовательская платформа для изучения геометрии лица, landmark, устойчивости измерений, LIC и воспроизводимых экспериментов.

Проект не формирует психологических, HR, криминалистических или биометрических выводов о человеке и не предназначен для оценки личности, характера, интеллекта, профессиональной пригодности или надежности.

## Архитектура Profile

Profile больше не рассматривается как отдельная библиотека анализа лица. Это единая научная платформа:

```text
portrait_core
↓
Scientific Engine
↓
Applications
↓
Research
```

- `portrait_core/` — Scientific Engine и единственный источник истины. Только этот слой анализирует лицо, вычисляет landmark, Mesh, morphology, measurements, LIC, Report Pack и создает `portrait.json`.
- `apps/` — приложения платформы. Они получают данные и передают изображения в `portrait_core`, не повторяя геометрию лица.
- `apps/dataset_builder/` — официальный Dataset Builder платформы Profile.
- `research/` — научная память проекта: гипотезы, методология, эксперименты, LIC, Dataset Builder и knowledge registry. В этом разделе не должно быть исполняемого кода.
- `docs/` — архитектурные и технические документы платформы.

Официальный API Scientific Engine:

```python
import portrait_core

report = portrait_core.analyze("photo.jpg")
report = portrait_core.process_face("face_crop.jpg")
report = portrait_core.create_portrait_report("photo.jpg")
```

Подробнее: `docs/architecture.md`.
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

## Dataset Builder

Dataset Builder является официальным приложением Profile:

```powershell
python -m apps.dataset_builder input_images output_dataset
```

Для видео:

```powershell
python -m apps.dataset_builder video.mp4 output_dataset --frame-step 24
```

Приложение не вычисляет собственные landmark, morphology, measurements, LIC или Report Pack. Оно подготавливает входные изображения и вызывает официальный API `portrait_core.create_portrait_report()`.
## Графический интерфейс

```powershell
python -m portrait_core.gui
```

В интерфейсе можно выбрать фотографию, выполнить анализ, проверить положение
точек, переключить подписи RU/EN, вручную перетащить семантические точки и сохранить JSON-отчет,
размеченное изображение или аннотацию для собственного датасета.

Приложение отдельно показывает пригодность кадра: наклон и поворот головы,
резкость, яркость, контраст, размер лица и нейтральность выражения.


## LIC Core

LIC — Лицевой Инвариантный Каркас. Это экспериментальный геометрический
слой проекта для поиска устойчивой основы измерения лица. LIC не является
психологической интерпретацией, оценкой личности или поведенческим выводом.

LIC Core добавляется в полный JSON-отчет и хранит базовые кандидатные
расстояния, отношения к рекомендованной базе нормализации и ограничения
расчета. Текущая задача слоя — проверить, является ли IPD лучшей базовой
единицей или более устойчивой будет совокупность отношений между несколькими
опорными расстояниями.

Получить полный отчет с LIC Core:

```powershell
python -m portrait_core.main photo.jpg --json
```

Пакетно создать отчеты:

```powershell
python -m portrait_core.batch photos reports
```

Проверить стабильность LIC-кандидатов по серии отчетов одного человека:

```powershell
python -m portrait_core.lic_experiment reports --output lic_stability.json
```

Построить TOP-10 самых стабильных опорных точек лица:

```powershell
python -m portrait_core.lic_stability_report reports --output lic_points.json
```

Упаковать серию отчетов в один компактный исследовательский файл для передачи в ChatGPT или дальнейшего анализа:

```powershell
python -m portrait_core.report_pack reports `
  --output report_pack.json `
  --markdown report_pack.md
```
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


