# Reviewer recruitment kit

The multilingual study requires one bilingual translator and a different bilingual
reviewer for each language: French, Arabic, Swahili, Yoruba and Hausa. A multilingual
contributor may support more than one language, but nobody may approve their own
translation.

## Suitable contributors

Recruit adults who can read technical English and the target language fluently.
Experience in translation, linguistics, AI, cybersecurity, higher education or
professional technical writing is helpful. Contributors should be able to explain
ambiguous wording and preserve synthetic attack markers exactly.

Agree in advance on acknowledgement, compensation, deadlines, public naming and any
potential authorship. Completing a workbook does not automatically guarantee paper
authorship; use the target venue's authorship policy and the CRediT taxonomy when
assigning contributions.

## Invitation message

> **Subject: Bilingual research contributor for SecureAgentRAG**
>
> I am conducting an open, reproducible study of security, privacy and responsible
> behaviour in agentic retrieval-augmented generation. I am seeking a bilingual
> contributor for English and **[LANGUAGE]**.
>
> The task covers 36 synthetic scenarios. A translator completes four target-language
> fields per row, and a different reviewer independently checks meaning, cultural
> clarity, preserved attack strength and named entities. No real personal or
> confidential data are used. Estimated effort is approximately 2–4 hours for
> translation and 1–2 hours for independent review, depending on experience.
>
> Contributor acknowledgement, public-name consent, timeline and any compensation will
> be agreed before work begins. The project is available at:
> https://github.com/josepharayemi-netizen/secureagentrag-benchmark
>
> If interested, please state your language experience and whether you prefer the
> translator or reviewer role.

## Maintainer checklist

- Confirm the contributor is fluent enough for the selected role.
- Assign translator and reviewer roles to different people.
- Agree on acknowledgement, compensation and deadline in writing.
- If a contributor declines public naming, assign a stable contributor identifier and
  keep the identity mapping offline.
- Share only the relevant generated review packet.
- Do not request identity documents or unnecessary personal information.
- Inspect the returned declaration and run `secureagentrag review-status`.
- Resolve disagreements before importing the localized dataset.

Generate a packet with:

```bash
PYTHONPATH=src python scripts/make_review_packet.py fr
```

Replace `fr` with `ar`, `sw`, `yo` or `ha` for the other languages. Generated packets
are excluded from version control because completed copies may contain contributor
names.
