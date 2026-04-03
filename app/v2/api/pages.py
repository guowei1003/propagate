from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.v2.core.config import v2_settings


router = APIRouter()


@router.get("/healthz")
def healthz():
    return JSONResponse({"status": "ok"})


@router.get("/", response_class=HTMLResponse)
def spa_entry():
    index_path = v2_settings.frontend_dist_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse(
        """
        <!doctype html>
        <html lang="zh-CN">
          <head>
            <meta charset="utf-8" />
            <title>Propagate V2</title>
            <style>
              body { font-family: sans-serif; padding: 48px; background: #0b1020; color: #f4f7fb; }
              code { background: rgba(255,255,255,0.12); padding: 2px 6px; border-radius: 4px; }
              a { color: #7dd3fc; }
            </style>
          </head>
          <body>
            <h1>Propagate V2</h1>
            <p>前端源码已生成在 <code>frontend/</code>，当前尚未构建产物。</p>
            <p>可先直接使用 <a href="/docs">/docs</a> 调试 V2 API。</p>
          </body>
        </html>
        """
    )
