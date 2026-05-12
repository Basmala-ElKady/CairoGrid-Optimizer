from fastapi import APIRouter, Depends

from Backend.api.dependencies import get_runtime
from Backend.api.runtime import BackendRuntime
from Backend.api.schemas import EdgeSchema, GraphSchema, NodeSchema
from Backend.api.serializers import serialize_edge, serialize_node

router = APIRouter(tags=["graph"])


@router.get("/api/graph", response_model=GraphSchema)
def get_graph(runtime: BackendRuntime = Depends(get_runtime)):
    return {
        "nodes": [serialize_node(runtime, node) for node in runtime.nodes],
        "edges": [serialize_edge(edge) for edge in runtime.unique_edges()],
    }


@router.get("/api/nodes", response_model=list[NodeSchema])
def get_nodes(runtime: BackendRuntime = Depends(get_runtime)):
    return [serialize_node(runtime, node) for node in runtime.nodes]


@router.get("/api/edges", response_model=list[EdgeSchema])
def get_edges(runtime: BackendRuntime = Depends(get_runtime)):
    return [serialize_edge(edge) for edge in runtime.unique_edges()]
