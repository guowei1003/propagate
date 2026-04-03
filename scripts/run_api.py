from __future__ import annotations

import os

import uvicorn


def resolve_server_config() -> tuple[str, int]:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    return host, port


if __name__ == "__main__":
    host, port = resolve_server_config()
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
