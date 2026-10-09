import csv
import json
from pathlib import Path
import tempfile
import unittest

from secureagentrag.packets import build_review_packet
from secureagentrag.review import sha256_file


class ReviewPacketTests(unittest.TestCase):
    def test_packet_contains_hash_linked_workbook_and_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbooks = root / "translation_workbooks"
            workbooks.mkdir()
            source = workbooks / "secureagentrag_fr.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(["scenario_id", "target_benign_request"])
                writer.writerow(["sar-test-01", ""])

            packet = build_review_packet(root, root / "packets", "fr")
            self.assertTrue(packet.workbook.exists())
            self.assertTrue(packet.instructions.exists())
            self.assertTrue(packet.declaration.exists())
            manifest = json.loads(packet.manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest["language_code"], "fr")
            self.assertEqual(manifest["workbook_sha256"], sha256_file(packet.workbook))
            self.assertFalse(manifest["contains_personal_data_at_generation"])

    def test_existing_packet_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbooks = root / "translation_workbooks"
            workbooks.mkdir()
            (workbooks / "secureagentrag_fr.csv").write_text(
                "scenario_id\nsar-test-01\n", encoding="utf-8"
            )
            output = root / "packets"
            build_review_packet(root, output, "fr")
            with self.assertRaisesRegex(FileExistsError, "will not be overwritten"):
                build_review_packet(root, output, "fr")

    def test_unsupported_language_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "unsupported target language"):
                build_review_packet(directory, directory, "de")


if __name__ == "__main__":
    unittest.main()
