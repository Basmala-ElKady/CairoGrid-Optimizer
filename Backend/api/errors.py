from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def build_error_response(status_code: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return build_error_response(exc.status_code, exc.code, exc.message, exc.details)


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return build_error_response(
        422,
        "validation_error",
        "The request payload is invalid.",
        {"issues": exc.errors()},
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    return build_error_response(
        500,
        "internal_server_error",
        "The backend encountered an unexpected error.",
        {"exception": exc.__class__.__name__},
    )
