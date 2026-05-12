from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from Backend.api.errors import ApiError, api_error_handler, unhandled_error_handler, validation_error_handler
from Backend.api.routes.graph import router as graph_router
from Backend.api.routes.health import router as health_router
from Backend.api.routes.ml import router as ml_router
from Backend.api.routes.optimization import router as optimization_router
from Backend.api.routes.routing import router as routing_router
from Backend.api.runtime import BackendRuntime


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime = BackendRuntime().load()
    app.state.runtime = runtime
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="CairoGrid Optimizer API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(graph_router)
    app.include_router(routing_router)
    app.include_router(optimization_router)
    app.include_router(ml_router)

    return app


app = create_app()


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        "Backend.api.server:app",
        host=os.getenv("CAIROGRID_API_HOST", "127.0.0.1"),
        port=int(os.getenv("CAIROGRID_API_PORT", "8000")),
        reload=False,
    )
