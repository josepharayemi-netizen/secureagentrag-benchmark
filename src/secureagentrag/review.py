from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


TARGET_FIELDS = (
    "target_benign_request",
    "target_untrusted_content",
    "target_expected_safe_behavior",
    "target_expected_utility_behavior",
)
REVIEW_CHECKS = (
    "semantic_equivalence",
    "cultural_clarity",
    "attack_strength_preserved",
    "named_entities_preserved",
)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class WorkbookAudit:
    language: str
    ready: bool
    row_count: int
    workbook_sha256: str
    translators: tuple[str, ...]
    reviewers: tuple[str, ...]
    blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "language": self.language,
            "ready": self.ready,
            "row_count": self.row_count,
            "workbook_sha256": self.workbook_sha256,
            "translators": list(self.translators),
            "reviewers": list(self.reviewers),
            "blockers": list(self.blockers),
        }


def audit_workbook(
    path: str | Path, language: str, expected_rows: int = 36
) -> WorkbookAudit:
    workbook = Path(path)
    blockers: list[str] = []
    if not workbook.exists():
        return WorkbookAudit(language, False, 0, "", (), (), ("workbook missing",))

    with workbook.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != expected_rows:
        blockers.append(f"expected {expected_rows} rows, found {len(rows)}")

    scenario_ids: list[str] = []
    translators: set[str] = set()
    reviewers: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        scenario_id = row.get("scenario_id", "").strip()
        scenario_ids.append(scenario_id)
        if not scenario_id:
            blockers.append(f"row {row_number}: scenario_id is missing")
        missing_targets = [name for name in TARGET_FIELDS if not row.get(name, "").strip()]
        if missing_targets:
            blockers.append(
                f"row {row_number}: missing translations: {', '.join(missing_targets)}"
            )

        translator = row.get("translator_name", "").strip()
        reviewer = row.get("reviewer_name", "").strip()
        if not translator or not reviewer:
            blockers.append(f"row {row_number}: translator and reviewer names are required")
        else:
            translators.add(translator)
            reviewers.add(reviewer)
            if translator.casefold() == reviewer.casefold():
                blockers.append(
                    f"row {row_number}: translator and reviewer must be different people"
                )

        failed_checks = [
            name for name in REVIEW_CHECKS if row.get(name, "").strip().casefold() != "yes"
        ]
        if failed_checks:
            blockers.append(
                f"row {row_number}: incomplete review checks: {', '.join(failed_checks)}"
            )
        if row.get("review_status", "").strip() != "review_approved":
            blockers.append(f"row {row_number}: review_status is not review_approved")

    duplicates = sorted({item for item in scenario_ids if scenario_ids.count(item) > 1})
    if duplicates:
        blockers.append(f"duplicate scenario identifiers: {', '.join(duplicates)}")

    return WorkbookAudit(
        language=language,
        ready=not blockers,
        row_count=len(rows),
        workbook_sha256=sha256_file(workbook),
        translators=tuple(sorted(translators)),
        reviewers=tuple(sorted(reviewers)),
        blockers=tuple(blockers),
    )


def write_review_evidence(
    audit: WorkbookAudit,
    dataset_path: str | Path,
    output_path: str | Path,
    maintainer_name: str,
) -> Path:
    if not audit.ready:
        raise ValueError("cannot issue review evidence for a workbook with blockers")
    if not maintainer_name.strip():
        raise ValueError("maintainer_name is required")
    dataset = Path(dataset_path)
    output = Path(output_path)
    payload = {
        "schema_version": "0.1.0",
        "language": audit.language,
        "review_status": "review_approved",
        "approved_rows": audit.row_count,
        "workbook_sha256": audit.workbook_sha256,
        "dataset_sha256": sha256_file(dataset),
        "translators": list(audit.translators),
        "reviewers": list(audit.reviewers),
        "maintainer_attestation": maintainer_name.strip(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def verify_review_evidence(
    evidence_path: str | Path, workbook_path: str | Path, dataset_path: str | Path
) -> list[str]:
    evidence_file = Path(evidence_path)
    workbook = Path(workbook_path)
    dataset = Path(dataset_path)
    missing = []
    if not workbook.exists():
        missing.append("review workbook missing")
    if not dataset.exists():
        missing.append("localized dataset missing")
    if missing:
        return missing
    if not evidence_file.exists():
        return ["review evidence manifest missing"]
    try:
        evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"review evidence manifest is invalid: {exc}"]
    errors: list[str] = []
    if evidence.get("review_status") != "review_approved":
        errors.append("review evidence is not approved")
    if evidence.get("workbook_sha256") != sha256_file(workbook):
        errors.append("review workbook hash does not match evidence")
    if evidence.get("dataset_sha256") != sha256_file(dataset):
        errors.append("localized dataset hash does not match evidence")
    if not evidence.get("maintainer_attestation"):
        errors.append("maintainer attestation is missing")
    return errors
