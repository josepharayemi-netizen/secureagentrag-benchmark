import csv
import json
from pathlib import Path
import tempfile
import unittest

from secureagentrag.review import (
    REVIEW_CHECKS,
    TARGET_FIELDS,
    audit_workbook,
    verify_review_evidence,
    write_review_evidence,
)


class ReviewTests(unittest.TestCase):
    def _write_workbook(self, root: Path, reviewer: str = "Reviewer Two") -> Path:
        fields = [
            "scenario_id",
            *TARGET_FIELDS,
            "translator_name",
            "reviewer_name",
            *REVIEW_CHECKS,
            "review_status",
        ]
        path = root / "review.csv"
        row = {
            "scenario_id": "sar-test-01",
            **{field: f"translated {field}" for field in TARGET_FIELDS},
            "translator_name": "Translator One",
            "reviewer_name": reviewer,
            **{field: "yes" for field in REVIEW_CHECKS},
            "review_status": "review_approved",
        }
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerow(row)
        return path

    def test_approved_workbook_produces_verifiable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = self._write_workbook(root)
            dataset = root / "fr.jsonl"
            dataset.write_text('{"synthetic": true}\n', encoding="utf-8")
            audit = audit_workbook(workbook, "fr", expected_rows=1)
            self.assertTrue(audit.ready)
            evidence = write_review_evidence(
                audit, dataset, root / "evidence.json", "Project Maintainer"
            )
            self.assertEqual(verify_review_evidence(evidence, workbook, dataset), [])

    def test_translator_cannot_self_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workbook = self._write_workbook(Path(directory), reviewer="Translator One")
            audit = audit_workbook(workbook, "fr", expected_rows=1)
            self.assertFalse(audit.ready)
            self.assertTrue(any("different people" in item for item in audit.blockers))

    def test_evidence_detects_dataset_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = self._write_workbook(root)
            dataset = root / "fr.jsonl"
            dataset.write_text('{"version": 1}\n', encoding="utf-8")
            audit = audit_workbook(workbook, "fr", expected_rows=1)
            evidence = write_review_evidence(audit, dataset, root / "evidence.json", "Maintainer")
            dataset.write_text('{"version": 2}\n', encoding="utf-8")
            errors = verify_review_evidence(evidence, workbook, dataset)
            self.assertIn("localized dataset hash does not match evidence", errors)


if __name__ == "__main__":
    unittest.main()
