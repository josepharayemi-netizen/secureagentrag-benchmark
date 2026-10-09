# Cloud adapter guide

The AWS and Azure adapters are real client integrations designed for dedicated benchmark environments. They are not enabled by the committed example configurations.

## AWS Bedrock

`AWSBedrockRAGAdapter` retrieves synthetic documents through Amazon Bedrock Knowledge Bases and sends the controlled prompt to the Bedrock Converse API. It uses the standard AWS credential chain and does not accept secrets in the repository configuration.

1. Create a dedicated test knowledge base containing synthetic documents and authorization metadata.
2. Copy `configs/providers/aws.example.json` to `configs/providers/aws.json`.
3. Replace every placeholder, record current regional prices, and set `status` to `configured` only after review.
4. Grant a least-privilege role only the retrieval, model-invocation, guardrail and logging actions required by the test.
5. Install with `pip install -e '.[aws]'`.

## Microsoft Azure

`AzureRAGAdapter` retrieves synthetic documents through Azure AI Search and sends the controlled prompt to an Azure OpenAI deployment. It uses `DefaultAzureCredential`, supporting managed identity and workload identity without committed secrets.

1. Create a dedicated Azure AI Search index with `content`, `source` and `authorized_roles` fields.
2. Copy `configs/providers/azure.example.json` to `configs/providers/azure.json`.
3. Replace every placeholder, pin the deployment and API version, record pricing, and set `status` to `configured` only after review.
4. Assign least-privilege roles to the test identity.
5. Install with `pip install -e '.[azure]'`.

## Defense configurations

- **C0:** ordinary retrieval and minimally protected prompting; all synthetic benchmark tools are visible.
- **C1:** explicit instruction hierarchy and untrusted-content labeling; tool exposure remains matched to C0.
- **C2:** document-level role filtering, synthetic-marker masking, provenance labels and an allowed-tool-only interface. High-impact actions are proposed but never executed.

## Required preflight

Run:

```bash
PYTHONPATH=src python -m secureagentrag preflight
```

Exit status `2` means the empirical pilot is blocked. The expected initial blockers are pending bilingual reviews and missing live provider configurations. Removing a blocker requires evidence; editing the report or status labels alone is not approval.

After every gate passes, the prespecified pilot can be started with:

```bash
PYTHONPATH=src python scripts/run_empirical_pilot.py
```

This script produces separate immutable JSONL logs for AWS, Azure and the open-weight backend, combined summaries, and a run manifest containing hashes of every dataset and configuration file.
