# AWS and Azure account readiness

Cloud preparation can proceed while localization review is underway. Do not deploy
production data or long-lived credentials for this experiment.

## Common controls

- Use a dedicated research account, subscription or isolated project boundary.
- Enable MFA on human administrator accounts before provisioning resources.
- Configure a billing budget and alerts before the first model invocation.
- Use synthetic benchmark documents only.
- Use short-lived identity, least privilege and separate deploy/run roles.
- Pin model/deployment versions, region, API version and current pricing.
- Set log retention and a documented teardown date.
- Never commit access keys, API keys, client secrets or connection strings.

## AWS readiness

- Confirm Amazon Bedrock model access in the selected region.
- Create a dedicated S3 location for synthetic documents.
- Create a Bedrock Knowledge Base with authorization metadata.
- Create a test guardrail and record its immutable version.
- Grant the runner only required retrieval, invocation, guardrail and logging actions.
- Copy `configs/providers/aws.example.json` to the ignored `aws.json` file and complete
  every placeholder.

## Azure readiness

- Confirm Azure OpenAI access and deployment availability in the selected region.
- Create a dedicated resource group and managed identity.
- Create an Azure AI Search index with `content`, `source` and `authorized_roles`
  fields.
- Grant the managed identity only the required OpenAI, Search and monitoring roles.
- Copy `configs/providers/azure.example.json` to the ignored `azure.json` file and
  complete every placeholder.

## Release decision

Run `PYTHONPATH=src python -m secureagentrag preflight`. Do not begin the paid empirical
pilot until the output reports `"ready": true`, every localization has hash-linked
evidence, and the maximum cost for each provider remains inside its approved budget.
