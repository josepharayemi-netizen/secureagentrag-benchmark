from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "aws": ("region", "model_id", "knowledge_base_id", "guardrail_id", "guardrail_version"),
    "azure": (
        "region",
        "model_deployment",
        "azure_openai_endpoint",
        "api_version",
        "search_endpoint",
        "search_index",
    ),
    "open_weight": ("endpoint", "model_id", "corpus_path", "deployment_environment"),
}
SECRET_FIELD_NAMES = {
    "access_key",
    "access_key_id",
    "api_key",
    "client_secret",
    "connection_string",
    "password",
    "private_key",
    "secret_access_key",
    "token",
}


@dataclass(frozen=True)
class ProviderConfigAudit:
    provider: str
    ready: bool
    estimated_max_run_usd: float | None
    blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "ready": self.ready,
            "estimated_max_run_usd": self.estimated_max_run_usd,
            "blockers": list(self.blockers),
        }


def audit_provider_config(
    path: str | Path, provider: str, observations: int
) -> ProviderConfigAudit:
    config_path = Path(path)
    if not config_path.exists():
        return ProviderConfigAudit(provider, False, None, ("configuration file missing",))
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return ProviderConfigAudit(provider, False, None, (f"invalid JSON: {exc}",))

    blockers: list[str] = []
    if config.get("provider") != provider:
        blockers.append(f"provider must equal {provider}")
    if config.get("status") != "configured":
        blockers.append("status must equal configured")
    for field in REQUIRED_FIELDS[provider]:
        if field not in config or config[field] in (None, ""):
            blockers.append(f"required field is missing: {field}")
    unresolved = _placeholder_paths(config)
    if unresolved:
        blockers.append(f"unresolved placeholders: {', '.join(unresolved)}")
    secret_paths = _secret_paths(config)
    if secret_paths:
        blockers.append(f"credential material must not appear in config: {', '.join(secret_paths)}")

    for field in ("top_k", "max_tokens"):
        if not isinstance(config.get(field), int) or config[field] <= 0:
            blockers.append(f"{field} must be a positive integer")
    temperature = config.get("temperature")
    if not isinstance(temperature, (int, float)) or not 0 <= temperature <= 2:
        blockers.append("temperature must be between 0 and 2")
    if config.get("data_policy") != "Synthetic benchmark data only.":
        blockers.append("data_policy must restrict the run to synthetic benchmark data")

    estimated = _estimated_cost(config, observations, blockers)
    return ProviderConfigAudit(provider, not blockers, estimated, tuple(blockers))


def _estimated_cost(
    config: dict[str, Any], observations: int, blockers: list[str]
) -> float | None:
    pricing = config.get("pricing", {})
    budget = config.get("budget", {})
    values = {
        "pricing.input_per_1k_usd": pricing.get("input_per_1k_usd"),
        "pricing.output_per_1k_usd": pricing.get("output_per_1k_usd"),
        "generation.max_output_tokens": config.get("max_tokens"),
        "budget.max_input_tokens_per_observation": budget.get(
            "max_input_tokens_per_observation"
        ),
        "budget.max_run_usd": budget.get("max_run_usd"),
    }
    for path, value in values.items():
        if not isinstance(value, (int, float)) or value < 0:
            blockers.append(f"{path} must be a non-negative number")
    if any(not isinstance(value, (int, float)) or value < 0 for value in values.values()):
        return None
    estimate = observations * (
        values["budget.max_input_tokens_per_observation"]
        * values["pricing.input_per_1k_usd"]
        / 1000
        + values["generation.max_output_tokens"]
        * values["pricing.output_per_1k_usd"]
        / 1000
    )
    estimate = round(estimate, 4)
    if estimate > values["budget.max_run_usd"]:
        blockers.append(
            f"estimated maximum ${estimate:.4f} exceeds budget ${values['budget.max_run_usd']:.4f}"
        )
    return estimate


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


def _secret_paths(value: Any, path: str = "config") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            item_path = f"{path}.{key}"
            if key.casefold() in SECRET_FIELD_NAMES and item not in (None, ""):
                found.append(item_path)
            found.extend(_secret_paths(item, item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_secret_paths(item, f"{path}[{index}]"))
    return found
