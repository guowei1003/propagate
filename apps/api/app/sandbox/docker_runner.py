from __future__ import annotations

import asyncio
from pathlib import Path

from app.config import get_settings


class DockerRunner:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def run(
        self,
        workspace: Path,
        command: list[str],
        timeout_sec: int,
    ) -> dict:
        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--cpus",
            str(self.settings.default_sandbox_cpu_limit),
            "--memory",
            f"{self.settings.default_sandbox_memory_limit_mb}m",
            "-v",
            f"{workspace}:/workspace",
            "python:3.12-slim",
            *command,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return {
                "status": "failed",
                "summary": "docker command not available",
                "stdout": "",
                "stderr": "docker command not found",
                "artifacts": [],
            }

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {
                "status": "failed",
                "summary": "sandbox execution timed out",
                "stdout": "",
                "stderr": "timeout",
                "artifacts": [],
            }

        status = "completed" if proc.returncode == 0 else "failed"
        return {
            "status": status,
            "summary": f"command exited with {proc.returncode}",
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "artifacts": [],
        }
