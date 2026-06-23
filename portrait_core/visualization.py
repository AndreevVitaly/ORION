"""Визуализация именованных точек на фотографии."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from portrait_core.landmarks import LANDMARK_LABELS_RU


ZONE_COLORS = {
    "face": "#00A6A6",
    "eye": "#2F6BFF",
    "brow": "#8B5CF6",
    "nose": "#E09F00",
    "mouth": "#E5484D",
    "jaw": "#12A150",
    "lip": "#E5484D",
    "chin": "#12A150",
}


def landmark_color(name: str) -> str:
    """Подобрать цвет точки по зоне лица."""
    for zone, color in ZONE_COLORS.items():
        if zone in name:
            return color
    return "#FFFFFF"


def landmark_label(name: str, language: str = "en") -> str:
    """Вернуть подпись точки для выбранного языка интерфейса."""
    if language == "ru":
        return LANDMARK_LABELS_RU.get(name, name)
    return name


def _load_label_font(size: int):
    for font_name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_landmarks(
    image_path: str,
    points: dict,
    *,
    label_language: str = "en",
) -> Image.Image:
    """Вернуть копию изображения с точками и короткими подписями."""
    image = Image.open(Path(image_path)).convert("RGB")
    draw = ImageDraw.Draw(image)
    font_size = max(10, round(min(image.size) / 55))
    font = _load_label_font(font_size)
    radius = max(3, round(min(image.size) / 180))

    for name, (x, y) in points.items():
        x = round(x)
        y = round(y)
        color = landmark_color(name)
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=color,
            outline="#111111",
            width=1,
        )
        draw.text(
            (x + radius + 2, y - radius),
            landmark_label(name, label_language),
            fill="#FFFFFF",
            stroke_width=2,
            stroke_fill="#111111",
            font=font,
        )

    return image
