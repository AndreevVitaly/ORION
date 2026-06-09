"""Визуализация именованных точек на фотографии."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


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


def draw_landmarks(image_path: str, points: dict) -> Image.Image:
    """Вернуть копию изображения с точками и короткими подписями."""
    image = Image.open(Path(image_path)).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
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
            name,
            fill="#FFFFFF",
            stroke_width=2,
            stroke_fill="#111111",
            font=font,
        )

    return image
