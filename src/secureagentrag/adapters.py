from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from .models import AgentDecision, Scenario, ToolCall


class AgentAdapter(Protocol):
    name: str

    def run(self, scenario: Scenario, configuration: str, seed: int) -> AgentDecision:
        """Return one isolated decision for a scenario."""


def _fraction(*parts: object) -> float:
    value = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(value).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64)


@dataclass(frozen=True)
class DeterministicMockAdapter:
    """Safe CI simulator. Its outputs are not empirical model findings."""

    name: str = "deterministic-mock"

    def run(self, scenario: Scenario, configuration: str, seed: int) -> AgentDecision:
        if configuration not in {"C0", "C1", "C2"}:
            raise ValueError(f"unknown configuration: {configuration}")

        if scenario.threat_class == "benign_control":
            refusal_rate = {"C0": 0.02, "C1": 0.06, "C2": 0.10}[configuration]
            refused = _fraction(scenario.scenario_id, configuration, seed, "utility") < refusal_rate
            response = (
                "Request declined by the simulated policy."
                if refused
                else f"Completed the synthetic task safely: {scenario.expected_utility_behavior}"
            )
            return AgentDecision(
                response=response,
                refused=refused,
                grounded=True,
                latency_ms=25 + 8 * (ord(configuration[-1]) - ord("0")),
                input_tokens=120,
                output_tokens=48,
                cost_usd=0.0,
            )

        vulnerable_rate = {"C0": 0.66, "C1": 0.34, "C2": 0.12}[configuration]
        compromised = _fraction(scenario.scenario_id, configuration, seed, "security") < vulnerable_rate
        tool_calls: tuple[ToolCall, ...] = ()
        response = "Untrusted instructions ignored; authorized task completed with synthetic data."
        if compromised:
            if scenario.sensitive_markers:
                response = f"Simulated unsafe disclosure: {scenario.sensitive_markers[0]}"
            elif scenario.forbidden_tools:
                tool_calls = (
                    ToolCall(
                        name=scenario.forbidden_tools[0],
                        arguments={"reason": "synthetic benchmark simulation"},
                    ),
                )
            elif scenario.attack_indicators:
                response = f"Simulated unsafe outcome: {scenario.attack_indicators[0]}"

        return AgentDecision(
            response=response,
            tool_calls=tool_calls,
            refused=False,
            grounded=not compromised,
            latency_ms=30 + 12 * (ord(configuration[-1]) - ord("0")),
            input_tokens=180,
            output_tokens=64,
            cost_usd=0.0,
        )
