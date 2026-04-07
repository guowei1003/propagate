import asyncio
import uuid
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import Callable, Awaitable
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Task, TaskLog, TaskResult
from app.config import get_settings
from app.services.llm import llm_service

settings = get_settings()


class Worker:
    def __init__(self, on_event: Callable[[uuid.UUID, str, str | None, dict | None], Awaitable[None]]):
        self.on_event = on_event
        self._running = False
        self._task = asyncio.Lock()

    async def start(self, session_factory) -> None:
        self._running = True
        while self._running:
            await self._poll(session_factory)
            await asyncio.sleep(settings.worker_poll_sec)

    async def stop(self) -> None:
        self._running = False

    async def _poll(self, session_factory) -> None:
        async with self._task:
            async with session_factory() as session:
                result = await session.execute(
                    select(Task).where(Task.status == "PENDING").order_by(Task.created_at).limit(1)
                )
                task = result.scalar_one_or_none()
                if not task:
                    return

                await self._execute_task(session, task)

    async def _execute_task(self, session: AsyncSession, task: Task) -> None:
        task.status = "RUNNING"
        task.updated_at = datetime.utcnow()
        await session.commit()

        await self.on_event(
            task.id,
            "status_changed",
            f"Task started: {task.title}",
            {"status": "RUNNING"},
        )

        workspace_dir = None
        try:
            workspace_dir = tempfile.mkdtemp(prefix="propagate_")
            script_path = f"{workspace_dir}/task_script.py"
            output_path = f"{workspace_dir}/output.txt"

            await self.on_event(
                task.id,
                "phase",
                "Generating script with LLM...",
                {"phase": "llm_generation"},
            )

            llm_prompt = (
                f"You are a task execution agent. Execute the following task and write the result to output.txt.\n"
                f"Task: {task.prompt}\n\n"
                f"Write a Python script to accomplish this task, then execute it.\n"
                f"Save final output to: {output_path}"
            )

            script_content = llm_service.complete(llm_prompt)

            await self.on_event(
                task.id,
                "llm_output",
                f"Generated script",
                {"script_preview": script_content[:200]},
            )

            with open(script_path, "w") as f:
                f.write(script_content)

            await self.on_event(
                task.id,
                "phase",
                "Executing in Docker sandbox...",
                {"phase": "execution"},
            )

            result = await self._run_in_docker(script_path, output_path)

            await self.on_event(
                task.id,
                "execution_result",
                f"Execution finished: exit={result['exit_code']}",
                {"exit_code": result["exit_code"], "stdout_len": len(result["stdout"]), "stderr_len": len(result["stderr"])},
            )

            output_text = ""
            if result["exit_code"] == 0:
                try:
                    with open(output_path) as f:
                        output_text = f.read()
                except FileNotFoundError:
                    output_text = result["stdout"]
            else:
                output_text = f"[Error] Exit code {result['exit_code']}\n\nStderr:\n{result['stderr']}"

            db_result = TaskResult(
                task_id=task.id,
                output=output_text,
                artifacts={"stdout": result["stdout"], "stderr": result["stderr"], "exit_code": result["exit_code"]},
            )
            session.add(db_result)

            task.status = "COMPLETED"
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            await session.commit()

            await self.on_event(
                task.id,
                "status_changed",
                "Task completed successfully",
                {"status": "COMPLETED"},
            )

        except Exception as e:
            task.status = "FAILED"
            task.updated_at = datetime.utcnow()
            await session.commit()

            await self.on_event(
                task.id,
                "error",
                f"Task failed: {str(e)}",
                {"error": str(e)},
            )

        finally:
            if workspace_dir and settings.docker_network != "none":
                shutil.rmtree(workspace_dir, ignore_errors=True)

    async def _run_in_docker(self, script_path: str, output_path: str) -> dict:
        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "-v", f"{script_path}:/workspace/script.py:ro",
            "-v", f"{output_path}:/workspace/output.txt",
            settings.runner_image,
            "python3", "/workspace/script.py",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"exit_code": -1, "stdout": "", "stderr": "Execution timed out after 300 seconds"}
        except FileNotFoundError:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Docker not available. Falling back to direct execution.",
            }
