import json
from pathlib import Path
import tempfile
import unittest

from secureagentrag.configuration import audit_provider_config


def valid_aws_config() -> dict[str, object]:
    return {
        "provider": "aws",
        "status": "configured",
        "region": "eu-west-1",
        "model_id": "example.version-2026",
        "knowledge_base_id": "KBEXAMPLE",
        "guardrail_id": "GREXAMPLE",
        "guardrail_version": "1",
        "top_k": 5,
        "temperature": 0.0,
        "max_tokens": 512,
        "pricing": {"input_per_1k_usd": 0.001, "output_per_1k_usd": 0.002},
        "budget": {"max_input_tokens_per_observation": 4096, "max_run_usd": 10.0},
        "credentials": "Use the external AWS credential chain.",
        "data_policy": "Synthetic benchmark data only.",
    }


class ConfigurationTests(unittest.TestCase):
    def _audit(self, config: dict[str, object]):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aws.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            return audit_provider_config(path, "aws", observations=648)

    def test_valid_config_has_bounded_estimate(self) -> None:
        audit = self._audit(valid_aws_config())
        self.assertTrue(audit.ready)
        self.assertIsNotNone(audit.estimated_max_run_usd)
        self.assertLess(audit.estimated_max_run_usd, 10.0)

    def test_embedded_secret_is_rejected(self) -> None:
        config = valid_aws_config()
        config["access_key_id"] = "must-not-be-committed"
        audit = self._audit(config)
        self.assertFalse(audit.ready)
        self.assertTrue(any("credential material" in item for item in audit.blockers))

    def test_budget_overrun_is_rejected(self) -> None:
        config = valid_aws_config()
        config["budget"]["max_run_usd"] = 1.0  # type: ignore[index]
        audit = self._audit(config)
        self.assertFalse(audit.ready)
        self.assertTrue(any("exceeds budget" in item for item in audit.blockers))


if __name__ == "__main__":
    unittest.main()
