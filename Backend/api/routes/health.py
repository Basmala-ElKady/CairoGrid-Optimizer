from fastapi import APIRouter, Depends

from Backend.api.dependencies import get_runtime
from Backend.api.runtime import BackendRuntime
from Backend.api.schemas import HealthSchema

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthSchema)
def get_health(runtime: BackendRuntime = Depends(get_runtime)):
    nodes_count, edges_count = runtime.graph_counts()
    return {
        "status": "online",
        "graph_loaded": runtime.graph is not None,
        "nodes_count": nodes_count,
        "edges_count": edges_count,
        "ml_ready": bool(runtime.ml_service and runtime.ml_service.is_ready),
    }
