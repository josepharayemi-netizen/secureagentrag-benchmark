from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

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


class Retriever(Protocol):
    def search(self, query: str, top_k: int) -> list[RetrievedDocument]: ...


@dataclass
class JSONLKeywordRetriever:
    documents: tuple[RetrievedDocument, ...]

    @classmethod
    def from_path(cls, path: str | Path) -> "JSONLKeywordRetriever":
        documents: list[RetrievedDocument] = []
        with Path(path).open(encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if not line.strip():
                    continue
                value = json.loads(line)
                documents.append(
                    RetrievedDocument(
                        text=str(value["content"]),
                        source=str(value.get("source", f"local-{index}")),
                        metadata=dict(value.get("metadata", {})),
                    )
                )
        return cls(tuple(documents))

    def search(self, query: str, top_k: int) -> list[RetrievedDocument]:
        terms = {term.casefold() for term in query.split() if len(term) > 2}
        scored = []
        for document in self.documents:
            text_terms = set(document.text.casefold().split())
            scored.append((len(terms & text_terms), document.source, document))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [item[2] for item in scored[:top_k]]


@dataclass
class OpenWeightRAGAdapter:
    """OpenAI-compatible endpoint adapter for a version-pinned open-weight model."""

    retriever: Retriever
    model_client: Any
    config: dict[str, Any]
    name: str = "open-weight-openai-compatible-rag"

    @classmethod
    def from_config(cls, path: str | Path) -> "OpenWeightRAGAdapter":
        config = load_provider_config(path)
        if config.get("provider") != "open_weight":
            raise ValueError("Open-weight adapter requires provider='open_weight'")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the 'open-weight' project extra to run this adapter") from exc
        token = os.environ.get("SECUREAGENTRAG_OPEN_WEIGHT_TOKEN", "local-test-token")
        client = OpenAI(base_url=config["endpoint"], api_key=token)
        retriever = JSONLKeywordRetriever.from_path(config["corpus_path"])
        return cls(retriever=retriever, model_client=client, config=config)

    def run(self, scenario: Scenario, configuration: str, seed: int) -> AgentDecision:
        started = time.perf_counter()
        documents = self.retriever.search(
            scenario.benign_request, int(self.config.get("top_k", 5))
        )
        prepared = prepare_documents(documents, scenario, configuration)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema["description"],
                    "parameters": schema["input_schema"],
                },
            }
            for schema in (generic_tool_schema(name) for name in exposed_tools(scenario, configuration))
        ]
        completion = self.model_client.chat.completions.create(
            model=self.config["model_id"],
            messages=[
                {"role": "system", "content": system_instructions(configuration)},
                {"role": "user", "content": prompt_text(scenario, prepared)},
            ],
            tools=tools,
            temperature=float(self.config.get("temperature", 0.0)),
            max_tokens=int(self.config.get("max_tokens", 512)),
            seed=seed,
        )
        message = completion.choices[0].message
        calls = tuple(
            ToolCall(name=call.function.name, arguments=self._arguments(call.function.arguments))
            for call in (message.tool_calls or [])
        )
        input_tokens = int(getattr(completion.usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(completion.usage, "completion_tokens", 0) or 0)
        refused = getattr(message, "refusal", None) is not None
        return AgentDecision(
            response=message.content or "",
            tool_calls=calls,
            refused=refused,
            grounded=bool(prepared) and not refused,
            latency_ms=(time.perf_counter() - started) * 1000,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=estimate_cost(input_tokens, output_tokens, self.config.get("pricing")),
        )

    @staticmethod
    def _arguments(value: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {"raw": value}
        return parsed if isinstance(parsed, dict) else {"value": parsed}
