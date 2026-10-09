from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable


METRICS = (
    "attack_success",
    "sensitive_data_exposure",
    "unauthorized_tool_invocation",
    "over_refusal",
    "benign_task_completion",
    "grounded_answer",
)


def load_results(path: str | Path) -> list[dict[str, object]]:
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _aggregate(records: Iterable[dict[str, object]]) -> dict[str, object]:
    rows = list(records)
    total = len(rows)
    summary: dict[str, object] = {"observations": total}
    for metric in METRICS:
        positives = sum(bool(row["score"][metric]) for row in rows)  # type: ignore[index]
        summary[f"{metric}_count"] = positives
        summary[f"{metric}_rate"] = positives / total if total else 0.0
    return summary


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    by_configuration: dict[str, list[dict[str, object]]] = defaultdict(list)
    by_threat: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        by_configuration[str(record["configuration"])].append(record)
        by_threat[str(record["threat_class"])].append(record)
    return {
        "warning": "Deterministic mock outputs are CI smoke-test data, not empirical model findings.",
        "overall": _aggregate(records),
        "by_configuration": {
            key: _aggregate(value) for key, value in sorted(by_configuration.items())
        },
        "by_threat_class": {
            key: _aggregate(value) for key, value in sorted(by_threat.items())
        },
    }


def write_summary(summary: dict[str, object], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
