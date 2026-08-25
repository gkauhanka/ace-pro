from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


@dataclass
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    details: dict[str, Any] | None = None


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_request: Request, error: ApiError) -> JSONResponse:
        content: dict[str, Any] = {
            "error": {
                "code": error.code,
                "message": error.message,
            }
        }
        if error.details:
            content["error"]["details"] = error.details
        return JSONResponse(status_code=error.status_code, content=content)

