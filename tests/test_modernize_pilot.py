"""Tests for the inventory-to-translation pilot."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.modernize_pilot import run_pilot


class ModernizePilotTests(unittest.TestCase):
    def test_inventory_translation_and_syntax_report_are_connected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "legacy"
            output = base / "pilot-output"
            root.mkdir()
            (root / "MAIN.cbl").write_text("""IDENTIFICATION DIVISION.
PROGRAM-ID. MAIN.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-COUNT PIC 99 VALUE 1.
PROCEDURE DIVISION.
    ADD 1 TO WS-COUNT.
    DISPLAY WS-COUNT.
    STOP RUN.
""", encoding="utf-8")

            report = run_pilot(root, output)

            self.assertEqual(report["inventory_summary"]["cobol_programs"], 1)
            self.assertEqual(report["translation_summary"]["source_files"], 1)
            self.assertEqual(report["translation_summary"]["translated"], 1)
            self.assertEqual(report["translation_summary"]["syntax_errors"], 0)
            self.assertEqual(report["semantic_validation"], "not-performed")
            self.assertTrue((output / "inventory.json").is_file())
            self.assertTrue((output / "inventory.md").is_file())
            self.assertTrue((output / "translation-report.md").is_file())
            self.assertTrue((output / "translated" / "MAIN.py").is_file())
            saved = json.loads((output / "translation-report.json").read_text(encoding="utf-8"))
            self.assertIn(saved["results"][0]["status"], ("translated", "translated-with-diagnostics"))

    def test_rejects_output_inside_source_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "legacy"
            root.mkdir()
            with self.assertRaisesRegex(ValueError, "outside the source root"):
                run_pilot(root, root / "output")


if __name__ == "__main__":
    unittest.main()
