"""Ручной адаптер точек лица."""

from .base import FacePointAdapter
from portrait_core.mesh import build_mesh


class ManualAdapter(FacePointAdapter):
    """Временный адаптер с тестовыми координатами без внешних библиотек."""

    def extract_mesh(self, image_path: str) -> dict:
        """Вернуть тестовую сетку с семантическими вершинами."""
        # image_path пока не используется: позже здесь можно читать ручную
        # разметку из файла или заменить источник на другую реализацию.
        points = {
            "face_left": [120, 220],
            "face_right": [360, 220],
            "face_top": [240, 80],
            "chin": [240, 420],
            "left_eye_outer": [155, 195],
            "left_eye_inner": [205, 195],
            "right_eye_inner": [275, 195],
            "right_eye_outer": [325, 195],
            "nose_tip": [240, 270],
            "nose_bridge": [240, 210],
            "nose_left": [220, 275],
            "nose_right": [260, 275],
            "mouth_left": [190, 335],
            "mouth_right": [290, 335],
            "upper_lip": [240, 320],
            "lower_lip": [240, 350],
            "jaw_left": [155, 355],
            "jaw_right": [325, 355],
            "left_brow_outer": [160, 165],
            "left_brow_inner": [215, 160],
            "right_brow_inner": [265, 160],
            "right_brow_outer": [320, 165],
        }
        names = list(points)
        vertices = [[*points[name], 0.0] for name in names]
        return build_mesh(
            vertices,
            {name: index for index, name in enumerate(names)},
            source="manual",
            source_topology="portrait-semantic-22",
            image_width=480,
            image_height=500,
            metadata={"synthetic": True},
        )
