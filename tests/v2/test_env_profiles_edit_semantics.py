from __future__ import annotations

import unittest

from app.v2.modules.env_profiles.service import merge_profile_update_payload


class EnvProfilesEditSemanticsTestCase(unittest.TestCase):
    def test_blank_api_key_keeps_existing_value(self) -> None:
        existing = {"api_key": "secret", "name": "prod", "provider_type": "openai_compatible"}
        incoming = {"api_key": "", "name": "prod-v2", "provider_type": "openai_compatible"}
        merged = merge_profile_update_payload(existing, incoming)
        self.assertEqual(merged["api_key"], "secret")
        self.assertEqual(merged["name"], "prod-v2")


if __name__ == "__main__":
    unittest.main()
