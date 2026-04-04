from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.v2.core.errors import V2Error


logger = logging.getLogger(__name__)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(V2Error)
    async def handle_v2_error(_: Request, exc: V2Error) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.message,
                "type": exc.__class__.__name__,
                "code": exc.code,
                "status": exc.status_code,
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled v2 exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "message": "服务器内部错误，请稍后重试。",
                "type": exc.__class__.__name__,
                "code": "INTERNAL_ERROR",
                "status": 500,
            },
        )
