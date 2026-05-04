import asyncio

import pytest

from app.sandbox.docker_runner import DockerRunner


@pytest.mark.asyncio
async def test_docker_runner_reports_missing_binary(monkeypatch, tmp_path):
    async def fake_exec(*args, **kwargs):  # noqa: ARG001
        raise FileNotFoundError

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    runner = DockerRunner()
    result = await runner.run(tmp_path, ["python", "/workspace/script.py"], timeout_sec=5)
    assert result["status"] == "failed"
    assert "docker" in result["summary"]
