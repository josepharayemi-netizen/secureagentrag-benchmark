# SecureAgentRAG Benchmark

**A multilingual research benchmark for prompt injection, privacy leakage and responsible behaviour in agentic retrieval-augmented generation.**

[![CI](https://github.com/josepharayemi-netizen/secureagentrag-benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/josepharayemi-netizen/secureagentrag-benchmark/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Protocol](https://img.shields.io/badge/study-protocol%20stage-blue)](docs/PROTOCOL_SUMMARY.md)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0007--0776--7238-A6CE39)](https://orcid.org/0009-0007-0776-7238)

SecureAgentRAG tests whether security controls protect an agentic RAG system across languages and cloud platforms without destroying useful behaviour or making the system unaffordable. It joins a secure multi-cloud RAG architecture with the multilingual AgentGuardBench evaluation framework.

> **Research status:** this repository is at the protocol and instrumentation stage. The included deterministic mock run validates code paths only. It is not an AWS, Azure or language-model experiment and must not be cited as empirical evidence.

## What is new

SecureAgentRAG contributes a joint evaluation of:

- direct and indirect prompt injection;
- retrieval poisoning;
- privacy leakage;
- unauthorized tool use;
- benign-task completion and over-refusal;
- grounded-answer quality, latency and cost;
- matched AWS and Azure control layers;
- English, French, Arabic, Swahili, Yoruba and Hausa.

## Research design

| Dimension | Prespecified value |
|---|---:|
| English source scenarios | 36 |
| Threat/control classes | 6 |
| Planned languages | 6 |
| Defense configurations | 3 |
| Model backends | 3 |
| Pilot observations | 1,944 |
| Full-study observations | 5,832 |

The three defense levels are not interchangeable: C0 is a minimally protected baseline, C1 adds prompt-focused controls, and C2 adds policy-gated controls across retrieval, model and action layers.

## Safe quick start

Python 3.10 or later is required.

```bash
python scripts/generate_dataset.py
PYTHONPATH=src python scripts/validate_dataset.py
PYTHONPATH=src python -m secureagentrag validate
PYTHONPATH=src python -m secureagentrag pilot
PYTHONPATH=src python -m secureagentrag preflight
python -m unittest discover -s tests -v
```

The pilot command creates 324 deterministic observations: 36 source scenarios × 3 configurations × 3 seeds. These results are smoke-test fixtures, not the prespecified multilingual empirical pilot.

The preflight command is expected to remain blocked until bilingual reviewers approve all five localizations and live, version-pinned AWS, Azure and open-weight provider configurations are supplied outside version control. See the [cloud adapter guide](docs/CLOUD_ADAPTERS.md).

Localization release uses independent translator/reviewer roles plus hash-linked evidence manifests. See the [review and release guide](docs/REVIEW_AND_RELEASE.md). Provider preflight also calculates a worst-case cost and rejects a run that exceeds its declared budget.

## Repository map

```text
data/scenarios.jsonl             approved English source scenarios
data/locales/manifest.json       translation and review status
configs/experiment.json          prespecified experimental dimensions
configs/providers/               credential-free provider templates
src/secureagentrag/              validation, adapters, scoring and reporting
translation_workbooks/           bilingual translation and review worksheets
tests/                            deterministic unit and integrity tests
docs/PROTOCOL_SUMMARY.md          link between software and the third paper
docs/REVIEW_AND_RELEASE.md        independent review and provenance procedure
```

## Evidence gates

An empirical release requires all of the following:

1. Bilingual review of every localized scenario.
2. Version-pinned models, controls, regions and pricing inputs.
3. Immutable scenario, configuration, output and score records.
4. Declared handling of API failures and missing runs.
5. Blinded human review of at least 20% of outputs.
6. Prespecified statistical analysis and a reproducibility package.

## Relationship to the first two publications

SecureAgentRAG explicitly cites and extends:

1. Joseph Arayemi, *Secure and Responsible Retrieval-Augmented Generation for Resource-Constrained Organizations: A Multi-Cloud Reference Architecture and Experimental Evaluation*. [DOI 10.5281/zenodo.23048249](https://doi.org/10.5281/zenodo.23048249)
2. Joseph Arayemi, *AgentGuardBench: A Multilingual Benchmark for Privacy, Security and Responsible Behaviour in AI Agents*. [DOI 10.5281/zenodo.23132194](https://doi.org/10.5281/zenodo.23132194)

The first work supplies the cloud architecture and governance foundation. The second supplies the multilingual agent-safety categories. SecureAgentRAG tests their combined claims under one prespecified empirical protocol.

## Responsible use

Use only synthetic data, dedicated test accounts and inert tools. Never connect the benchmark to production credentials, real personal information or irreversible actions. Read [ETHICS.md](ETHICS.md), [SECURITY.md](SECURITY.md) and [DATASET_CARD.md](DATASET_CARD.md) before adding an adapter.

## Citation

The project is in prerelease and does not yet have its own DOI. Use [CITATION.cff](CITATION.cff) for provisional metadata. A version-specific Zenodo DOI should be minted only after the source dataset, documentation and release tag are complete.

## Author

Joseph Arayemi — GIIT Africa ICT Training Limited
[ORCID 0009-0007-0776-7238](https://orcid.org/0009-0007-0776-7238) · yemi@giitafrica.com
