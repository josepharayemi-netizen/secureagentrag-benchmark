from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from .review import sha256_file


LANGUAGE_NAMES = {
    "fr": "French",
    "ar": "Arabic",
    "sw": "Swahili",
    "yo": "Yoruba",
    "ha": "Hausa",
}


@dataclass(frozen=True)
class ReviewPacket:
    language: str
    directory: Path
    workbook: Path
    instructions: Path
    declaration: Path
    manifest: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "language": self.language,
            "directory": str(self.directory),
            "workbook": str(self.workbook),
            "instructions": str(self.instructions),
            "declaration": str(self.declaration),
            "manifest": str(self.manifest),
        }


def build_review_packet(
    project_root: str | Path, output_root: str | Path, language: str
) -> ReviewPacket:
    if language not in LANGUAGE_NAMES:
        raise ValueError(f"unsupported target language: {language}")
    project = Path(project_root)
    source_workbook = (
        project / "translation_workbooks" / f"secureagentrag_{language}.csv"
    )
    if not source_workbook.exists():
        raise FileNotFoundError(f"translation workbook not found: {source_workbook}")

    packet_dir = Path(output_root) / f"secureagentrag-review-{language}"
    if packet_dir.exists() and any(packet_dir.iterdir()):
        raise FileExistsError(
            f"review packet already exists and will not be overwritten: {packet_dir}"
        )
    packet_dir.mkdir(parents=True, exist_ok=True)
    workbook = packet_dir / source_workbook.name
    instructions = packet_dir / "INSTRUCTIONS.md"
    declaration = packet_dir / "REVIEWER_DECLARATION.md"
    manifest = packet_dir / "MANIFEST.json"

    shutil.copyfile(source_workbook, workbook)
    instructions.write_text(
        _instructions(language, LANGUAGE_NAMES[language]), encoding="utf-8"
    )
    declaration.write_text(
        _declaration(language, LANGUAGE_NAMES[language]), encoding="utf-8"
    )
    payload = {
        "schema_version": "0.1.0",
        "project": "SecureAgentRAG",
        "language_code": language,
        "language_name": LANGUAGE_NAMES[language],
        "expected_rows": 36,
        "workbook": workbook.name,
        "workbook_sha256": sha256_file(workbook),
        "instructions": instructions.name,
        "declaration": declaration.name,
        "contains_personal_data_at_generation": False,
    }
    manifest.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return ReviewPacket(
        language=language,
        directory=packet_dir,
        workbook=workbook,
        instructions=instructions,
        declaration=declaration,
        manifest=manifest,
    )


def _instructions(language: str, language_name: str) -> str:
    return f"""# SecureAgentRAG {language_name} review packet

Language code: `{language}`

This packet contains 36 synthetic research scenarios. It contains no intentionally
collected personal data and must not be populated with real personal information.

## Required roles

1. A bilingual translator completes every blank `target_*` field.
2. A different bilingual reviewer independently checks every completed row.
3. The project maintainer validates and imports the returned workbook.

## Row-level review

- Preserve meaning, safety expectations, attack strength and named entities.
- Keep synthetic markers and tool names exact when they appear in the source.
- Record the translator and reviewer names only with their consent.
- Set each of the four review checks to `yes` only after verification.
- Set `review_status` to `review_approved` only when the row is complete.
- Use `review_notes` for material choices or disagreements.

Do not alter scenario identifiers, column names or the CSV filename. Return the
completed CSV and declaration to the project maintainer. The automated import will
reject missing translations, self-review, incomplete checks and changed evidence.
"""


def _declaration(language: str, language_name: str) -> str:
    return f"""# Reviewer declaration — {language_name} (`{language}`)

Complete this document only after the workbook review is finished.

- Translator name:
- Reviewer name:
- Maintainer name:
- Date completed (YYYY-MM-DD):
- Relevant language experience:
- Conflicts of interest, if any:
- Translation tools or AI assistance disclosed, if any:
- Consent to publish contributor names: yes / no

## Attestation

The translator confirms responsibility for the target-language text. The independent
reviewer confirms that all 36 rows were checked for semantic equivalence, cultural
clarity, preserved attack strength and preserved named entities. Both confirm that no
real personal or confidential data were introduced.
"""
