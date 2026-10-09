#!/usr/bin/env python3
"""Run the prespecified 1,944-observation pilot after every evidence gate passes."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from secureagentrag.dataset import load_scenarios, validate_dataset
from secureagentrag.preflight import empirical_pilot_preflight
from secureagentrag.providers import AWSBedrockRAGAdapter, AzureRAGAdapter, OpenWeightRAGAdapter
from secureagentrag.reporting import summarize, write_summary
from secureagentrag.runner import run_benchmark


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "fr", "ar", "sw", "yo", "ha")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    preflight = empirical_pilot_preflight(ROOT)
    if not preflight.ready:
        print(json.dumps(preflight.as_dict(), indent=2))
        print("Empirical pilot blocked; resolve the listed evidence gates before any API call.")
        return 2

    scenarios = []
    dataset_paths: list[Path] = []
    for language in LANGUAGES:
        path = (
            ROOT / "data" / "scenarios.jsonl"
            if language == "en"
            else ROOT / "data" / "locales" / f"{language}.jsonl"
        )
        localized = load_scenarios(path)
        errors = validate_dataset(localized, expected_language=language)
        if errors:
            raise ValueError(errors[0])
        scenarios.extend(localized)
        dataset_paths.append(path)

    adapters = (
        AWSBedrockRAGAdapter.from_config(ROOT / "configs" / "providers" / "aws.json"),
        AzureRAGAdapter.from_config(ROOT / "configs" / "providers" / "azure.json"),
        OpenWeightRAGAdapter.from_config(
            ROOT / "configs" / "providers" / "open_weight.json"
        ),
    )
    output_dir = ROOT / "results" / "empirical_pilot"
    output_dir.mkdir(parents=True, exist_ok=True)
    combined: list[dict[str, object]] = []
    for adapter in adapters:
        path = output_dir / f"{adapter.name}.jsonl"
        records = run_benchmark(scenarios, adapter, ("C0", "C1", "C2"), (0,), path)
        combined.extend(records)
        write_summary(summarize(records), output_dir / f"{adapter.name}_summary.json")

    if len(combined) != preflight.expected_observations:
        raise RuntimeError(
            f"expected {preflight.expected_observations} observations, produced {len(combined)}"
        )
    write_summary(summarize(combined), output_dir / "combined_summary.json")
    config_paths = [
        ROOT / "configs" / "experiment.json",
        ROOT / "configs" / "providers" / "aws.json",
        ROOT / "configs" / "providers" / "azure.json",
        ROOT / "configs" / "providers" / "open_weight.json",
    ]
    manifest = {
        "schema_version": "0.1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "observations": len(combined),
        "dataset_sha256": {
            str(path.relative_to(ROOT)): _sha256(path) for path in dataset_paths
        },
        "config_sha256": {
            str(path.relative_to(ROOT)): _sha256(path) for path in config_paths
        },
        "adapters": [adapter.name for adapter in adapters],
        "configurations": ["C0", "C1", "C2"],
        "seed": 0,
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "complete", "observations": len(combined)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
