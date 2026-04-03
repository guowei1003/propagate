from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class AppEntryTestCase(unittest.TestCase):
    def test_root_serves_v2_entry(self) -> None:
        client = TestClient(app)
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Propagate V2", response.text)

    def test_healthz_is_available(self) -> None:
        client = TestClient(app)
        response = client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
