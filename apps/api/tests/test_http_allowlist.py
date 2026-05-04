import httpx
import pytest

from app.tools.http_allowlist import call_allowlisted_url


@pytest.mark.asyncio
async def test_http_allowlist_blocks_unknown_domain():
    result = await call_allowlisted_url(
        "https://example.com",
        "GET",
        allowed_domains=["api.internal.local"],
        allowed_methods=["GET"],
    )
    assert result.status == "failed"
    assert "not allowlisted" in result.summary


@pytest.mark.asyncio
async def test_http_allowlist_allows_configured_domain(monkeypatch):
    async def fake_request(self, method, url, headers=None, content=None):  # noqa: ARG001
        return httpx.Response(200, text='{"ok":true}')

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)
    result = await call_allowlisted_url(
        "https://api.internal.local/health",
        "GET",
        allowed_domains=["api.internal.local"],
        allowed_methods=["GET"],
    )
    assert result.status == "completed"
    assert result.payload["status_code"] == 200
