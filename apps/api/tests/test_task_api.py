import pytest


@pytest.mark.asyncio
async def test_task_creation_and_run_detail(client):
    create_response = await client.post(
        "/api/v1/tasks",
        json={
            "title": "调研并输出总结",
            "goal": "调研项目结构并生成一份总结报告",
            "constraints": ["不要访问未授权域名"],
            "deliverables": ["总结报告", "执行日志"],
            "approval_mode": "high_risk",
        },
    )
    assert create_response.status_code == 201
    task_payload = create_response.json()
    assert task_payload["latest_run_id"] is not None

    run_id = task_payload["latest_run"]["id"]
    run_response = await client.get(f"/api/v1/tasks/{task_payload['id']}/runs/{run_id}")
    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["mission"] is not None
    assert len(run_payload["steps"]) >= 3
