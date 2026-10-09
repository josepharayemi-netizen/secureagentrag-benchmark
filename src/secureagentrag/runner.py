from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .adapters import AgentAdapter
from .models import CONFIGURATIONS, Scenario
from .scoring import score_decision


def run_benchmark(
    scenarios: Iterable[Scenario],
    adapter: AgentAdapter,
    configurations: Iterable[str],
    seeds: Iterable[int],
    output_path: str | Path,
) -> list[dict[str, object]]:
    selected = tuple(configurations)
    unknown = sorted(set(selected) - CONFIGURATIONS)
    if unknown:
        raise ValueError(f"unknown configurations: {', '.join(unknown)}")

    records: list[dict[str, object]] = []
    for scenario in scenarios:
        for configuration in selected:
            for seed in seeds:
                decision = adapter.run(scenario, configuration, seed)
                score = score_decision(scenario, decision)
                records.append(
                    {
                        "schema_version": "0.1.0",
                        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        "scenario_id": scenario.scenario_id,
                        "threat_class": scenario.threat_class,
                        "sector": scenario.sector,
                        "language": scenario.source_language,
                        "configuration": configuration,
                        "adapter": adapter.name,
                        "seed": seed,
                        "decision": {
                            "response": decision.response,
                            "tool_calls": [
                                {"name": call.name, "arguments": call.arguments}
                                for call in decision.tool_calls
                            ],
                            "refused": decision.refused,
                            "grounded": decision.grounded,
                            "latency_ms": decision.latency_ms,
                            "input_tokens": decision.input_tokens,
                            "output_tokens": decision.output_tokens,
                            "cost_usd": decision.cost_usd,
                        },
                        "score": score.as_dict(),
                    }
                )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return records
