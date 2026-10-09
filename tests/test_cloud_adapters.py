from pathlib import Path
from types import SimpleNamespace
import unittest

from secureagentrag.dataset import load_scenarios
from secureagentrag.providers.aws_bedrock import AWSBedrockRAGAdapter
from secureagentrag.providers.azure_rag import AzureRAGAdapter
from secureagentrag.providers.common import RetrievedDocument
from secureagentrag.providers.open_weight import OpenWeightRAGAdapter


ROOT = Path(__file__).resolve().parents[1]


class FakeAWSRetrieval:
    def retrieve(self, **kwargs):
        self.request = kwargs
        return {
            "retrievalResults": [
                {
                    "content": {"text": "Record contains SYNTHETIC-SECRET-BANKING-01"},
                    "location": {"s3Location": {"uri": "s3://synthetic/doc"}},
                    "metadata": {"authorized_roles": ["customer_service_analyst"]},
                }
            ]
        }


class FakeAWSRuntime:
    def converse(self, **kwargs):
        self.request = kwargs
        return {
            "output": {"message": {"content": [{"text": "Grounded synthetic answer"}]}},
            "usage": {"inputTokens": 100, "outputTokens": 20},
            "stopReason": "end_turn",
        }


class FakeSearch:
    def search(self, **kwargs):
        self.request = kwargs
        return [
            {
                "content": "Authorized synthetic search result",
                "source": "azure://synthetic/doc",
                "authorized_roles": ["customer_service_analyst"],
            }
        ]


class FakeCompletions:
    def create(self, **kwargs):
        self.request = kwargs
        message = SimpleNamespace(content="Grounded synthetic answer", tool_calls=[], refusal=None)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message)],
            usage=SimpleNamespace(prompt_tokens=90, completion_tokens=18),
        )


class CloudAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        scenarios = load_scenarios(ROOT / "data" / "scenarios.jsonl")
        cls.privacy = next(item for item in scenarios if item.scenario_id == "sar-prv-01")

    def test_aws_c2_masks_marker_and_exposes_only_allowed_tool(self) -> None:
        runtime = FakeAWSRuntime()
        adapter = AWSBedrockRAGAdapter(
            runtime,
            FakeAWSRetrieval(),
            {
                "knowledge_base_id": "kb-test",
                "model_id": "model-test",
                "guardrail_id": "guard-test",
                "guardrail_version": "1",
            },
        )
        decision = adapter.run(self.privacy, "C2", 0)
        prompt = runtime.request["messages"][0]["content"][0]["text"]
        tools = runtime.request["toolConfig"]["tools"]
        self.assertIn("[MASKED_SYNTHETIC_FIELD]", prompt)
        self.assertNotIn("SYNTHETIC-SECRET-BANKING-01", prompt)
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["toolSpec"]["name"], self.privacy.allowed_tools[0])
        self.assertEqual(decision.input_tokens, 100)

    def test_azure_c0_keeps_matched_tool_exposure(self) -> None:
        completions = FakeCompletions()
        model_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        adapter = AzureRAGAdapter(
            FakeSearch(),
            model_client,
            {"model_deployment": "deployment-test", "select_fields": ["content"]},
        )
        decision = adapter.run(self.privacy, "C0", 0)
        tool_names = {
            item["function"]["name"] for item in completions.request["tools"]
        }
        self.assertEqual(
            tool_names,
            set((*self.privacy.allowed_tools, *self.privacy.forbidden_tools)),
        )
        self.assertEqual(decision.output_tokens, 18)

    def test_open_weight_c2_uses_allowlist(self) -> None:
        completions = FakeCompletions()
        model_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

        class Retriever:
            def search(self, query, top_k):
                return [
                    RetrievedDocument(
                        text="Authorized synthetic context",
                        source="local://synthetic",
                        metadata={"authorized_roles": ["customer_service_analyst"]},
                    )
                ]

        adapter = OpenWeightRAGAdapter(
            Retriever(), model_client, {"model_id": "open-weight-test"}
        )
        adapter.run(self.privacy, "C2", 0)
        tool_names = {
            item["function"]["name"] for item in completions.request["tools"]
        }
        self.assertEqual(tool_names, set(self.privacy.allowed_tools))


if __name__ == "__main__":
    unittest.main()
