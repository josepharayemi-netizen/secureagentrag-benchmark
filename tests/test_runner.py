from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from secureagentrag.adapters import DeterministicMockAdapter
from secureagentrag.dataset import load_scenarios
from secureagentrag.reporting import summarize
from secureagentrag.runner import run_benchmark


ROOT = Path(__file__).resolve().parents[1]


class RunnerTests(unittest.TestCase):
    def test_mock_pilot_has_expected_observations(self) -> None:
        scenarios = load_scenarios(ROOT / "data" / "scenarios.jsonl")
        with TemporaryDirectory() as temporary:
            records = run_benchmark(
                scenarios,
                DeterministicMockAdapter(),
                ("C0", "C1", "C2"),
                (0, 1, 2),
                Path(temporary) / "results.jsonl",
            )
        self.assertEqual(len(records), 324)
        self.assertEqual(summarize(records)["overall"]["observations"], 324)

    def test_mock_adapter_is_deterministic(self) -> None:
        scenario = load_scenarios(ROOT / "data" / "scenarios.jsonl")[0]
        adapter = DeterministicMockAdapter()
        self.assertEqual(adapter.run(scenario, "C2", 7), adapter.run(scenario, "C2", 7))


if __name__ == "__main__":
    unittest.main()
