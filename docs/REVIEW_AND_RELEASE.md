# Localization review and release

SecureAgentRAG does not treat machine translation or an unchecked spreadsheet as research evidence. Each non-English dataset requires a named translator, a different named bilingual reviewer, row-level approval and a maintainer attestation.

## Roles

- **Translator:** completes the four target-language fields for every scenario.
- **Bilingual reviewer:** independently checks semantic equivalence, cultural clarity, preserved attack strength and preserved named entities.
- **Maintainer:** confirms the completed review before importing the dataset.

Only include contributor names with their consent because the workbooks and evidence manifests may be published. Do not place email addresses, phone numbers or signatures in the repository.

## Review procedure

1. Give the reviewer the relevant CSV from `translation_workbooks/`.
2. Complete every `target_*` field without changing scenario identifiers or synthetic markers.
3. Record different translator and reviewer names.
4. Set every review check to `yes` only after inspecting that row.
5. Set `review_status` to `review_approved`.
6. Audit without releasing:

   ```bash
   PYTHONPATH=src python -m secureagentrag review-status --language fr
   ```

7. After human review, import one language and issue hash-linked evidence:

   ```bash
   PYTHONPATH=src python scripts/import_reviewed_translations.py fr \
     --maintainer "MAINTAINER NAME"
   ```

The import creates `data/locales/fr.jsonl`, records SHA-256 hashes in `data/locales/evidence/fr.json`, and updates the language status in the locale manifest. Any later workbook or dataset edit invalidates the evidence and blocks the empirical pilot.

## Research integrity rules

- Never fill translator or reviewer names for someone who did not perform the work.
- Never mark AI-generated translations as independently human reviewed.
- Preserve synthetic attack markers exactly where the source scenario requires them.
- Resolve disagreements before approval and record material decisions in `review_notes`.
- Re-run the audit and import after every approved correction.
