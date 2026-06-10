"""Настраиваемые пороги объективного анализа."""

MORPHOLOGY_THRESHOLDS = {
    "face_proportion": {
        "low": 0.65,
        "high": 0.80,
        "labels": ("вытянутое", "среднее", "широкое"),
    },
    "jaw_width": {
        "low": 0.60,
        "high": 0.78,
        "labels": ("узкая", "средняя", "широкая"),
    },
    "mouth_width": {
        "low": 0.35,
        "high": 0.48,
        "labels": ("узкий", "средний", "широкий"),
    },
    "symmetry": {
        "low": 0.90,
        "high": 0.97,
        "labels": (
            "выраженная асимметрия",
            "умеренная симметрия",
            "высокая симметрия",
        ),
    },
}

QUALITY_THRESHOLDS = {
    "max_roll_degrees": 8.0,
    "max_yaw_offset_ratio": 0.12,
    "min_blur_score": 80.0,
    "min_brightness": 55.0,
    "max_brightness": 205.0,
    "min_contrast": 28.0,
    "min_face_coverage": 0.035,
    "max_mouth_opening_ratio": 0.22,
}
