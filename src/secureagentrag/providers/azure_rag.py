from __future__ import annotations

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
class AzureRAGAdapter:
    """Azure AI Search + Azure OpenAI adapter with managed-identity support."""

    search_client: Any
    model_client: Any
    config: dict[str, Any]
    name: str = "azure-ai-search-openai-rag"

    @classmethod
    def from_config(cls, path: str | Path) -> "AzureRAGAdapter":
        config = load_provider_config(path)
        if config.get("provider") != "azure":
            raise ValueError("Azure adapter requires provider='azure'")
        try:
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
            from azure.search.documents import SearchClient
            from openai import AzureOpenAI
        except ImportError as exc:
            raise RuntimeError("Install the 'azure' project extra to run Azure experiments") from exc

        credential = DefaultAzureCredential()
        search_client = SearchClient(
            endpoint=config["search_endpoint"],
            index_name=config["search_index"],
            credential=credential,
        )
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        model_client = AzureOpenAI(
            azure_endpoint=config["azure_openai_endpoint"],
            api_version=config["api_version"],
            azure_ad_token_provider=token_provider,
        )
        return cls(search_client=search_client, model_client=model_client, config=config)

    def run(self, scenario: Scenario, configuration: str, seed: int) -> AgentDecision:
        started = time.perf_counter()
        fields = self.config.get("select_fields", ["content", "source", "authorized_roles"])
        results = self.search_client.search(
            search_text=scenario.benign_request,
            top=int(self.config.get("top_k", 5)),
            select=fields,
        )
        documents = tuple(self._documents(results))
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
            model=self.config["model_deployment"],
            messages=[
                {"role": "system", "content": system_instructions(configuration)},
                {"role": "user", "content": prompt_text(scenario, prepared)},
            ],
            tools=tools,
            temperature=float(self.config.get("temperature", 0.0)),
            max_tokens=int(self.config.get("max_tokens", 512)),
            seed=seed,
        )
        choice = completion.choices[0]
        message = choice.message
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
    def _documents(results: Any) -> list[RetrievedDocument]:
        documents: list[RetrievedDocument] = []
        for index, item in enumerate(results):
            value = dict(item)
            documents.append(
                RetrievedDocument(
                    text=str(value.get("content", "")),
                    source=str(value.get("source", f"azure-result-{index}")),
                    metadata={"authorized_roles": value.get("authorized_roles", [])},
                )
            )
        return documents

    @staticmethod
    def _arguments(value: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        import json

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {"raw": value}
        return parsed if isinstance(parsed, dict) else {"value": parsed}
