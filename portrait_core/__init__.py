"""Scientific Engine проекта Profile.

Публичные функции этого пакета являются официальным API для приложений
экосистемы Profile. Внешние приложения должны использовать этот слой, а не
повторять геометрию лица, LIC, morphology или measurements самостоятельно.
"""

from portrait_core.api import analyze, create_portrait_report, process_face
from portrait_core.invariants import build_invariant_stats, build_invariants_for_portrait

__all__ = [
    "analyze",
    "build_invariant_stats",
    "build_invariants_for_portrait",
    "create_portrait_report",
    "process_face",
]
