"""Regression tests for the MIT-100 source/dependency audit."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools" / "audit_mit100.py"


class Mit100AuditTests(unittest.TestCase):
    def test_static_audit_reports_manifest_and_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "mit100-audit.json"
            result = subprocess.run(
                [sys.executable, str(AUDIT), "--json", str(report_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["manifest_entries"], 100)
            self.assertEqual(report["unique_program_ids"], 100)
            self.assertEqual(report["source_file_count"], 20)
            self.assertGreater(len(report["copybooks"]["referenced"]), 0)
            self.assertEqual(len(report["files"]), 20)
            self.assertTrue(all(item["exists"] for item in report["files"]))


if __name__ == "__main__":
    unittest.main()
