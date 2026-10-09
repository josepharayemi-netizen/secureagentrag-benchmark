from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


THREAT_CLASSES = {
    "direct_prompt_injection",
    "indirect_prompt_injection",
    "retrieval_poisoning",
    "privacy_leakage",
    "unauthorized_tool_use",
    "benign_control",
}

CONFIGURATIONS = {"C0", "C1", "C2"}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    title: str
    threat_class: str
    sector: str
    severity: str
    source_language: str
    user_role: str
    benign_request: str
    trusted_instructions: tuple[str, ...]
    untrusted_content: str
    authorized_resources: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...]
    sensitive_markers: tuple[str, ...]
    attack_indicators: tuple[str, ...]
    expected_safe_behavior: str
    expected_utility_behavior: str
    human_review_status: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Scenario":
        sequence_fields = {
            "trusted_instructions",
            "authorized_resources",
            "allowed_tools",
            "forbidden_tools",
            "sensitive_markers",
            "attack_indicators",
        }
        payload = dict(value)
        for name in sequence_fields:
            payload[name] = tuple(payload.get(name, []))
        return cls(**payload)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.scenario_id.startswith("sar-"):
            errors.append("scenario_id must begin with 'sar-'")
        if self.threat_class not in THREAT_CLASSES:
            errors.append(f"unsupported threat_class: {self.threat_class}")
        if self.severity not in {"low", "medium", "high"}:
            errors.append(f"unsupported severity: {self.severity}")
        if self.source_language != "en":
            errors.append("v0.1 source scenarios must use English ('en')")
        if self.human_review_status != "source_approved":
            errors.append("source scenario has not passed its review gate")
        if not self.trusted_instructions:
            errors.append("trusted_instructions cannot be empty")
        if not self.expected_safe_behavior or not self.expected_utility_behavior:
            errors.append("expected behaviours cannot be empty")
        if self.threat_class == "benign_control" and self.attack_indicators:
            errors.append("benign controls cannot contain attack indicators")
        return errors


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentDecision:
    response: str
    tool_calls: tuple[ToolCall, ...] = ()
    refused: bool = False
    grounded: bool = True
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


@dataclass(frozen=True)
class Score:
    attack_success: bool
    sensitive_data_exposure: bool
    unauthorized_tool_invocation: bool
    over_refusal: bool
    benign_task_completion: bool
    grounded_answer: bool
    leaked_markers: tuple[str, ...] = ()
    unauthorized_tools: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "attack_success": self.attack_success,
            "sensitive_data_exposure": self.sensitive_data_exposure,
            "unauthorized_tool_invocation": self.unauthorized_tool_invocation,
            "over_refusal": self.over_refusal,
            "benign_task_completion": self.benign_task_completion,
            "grounded_answer": self.grounded_answer,
            "leaked_markers": list(self.leaked_markers),
            "unauthorized_tools": list(self.unauthorized_tools),
        }
