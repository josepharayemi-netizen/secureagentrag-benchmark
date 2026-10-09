from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import AgentDecision, Scenario, ToolCall
from .common import (
    RetrievedDocument,
    estimate_cost,
    exposed_tools,
    generic_tool_schema,
    load_provider_config,
    prepare_documents,
    prompt_text,
    system_instructions,
)


@dataclass
class AWSBedrockRAGAdapter:
    """Bedrock Knowledge Bases + Converse adapter with inert tool proposals."""

    runtime_client: Any
    retrieval_client: Any
    config: dict[str, Any]
    name: str = "aws-bedrock-rag"

    @classmethod
    def from_config(cls, path: str | Path) -> "AWSBedrockRAGAdapter":
        config = load_provider_config(path)
        if config.get("provider") != "aws":
            raise ValueError("AWS adapter requires provider='aws'")
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("Install the 'aws' project extra to run Bedrock experiments") from exc
        session = boto3.Session(region_name=config["region"])
        return cls(
            runtime_client=session.client("bedrock-runtime"),
            retrieval_client=session.client("bedrock-agent-runtime"),
            config=config,
        )

    def run(self, scenario: Scenario, configuration: str, seed: int) -> AgentDecision:
        started = time.perf_counter()
        retrieval = self.retrieval_client.retrieve(
            knowledgeBaseId=self.config["knowledge_base_id"],
            retrievalQuery={"text": scenario.benign_request},
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": int(self.config.get("top_k", 5))}
            },
        )
        documents = tuple(self._documents(retrieval.get("retrievalResults", [])))
        prepared = prepare_documents(documents, scenario, configuration)

        request: dict[str, Any] = {
            "modelId": self.config["model_id"],
            "system": [{"text": system_instructions(configuration)}],
            "messages": [
                {"role": "user", "content": [{"text": prompt_text(scenario, prepared)}]}
            ],
            "inferenceConfig": {
                "temperature": float(self.config.get("temperature", 0.0)),
                "maxTokens": int(self.config.get("max_tokens", 512)),
            },
            "toolConfig": {
                "tools": [
                    {
                        "toolSpec": {
                            "name": schema["name"],
                            "description": schema["description"],
                            "inputSchema": {"json": schema["input_schema"]},
                        }
                    }
                    for schema in (
                        generic_tool_schema(name) for name in exposed_tools(scenario, configuration)
                    )
                ]
            },
        }
        if configuration == "C2" and self.config.get("guardrail_id"):
            request["guardrailConfig"] = {
                "guardrailIdentifier": self.config["guardrail_id"],
                "guardrailVersion": self.config["guardrail_version"],
                "trace": "enabled",
            }

        response = self.runtime_client.converse(**request)
        content = response.get("output", {}).get("message", {}).get("content", [])
        text_parts = [part.get("text", "") for part in content if "text" in part]
        calls = tuple(
            ToolCall(
                name=part["toolUse"]["name"],
                arguments=dict(part["toolUse"].get("input", {})),
            )
            for part in content
            if "toolUse" in part
        )
        usage = response.get("usage", {})
        input_tokens = int(usage.get("inputTokens", 0))
        output_tokens = int(usage.get("outputTokens", 0))
        response_text = "\n".join(part for part in text_parts if part).strip()
        refused = response.get("stopReason") in {"guardrail_intervened", "content_filtered"}
        return AgentDecision(
            response=response_text,
            tool_calls=calls,
            refused=refused,
            grounded=bool(prepared) and not refused,
            latency_ms=(time.perf_counter() - started) * 1000,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=estimate_cost(input_tokens, output_tokens, self.config.get("pricing")),
        )

    @staticmethod
    def _documents(results: list[dict[str, Any]]) -> list[RetrievedDocument]:
        documents: list[RetrievedDocument] = []
        for index, result in enumerate(results):
            content = result.get("content", {})
            text = content.get("text") or json.dumps(content, ensure_ascii=False)
            location = result.get("location", {})
            source = json.dumps(location, sort_keys=True) if location else f"aws-result-{index}"
            documents.append(
                RetrievedDocument(text=text, source=source, metadata=dict(result.get("metadata", {})))
            )
        return documents
