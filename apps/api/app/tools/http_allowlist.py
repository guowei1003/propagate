from __future__ import annotations

from urllib.parse import urlparse

import httpx

from app.tools.base import ToolResult


async def call_allowlisted_url(
    url: str,
    method: str,
    *,
    allowed_domains: list[str],
    allowed_methods: list[str],
    headers: dict[str, str] | None = None,
    body: str | None = None,
) -> ToolResult:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host not in allowed_domains:
        return ToolResult(
            status="failed",
            summary=f"domain {host} is not allowlisted",
            artifacts=[],
            payload={"status_code": None},
        )
    if method.upper() not in {item.upper() for item in allowed_methods}:
        return ToolResult(
            status="failed",
            summary=f"method {method} is not allowlisted",
            artifacts=[],
            payload={"status_code": None},
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(method.upper(), url, headers=headers, content=body)

    return ToolResult(
        status="completed" if response.status_code < 400 else "failed",
        summary=f"HTTP {response.status_code}",
        artifacts=[],
        payload={
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "text": response.text,
        },
    )
