from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.v2.core.errors import V2Error


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(V2Error)
    async def handle_v2_error(_: Request, exc: V2Error) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"message": exc.message, "type": exc.__class__.__name__}},
        )
