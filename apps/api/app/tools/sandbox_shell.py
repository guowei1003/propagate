from __future__ import annotations

from app.sandbox.docker_runner import DockerRunner
from app.sandbox.workspace import create_workspace
from app.tools.base import ToolResult
from app.tools.workspace_files import write_workspace_file


async def run_shell_commands(run_id: str, script: str, timeout_sec: int) -> ToolResult:
    workspace = create_workspace(run_id)
    write_workspace_file(workspace, "run.sh", script)
    runner = DockerRunner()
    result = await runner.run(workspace, ["sh", "/workspace/run.sh"], timeout_sec)
    return ToolResult(
        status=result["status"],
        summary=result["summary"],
        artifacts=["run.sh"],
        payload=result,
    )
