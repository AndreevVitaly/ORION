# Архитектура Profile

Profile рассматривается как единая исследовательская платформа, а не как отдельная библиотека анализа лица.

## Слои платформы

```text
portrait_core
↓
Scientific Engine
↓
Applications
↓
Research
```

## portrait_core

`portrait_core` является Scientific Engine и единственным источником истины проекта.

Только `portrait_core` имеет право:

- анализировать лицо;
- вычислять landmark;
- строить Mesh;
- вычислять morphology;
- вычислять measurements;
- вычислять LIC;
- строить Report Pack;
- создавать `portrait.json`.

Официальный API:

```python
import portrait_core

report = portrait_core.analyze("photo.jpg")
report = portrait_core.process_face("face_crop.jpg")
report = portrait_core.create_portrait_report("photo.jpg")
```

## apps

`apps/` содержит только приложения платформы. Приложения получают данные, готовят входной поток и передают изображения в `portrait_core`.

Приложения не должны повторять геометрию лица, LIC, morphology, measurements или построение `portrait.json`.

Текущие приложения:

- `apps/dataset_builder` — официальный Dataset Builder платформы Profile.

Возможные будущие приложения:

- `future_desktop`;
- `future_camera`;
- `future_api`.

## Dataset Builder

Dataset Builder больше не рассматривается как самостоятельный проект. Он является приложением Profile и использует `portrait_core.create_portrait_report()`.

Его роль:

```text
видео или изображения
↓
Dataset Builder
↓
кадры / входные изображения
↓
portrait_core
↓
portrait.json
↓
LIC, Morphology, Measurements, Report Pack
↓
Research
```

Dataset Builder может извлекать кадры из видео и раскладывать результаты по статусам качества, но не вычисляет собственные landmark, morphology, measurements, LIC или quality.

## research

`research/` содержит только исследовательскую информацию:

- гипотезы;
- методологию;
- эксперименты;
- LIC-документы;
- Dataset Builder-документы;
- knowledge registry.

В `research/` не должно быть исполняемого кода.

## Ограничение

Profile работает с геометрией лица, landmark, устойчивостью измерений и воспроизводимостью экспериментов. Платформа не делает выводов о личности, характере, интеллекте, профессиональной пригодности или надежности человека.
