"""CLI contract tests: strict mode and machine-readable diagnostics."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSLATOR = ROOT / "cobol2py.py"


class CliTests(unittest.TestCase):
    def run_cli(self, source: str, *args: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "input.cbl"
            source_path.write_text(source, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(TRANSLATOR), str(source_path), *args],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_simple_supported_program_translates_successfully(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. SMOKE.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            '           DISPLAY "OK".',
            "           STOP RUN.",
        ])
        result = self.run_cli(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('print("OK")', result.stdout)

    def test_strict_mode_fails_when_diagnostics_are_present(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. STRICTCHECK.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-COUNT PIC 9 VALUE 2.",
            "       01 WS-TABLE PIC X OCCURS 5 TIMES DEPENDING ON WS-COUNT.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           STOP RUN.",
        ])
        result = self.run_cli(source, "--strict")
        self.assertEqual(result.returncode, 2)
        self.assertIn("OCCURS_DEPENDING_ON_UNSUPPORTED", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_diagnostics_json_is_valid_json_on_stderr(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. JSONCHECK.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-COUNT PIC 9 VALUE 2.",
            "       01 WS-TABLE PIC X OCCURS 5 TIMES DEPENDING ON WS-COUNT.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           STOP RUN.",
        ])
        result = self.run_cli(source, "--diagnostics-json", "--strict")
        self.assertEqual(result.returncode, 2)
        diagnostics = json.loads(result.stderr)
        self.assertTrue(diagnostics)
        self.assertIn("OCCURS_DEPENDING_ON_UNSUPPORTED", {item["code"] for item in diagnostics})
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
