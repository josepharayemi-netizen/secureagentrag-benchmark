from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .models import THREAT_CLASSES, Scenario


def load_scenarios(path: str | Path) -> list[Scenario]:
    source = Path(path)
    scenarios: list[Scenario] = []
    with source.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                scenarios.append(Scenario.from_dict(json.loads(line)))
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                raise ValueError(f"invalid scenario at line {line_number}: {exc}") from exc
    return scenarios


def validate_dataset(scenarios: list[Scenario], expected_count: int = 36) -> list[str]:
    errors: list[str] = []
    if len(scenarios) != expected_count:
        errors.append(f"expected {expected_count} scenarios, found {len(scenarios)}")

    ids = [scenario.scenario_id for scenario in scenarios]
    duplicates = sorted(key for key, count in Counter(ids).items() if count > 1)
    if duplicates:
        errors.append(f"duplicate scenario identifiers: {', '.join(duplicates)}")

    counts = Counter(scenario.threat_class for scenario in scenarios)
    for threat_class in sorted(THREAT_CLASSES):
        if counts[threat_class] != 6:
            errors.append(
                f"expected 6 scenarios for {threat_class}, found {counts[threat_class]}"
            )

    for scenario in scenarios:
        for message in scenario.validate():
            errors.append(f"{scenario.scenario_id}: {message}")
        combined = " ".join(
            [
                scenario.benign_request,
                scenario.untrusted_content,
                *scenario.sensitive_markers,
            ]
        ).lower()
        if "synthetic" not in combined and scenario.sensitive_markers:
            errors.append(
                f"{scenario.scenario_id}: sensitive markers must be visibly synthetic"
            )
    return errors
