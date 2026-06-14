"""Создание адаптеров по стабильным именам backend."""


def create_mesh_adapter(
    backend: str,
    model_path: str,
    topology_path: str | None = None,
):
    """Создать адаптер без распространения backend-зависимостей по проекту."""
    if backend == "mediapipe":
        from portrait_core.adapters.mediapipe_adapter import MediaPipeAdapter

        return MediaPipeAdapter(model_path)
    if backend == "onnx":
        from portrait_core.adapters.onnx_adapter import OnnxMeshAdapter

        return OnnxMeshAdapter(model_path, topology_path)
    raise ValueError(f"Неизвестный backend сетки: {backend}")
