# Dataset card

## Current release

Version 0.1 contains 36 approved English source scenarios. They are evenly distributed across direct prompt injection, indirect prompt injection, retrieval poisoning, privacy leakage, unauthorized tool use and benign controls.

All names, markers, records, credentials and actions are synthetic. Tools are identifiers only; the source dataset cannot execute an external action.

## Planned localization

French, Arabic, Swahili, Yoruba and Hausa are declared in `data/locales/manifest.json` but remain `translation_pending`. A localized dataset must not be described as validated until a bilingual reviewer approves semantic equivalence, cultural clarity, attack strength, expected safe behaviour and expected utility behaviour.

Machine translation may assist drafting but cannot satisfy the human-review gate.

## Intended use

- Defensive research on agentic RAG controls.
- Reproducible cloud-security evaluation.
- Responsible-AI education and authorized red-team exercises.

## Prohibited use

- Testing systems without authorization.
- Connecting scenarios to production data or irreversible tools.
- Treating mock-runner output as empirical model evidence.
- Publishing unreviewed translations as validated benchmark results.
