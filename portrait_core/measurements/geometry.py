"""Базовая геометрия для расчетов по точкам лица."""


def _validate_point(point):
    """Проверить, что точка похожа на [x, y]."""
    if not isinstance(point, (list, tuple)):
        raise TypeError("Точка должна быть списком или кортежем: [x, y]")
    if len(point) != 2:
        raise ValueError("Точка должна содержать ровно две координаты: [x, y]")
    if not all(isinstance(value, (int, float)) for value in point):
        raise TypeError("Координаты точки должны быть числами")


def _validate_number(value):
    """Проверить, что значение можно использовать в числовом расчете."""
    if not isinstance(value, (int, float)):
        raise TypeError("Значение должно быть числом")


def distance(point_a, point_b) -> float:
    """Посчитать расстояние между двумя точками [x, y]."""
    _validate_point(point_a)
    _validate_point(point_b)
    ax, ay = point_a
    bx, by = point_b
    return float(((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5)


def midpoint(point_a, point_b) -> list:
    """Вернуть середину между двумя точками [x, y]."""
    _validate_point(point_a)
    _validate_point(point_b)
    ax, ay = point_a
    bx, by = point_b
    return [(ax + bx) / 2, (ay + by) / 2]


def ratio(value_a, value_b) -> float:
    """Безопасно посчитать отношение value_a / value_b."""
    _validate_number(value_a)
    _validate_number(value_b)
    if value_b == 0:
        return 0.0
    return float(value_a / value_b)


def horizontal_distance(point_a, point_b) -> float:
    """Посчитать расстояние между точками только по оси X."""
    _validate_point(point_a)
    _validate_point(point_b)
    return float(abs(point_b[0] - point_a[0]))


def vertical_distance(point_a, point_b) -> float:
    """Посчитать расстояние между точками только по оси Y."""
    _validate_point(point_a)
    _validate_point(point_b)
    return float(abs(point_b[1] - point_a[1]))
