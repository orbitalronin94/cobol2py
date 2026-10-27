"""Tests for the inventory-to-translation pilot."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.modernize_pilot import REPOSITORY_ROOT, _differential_fixtures, classify_diagnostic, run_pilot


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
            self.assertEqual(report["schema_version"], 2)
            self.assertEqual(report["tool_versions"]["translator"], "0.0.4")
            self.assertEqual(report["validation"]["semantics"], "not-evaluated")
            self.assertEqual(report["results"][0]["semantic_status"], "not-evaluated")
            self.assertIn("diagnostic_classifications", report["translation_summary"])
            self.assertTrue((output / "inventory.json").is_file())
            self.assertTrue((output / "inventory.md").is_file())
            self.assertTrue((output / "translation-report.md").is_file())
            self.assertTrue((output / "translated" / "MAIN.py").is_file())
            saved = json.loads((output / "translation-report.json").read_text(encoding="utf-8"))
            self.assertIn(saved["results"][0]["status"], ("translated", "translated-with-diagnostics"))

    def test_classifies_known_limits_separately_from_possible_defects(self):
        known = classify_diagnostic({"code": "ARITHMETIC_SIZE_ERROR_UNSUPPORTED", "severity": "warning"})
        defect = classify_diagnostic({"code": "MALFORMED_CONTROL_FLOW", "severity": "error"})
        unknown = classify_diagnostic({"code": "FUTURE_DIAGNOSTIC", "severity": "warning"})
        self.assertEqual(known["classification"], "known-limitation")
        self.assertTrue(known["review_required"])
        self.assertEqual(defect["classification"], "possible-defect")
        self.assertTrue(defect["review_required"])
        self.assertEqual(unknown["classification"], "review-required")
        self.assertTrue(unknown["review_required"])

    def test_differential_mode_marks_unmatched_sources_not_applicable(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "legacy"
            output = base / "pilot-output"
            root.mkdir()
            (root / "LOCAL.cbl").write_text(
                "IDENTIFICATION DIVISION.\nPROGRAM-ID. LOCAL.\nPROCEDURE DIVISION.\n STOP RUN.\n",
                encoding="utf-8",
            )
            report = run_pilot(root, output, differential=True)
            self.assertEqual(report["semantic_validation"], "not-applicable")
            self.assertEqual(report["differential_validation"]["case_count"], 0)
            self.assertEqual(report["results"][0]["semantic_status"], "not-applicable")

    def test_exact_manifest_source_path_gets_fixture_link(self):
        matches = _differential_fixtures(REPOSITORY_ROOT / "samples" / "realtest.cbl")
        self.assertEqual([item["id"] for item in matches], ["realtest"])
        self.assertEqual(_differential_fixtures(REPOSITORY_ROOT / "elsewhere" / "realtest.cbl"), [])

    def test_rejects_output_inside_source_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "legacy"
            root.mkdir()
            with self.assertRaisesRegex(ValueError, "outside the source root"):
                run_pilot(root, root / "output")


if __name__ == "__main__":
    unittest.main()
