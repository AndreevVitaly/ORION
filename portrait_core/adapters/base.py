"""Базовые интерфейсы адаптеров.

Адаптеры нужны, чтобы ядро портретного анализа не зависело от конкретного
источника точек лица. Источником может быть MediaPipe, ручная разметка или
будущая собственная модель.
"""


class BaseAdapter:
    """Минимальный базовый адаптер для будущих источников данных."""

    def load(self):
        """Загрузить данные и вернуть их в формате, понятном ядру."""
        raise NotImplementedError("Метод load должен быть реализован в наследнике")


class FacePointAdapter:
    """Базовый адаптер сетки лица с совместимым API именованных точек."""

    def extract_mesh(self, image_path: str) -> dict:
        """Извлечь полную сетку в формате Portrait Mesh Schema."""
        raise NotImplementedError(
            "Метод extract_mesh должен быть реализован в наследнике"
        )

    def extract_points(self, image_path: str) -> dict:
        """Спроецировать сетку в именованные точки старого контракта."""
        from portrait_core.mesh import project_semantic_points

        return project_semantic_points(self.extract_mesh(image_path))
