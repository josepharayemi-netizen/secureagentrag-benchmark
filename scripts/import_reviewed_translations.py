#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

from secureagentrag.dataset import load_scenarios, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
TARGET_FIELDS = {
    "benign_request": "target_benign_request",
    "untrusted_content": "target_untrusted_content",
    "expected_safe_behavior": "target_expected_safe_behavior",
    "expected_utility_behavior": "target_expected_utility_behavior",
}
CHECKS = (
    "semantic_equivalence",
    "cultural_clarity",
    "attack_strength_preserved",
    "named_entities_preserved",
)


def import_language(language: str) -> Path:
    if language not in {"fr", "ar", "sw", "yo", "ha"}:
        raise ValueError(f"unsupported target language: {language}")
    source = {item.scenario_id: item for item in load_scenarios(ROOT / "data" / "scenarios.jsonl")}
    workbook = ROOT / "translation_workbooks" / f"secureagentrag_{language}.csv"
    records: list[dict[str, object]] = []
    with workbook.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 36:
        raise ValueError(f"expected 36 workbook rows, found {len(rows)}")
    for row_number, row in enumerate(rows, start=2):
        missing = [field for field in TARGET_FIELDS.values() if not row.get(field, "").strip()]
        if missing:
            raise ValueError(f"row {row_number} missing translated fields: {', '.join(missing)}")
        if not row.get("translator_name", "").strip() or not row.get("reviewer_name", "").strip():
            raise ValueError(f"row {row_number} requires translator and reviewer names")
        failed = [field for field in CHECKS if row.get(field, "").strip().casefold() != "yes"]
        if failed:
            raise ValueError(f"row {row_number} has incomplete review checks: {', '.join(failed)}")
        if row.get("review_status", "").strip() != "review_approved":
            raise ValueError(f"row {row_number} is not review_approved")
        scenario = source[row["scenario_id"]]
        value = asdict(scenario)
        for field in (
            "trusted_instructions",
            "authorized_resources",
            "allowed_tools",
            "forbidden_tools",
            "sensitive_markers",
            "attack_indicators",
        ):
            value[field] = list(value[field])
        for destination, workbook_field in TARGET_FIELDS.items():
            value[destination] = row[workbook_field].strip()
        value["source_language"] = language
        value["human_review_status"] = "review_approved"
        records.append(value)

    destination = ROOT / "data" / "locales" / f"{language}.jsonl"
    with destination.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    scenarios = load_scenarios(destination)
    errors = validate_dataset(scenarios, expected_language=language)
    if errors:
        destination.unlink(missing_ok=True)
        raise ValueError(errors[0])
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("language", choices=["fr", "ar", "sw", "yo", "ha"])
    args = parser.parse_args()
    path = import_language(args.language)
    print(f"created validated localized dataset: {path}")
    print("A project maintainer must separately verify the workbook and update the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
