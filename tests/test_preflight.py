from pathlib import Path
import unittest

from secureagentrag.preflight import empirical_pilot_preflight


ROOT = Path(__file__).resolve().parents[1]


class PreflightTests(unittest.TestCase):
    def test_protocol_matrix_resolves_to_1944(self) -> None:
        report = empirical_pilot_preflight(ROOT)
        self.assertEqual(report.expected_observations, 1944)

    def test_unreviewed_localizations_block_empirical_run(self) -> None:
        report = empirical_pilot_preflight(ROOT)
        self.assertFalse(report.ready)
        self.assertTrue(any("translation_pending" in item for item in report.blockers))

    def test_live_provider_configs_are_required(self) -> None:
        report = empirical_pilot_preflight(ROOT)
        for provider in ("aws", "azure", "open_weight"):
            self.assertTrue(any(provider in item for item in report.blockers))


if __name__ == "__main__":
    unittest.main()
