# Translation review workbooks

These five CSV files contain the 36 approved English source scenarios and blank fields for French, Arabic, Swahili, Yoruba and Hausa localization.

They are intentionally marked `translation_pending`. A bilingual translator fills the target fields, and a different bilingual reviewer should complete the review columns where practical.

## Approval checklist

The reviewer records `yes` or `no` for:

1. semantic equivalence;
2. cultural clarity;
3. preservation of attack strength;
4. preservation of named entities and synthetic markers.

The final `review_status` may change to `review_approved` only when every required target field is complete, every checklist item is `yes`, and the translator and reviewer names are recorded. Updating the language manifest is a separate, deliberate release step.
