from pathlib import Path
import unittest

from secureagentrag.dataset import load_scenarios, validate_dataset


ROOT = Path(__file__).resolve().parents[1]


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenarios = load_scenarios(ROOT / "data" / "scenarios.jsonl")

    def test_dataset_is_valid(self) -> None:
        self.assertEqual(validate_dataset(self.scenarios), [])

    def test_balanced_threat_classes(self) -> None:
        counts: dict[str, int] = {}
        for scenario in self.scenarios:
            counts[scenario.threat_class] = counts.get(scenario.threat_class, 0) + 1
        self.assertEqual(set(counts.values()), {6})
        self.assertEqual(sum(counts.values()), 36)

    def test_identifiers_are_unique(self) -> None:
        identifiers = [scenario.scenario_id for scenario in self.scenarios]
        self.assertEqual(len(identifiers), len(set(identifiers)))


if __name__ == "__main__":
    unittest.main()
