from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app
from app.v2.core.errors import ConflictError
from app.v2.core.http import install_error_handlers


class AppEntryTestCase(unittest.TestCase):
    def test_root_serves_v2_entry(self) -> None:
        client = TestClient(app)
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Propagate", response.text)

    def test_healthz_is_available(self) -> None:
        client = TestClient(app)
        response = client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_v2_error_response_uses_top_level_message_contract(self) -> None:
        demo = FastAPI()
        install_error_handlers(demo)

        @demo.get("/conflict")
        def conflict() -> None:
            raise ConflictError("环境配置名称已存在，请更换后重试。", code="ENV_PROFILE_NAME_CONFLICT")

        client = TestClient(demo)
        response = client.get("/conflict")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json(),
            {
                "message": "环境配置名称已存在，请更换后重试。",
                "type": "ConflictError",
                "code": "ENV_PROFILE_NAME_CONFLICT",
                "status": 409,
            },
        )

    def test_unexpected_error_response_uses_internal_error_contract(self) -> None:
        demo = FastAPI()
        install_error_handlers(demo)

        @demo.get("/boom")
        def boom() -> None:
            raise RuntimeError("db offline")

        client = TestClient(demo, raise_server_exceptions=False)
        response = client.get("/boom")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {
                "message": "服务器内部错误，请稍后重试。",
                "type": "RuntimeError",
                "code": "INTERNAL_ERROR",
                "status": 500,
            },
        )


if __name__ == "__main__":
    unittest.main()
