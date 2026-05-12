from fastapi import Request

from Backend.api.runtime import BackendRuntime


def get_runtime(request: Request) -> BackendRuntime:
    return request.app.state.runtime
