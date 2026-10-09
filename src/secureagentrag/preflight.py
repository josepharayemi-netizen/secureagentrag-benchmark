from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .dataset import load_scenarios, validate_dataset


@dataclass(frozen=True)
class PreflightReport:
    ready: bool
    expected_observations: int
    checks: tuple[str, ...]
    blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "expected_observations": self.expected_observations,
            "checks": list(self.checks),
            "blockers": list(self.blockers),
        }


def empirical_pilot_preflight(root: str | Path) -> PreflightReport:
    project = Path(root)
    experiment = _read_json(project / "configs" / "experiment.json")
    manifest = _read_json(project / "data" / "locales" / "manifest.json")
    languages = list(experiment["languages"])
    configurations = list(experiment["configurations"])
    pilot_seeds = list(experiment.get("pilot_seeds", [0]))
    expected = (
        int(experiment["base_scenarios"])
        * len(languages)
        * len(configurations)
        * int(experiment["model_backends"])
        * len(pilot_seeds)
    )
    checks: list[str] = [f"experimental matrix resolves to {expected} pilot observations"]
    blockers: list[str] = []

    for language in languages:
        status = manifest.get("languages", {}).get(language, {}).get("status")
        if status not in {"source_approved", "review_approved"}:
            blockers.append(f"language {language} has status {status or 'missing'}")
        workbook = project / "translation_workbooks" / f"secureagentrag_{language}.csv"
        if language != "en" and not workbook.exists():
            blockers.append(f"translation workbook missing for {language}")
        if language != "en":
            localized = project / "data" / "locales" / f"{language}.jsonl"
            if not localized.exists():
                blockers.append(f"approved localized dataset missing for {language}")
            else:
                validation_errors = validate_dataset(
                    load_scenarios(localized), expected_language=language
                )
                if validation_errors:
                    blockers.append(
                        f"localized dataset {language} failed validation: {validation_errors[0]}"
                    )

    for provider in ("aws", "azure", "open_weight"):
        config_path = project / "configs" / "providers" / f"{provider}.json"
        if not config_path.exists():
            blockers.append(f"live provider config missing: {config_path.relative_to(project)}")
            continue
        config = _read_json(config_path)
        if config.get("status") != "configured":
            blockers.append(f"provider {provider} is not marked configured")
        placeholders = _placeholder_paths(config)
        if placeholders:
            blockers.append(f"provider {provider} has unresolved fields: {', '.join(placeholders)}")

    if expected != int(experiment["pilot_observations"]):
        blockers.append(
            f"calculated pilot size {expected} does not match declared {experiment['pilot_observations']}"
        )
    if not blockers:
        checks.append("all localization and provider release gates passed")
    return PreflightReport(
        ready=not blockers,
        expected_observations=expected,
        checks=tuple(checks),
        blockers=tuple(blockers),
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _placeholder_paths(value: Any, path: str = "config") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            found.extend(_placeholder_paths(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_placeholder_paths(item, f"{path}[{index}]"))
    elif isinstance(value, str) and (value.startswith("SET_") or value == "REVIEW_REQUIRED"):
        found.append(path)
    return found
