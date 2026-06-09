"""Адаптер MediaPipe Face Landmarker для одиночных фотографий."""

from pathlib import Path

from portrait_core.landmarks import validate_landmarks

from .base import FacePointAdapter


class FaceAdapterError(RuntimeError):
    """Базовая ошибка извлечения точек лица."""


class FaceNotFoundError(FaceAdapterError):
    """На изображении не найдено лицо."""


class MultipleFacesError(FaceAdapterError):
    """На изображении обнаружено более одного лица."""


class ImageQualityError(FaceAdapterError):
    """Изображение не соответствует минимальным требованиям."""


class MediaPipeAdapter(FacePointAdapter):
    """Преобразовать сетку MediaPipe в контракт измерительного ядра."""

    LANDMARK_INDEXES = {
        "face_left": 234,
        "face_right": 454,
        "face_top": 10,
        "chin": 152,
        "left_eye_outer": 33,
        "left_eye_inner": 133,
        "right_eye_inner": 362,
        "right_eye_outer": 263,
        "nose_tip": 1,
        "nose_bridge": 168,
        "nose_left": 98,
        "nose_right": 327,
        "mouth_left": 61,
        "mouth_right": 291,
        "upper_lip": 13,
        "lower_lip": 14,
        "jaw_left": 172,
        "jaw_right": 397,
        "left_brow_outer": 70,
        "left_brow_inner": 107,
        "right_brow_inner": 336,
        "right_brow_outer": 300,
    }

    def __init__(
        self,
        model_path: str,
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_image_size: int = 256,
    ):
        self.model_path = Path(model_path)
        self.min_detection_confidence = min_detection_confidence
        self.min_presence_confidence = min_presence_confidence
        self.min_image_size = min_image_size

    @staticmethod
    def _load_mediapipe():
        try:
            import mediapipe as mp
        except ImportError as error:
            raise FaceAdapterError(
                "MediaPipe не установлен. Выполните: pip install -r requirements.txt"
            ) from error
        return mp

    @classmethod
    def convert_landmarks(cls, landmarks, width: int, height: int) -> dict:
        """Преобразовать нормализованные точки MediaPipe в пиксели."""
        if width <= 0 or height <= 0:
            raise ValueError("Размер изображения должен быть положительным")

        points = {}
        for name, index in cls.LANDMARK_INDEXES.items():
            try:
                landmark = landmarks[index]
            except IndexError as error:
                raise FaceAdapterError(
                    f"MediaPipe не вернул точку с индексом {index}"
                ) from error
            points[name] = [
                float(landmark.x * width),
                float(landmark.y * height),
            ]

        validate_landmarks(points)
        return points

    def extract_points(self, image_path: str) -> dict:
        """Найти одно лицо на фотографии и вернуть именованные точки."""
        image_file = Path(image_path)
        if not image_file.is_file():
            raise FileNotFoundError(f"Фотография не найдена: {image_file}")
        if not self.model_path.is_file():
            raise FileNotFoundError(f"Модель MediaPipe не найдена: {self.model_path}")

        mp = self._load_mediapipe()
        image = mp.Image.create_from_file(str(image_file))
        if min(image.width, image.height) < self.min_image_size:
            raise ImageQualityError(
                "Короткая сторона фотографии должна быть не меньше "
                f"{self.min_image_size} пикселей"
            )

        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_buffer=self.model_path.read_bytes()
            ),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_faces=2,
            min_face_detection_confidence=self.min_detection_confidence,
            min_face_presence_confidence=self.min_presence_confidence,
        )

        with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
            result = landmarker.detect(image)

        face_count = len(result.face_landmarks)
        if face_count == 0:
            raise FaceNotFoundError("На фотографии не найдено лицо")
        if face_count > 1:
            raise MultipleFacesError(
                "На фотографии найдено несколько лиц; требуется одно лицо"
            )

        return self.convert_landmarks(
            result.face_landmarks[0],
            width=image.width,
            height=image.height,
        )
