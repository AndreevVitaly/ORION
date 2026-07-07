# Archive Model

Profile переходит от папок с разрозненными JSON к воспроизводимому научному архиву. Архив хранит не только файлы, но и связи между происхождением данных, анализом, экспериментом и итоговой исследовательской сводкой.

Главная цепочка:

```text
PFR -> Dataset -> Experiment -> Report Pack -> Research
```

## Почему не просто папка с JSON

Папка с JSON отвечает только на вопрос "где лежат отчеты". Для исследования этого мало: нужно понимать, какие кадры вошли в выборку, каким способом они получены, какие настройки использовались, какие PFR отсутствуют или отклонены, какой эксперимент был запущен и какой Report Pack относится к какому набору данных.

Dataset Archive делает эту цепочку явной и проверяемой.

## PFR

PFR (Profile Face Record) - минимальная единица архива. Это результат анализа одного лица в одном изображении.

PFR создается только `portrait_core` и содержит собственные `id` и `uuid`. Если PFR входит в Dataset, он также связывается с `dataset_id`.

## Dataset

Dataset, или DS, - коллекция PFR, полученных по единому сценарию.

Рекомендуемая структура:

```text
datasets/
└── DS-YYYYMMDD-HHMMSS/
    ├── dataset.json
    ├── images/
    ├── pfr/
    ├── experiments/
    └── summary.json
```

`dataset.json` хранит `id`, `uuid`, `created_at`, `source`, `settings`, `items` и `summary`. Каждый item связывает исходное изображение, PFR, статус качества и данные кадра.

## Experiment

Experiment, или EXP, - обработка одного или нескольких Dataset по заданной методике.

Минимальный `experiment.json` содержит:

```json
{
  "schema": {"name": "profile-experiment", "version": "1.0"},
  "id": "EXP-YYYYMMDD-HHMMSS",
  "uuid": "...",
  "created_at": "...",
  "datasets": ["DS-..."],
  "method": "lic_stability",
  "inputs": [],
  "outputs": [],
  "hypotheses": [],
  "notes": ""
}
```

## Report Pack

Report Pack, или RP, - агрегированный результат эксперимента. Он должен хранить собственные `id` и `uuid`, связь с `dataset_id`, `experiment_id` и список PFR, которые вошли в расчет.

Report Pack остается компактной исследовательской сводкой: сырые `points` и тяжелый `mesh` не дублируются в кадровой части.

## Research

`research/` - научная память проекта. Здесь фиксируются гипотезы, решения, ограничения, выводы и методология. Исполняемый код в этот раздел не помещается.

## Полный цикл

```text
Видео или серия фото
↓
Dataset Builder
↓
DS-YYYYMMDD-HHMMSS/images
↓
portrait_core
↓
DS-YYYYMMDD-HHMMSS/pfr/*.json
↓
Experiment EXP-YYYYMMDD-HHMMSS
↓
LIC / point stability / Report Pack
↓
Research notes and decisions
```

## CLI

Создать пустой Dataset Archive:

```powershell
python -m portrait_core.archive.create_dataset datasets --source photos
```

Создать Experiment:

```powershell
python -m portrait_core.archive.create_experiment datasets\DS-YYYYMMDD-HHMMSS --method lic_stability
```

Проверить Dataset Archive:

```powershell
python -m portrait_core.archive.validate_dataset datasets\DS-YYYYMMDD-HHMMSS
```

## Совместимость

Старые папки с `*_portrait.json` продолжают читаться инструментами LIC и Report Pack. Новая модель становится основным направлением, но не требует немедленной миграции всех старых экспериментов.
