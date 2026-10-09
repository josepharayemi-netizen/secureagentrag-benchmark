# SecureAgentRAG protocol summary

SecureAgentRAG extends two prior works by Joseph Arayemi:

1. *Secure and Responsible Retrieval-Augmented Generation for Resource-Constrained Organizations: A Multi-Cloud Reference Architecture and Experimental Evaluation* — [DOI 10.5281/zenodo.23048249](https://doi.org/10.5281/zenodo.23048249)
2. *AgentGuardBench: A Multilingual Benchmark for Privacy, Security and Responsible Behaviour in AI Agents* — [DOI 10.5281/zenodo.23132194](https://doi.org/10.5281/zenodo.23132194)

The new study evaluates prompt injection, retrieval poisoning, privacy leakage, unauthorized tool use and over-refusal in agentic RAG systems. It compares a baseline, a prompt-focused defense and a layered policy-gated defense using matched AWS and Azure deployments.

## Prespecified design

- 36 English source scenarios: six scenarios for each of six threat or control classes.
- Six planned languages: English, French, Arabic, Swahili, Yoruba and Hausa.
- Three defense configurations: C0, C1 and C2.
- Three model backends and three independent seeds.
- Pilot: 1,944 observations, using one seed.
- Full experiment: 5,832 observations, using three seeds.

## Evidence gate

No empirical result may be written into the final paper until the localized dataset, provider manifest, immutable run logs, human-review sample, statistical analysis and reproducibility package pass their declared completion rules.

The deterministic mock runner in this repository exists only to test orchestration, scoring and CI. Its outputs are not AWS, Azure or language-model findings.
