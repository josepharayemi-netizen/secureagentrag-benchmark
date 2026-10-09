#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

from secureagentrag.dataset import load_scenarios


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = {
    "fr": "French",
    "ar": "Arabic",
    "sw": "Swahili",
    "yo": "Yoruba",
    "ha": "Hausa",
}
FIELDS = [
    "scenario_id",
    "threat_class",
    "sector",
    "target_language",
    "source_benign_request",
    "target_benign_request",
    "source_untrusted_content",
    "target_untrusted_content",
    "source_expected_safe_behavior",
    "target_expected_safe_behavior",
    "source_expected_utility_behavior",
    "target_expected_utility_behavior",
    "translator_name",
    "reviewer_name",
    "semantic_equivalence",
    "cultural_clarity",
    "attack_strength_preserved",
    "named_entities_preserved",
    "review_notes",
    "review_status",
]


def main() -> None:
    scenarios = load_scenarios(ROOT / "data" / "scenarios.jsonl")
    output_dir = ROOT / "translation_workbooks"
    output_dir.mkdir(parents=True, exist_ok=True)
    for language, language_name in LANGUAGES.items():
        path = output_dir / f"secureagentrag_{language}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            for scenario in scenarios:
                writer.writerow(
                    {
                        "scenario_id": scenario.scenario_id,
                        "threat_class": scenario.threat_class,
                        "sector": scenario.sector,
                        "target_language": language_name,
                        "source_benign_request": scenario.benign_request,
                        "source_untrusted_content": scenario.untrusted_content,
                        "source_expected_safe_behavior": scenario.expected_safe_behavior,
                        "source_expected_utility_behavior": scenario.expected_utility_behavior,
                        "review_status": "translation_pending",
                    }
                )
        print(f"wrote {len(scenarios)} rows to {path}")


if __name__ == "__main__":
    main()
