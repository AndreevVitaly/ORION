# Profile Applications

`apps/` содержит официальные приложения платформы Profile.

Приложения не реализуют собственную геометрию лица. Они получают данные и передают изображения в `portrait_core`, который является Scientific Engine и Single Source of Truth.

## Приложения

- `dataset_builder/` — подготовка датасетов и запуск `portrait_core` по изображениям или кадрам видео.
