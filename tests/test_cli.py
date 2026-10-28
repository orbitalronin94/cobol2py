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
        self.assertIn('str("OK")', result.stdout)
        self.assertIn('print(', result.stdout)

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

    def test_subscript_on_elementary_field_indexes_enclosing_occurs_group(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. SUBPARENT.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-REC.",
            "          05 WS-ENTRY OCCURS 2 TIMES.",
            "             10 WS-GROUP.",
            "                15 WS-FIELD PIC 9(3).",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           MOVE 123 TO WS-FIELD(1).",
            "           DISPLAY WS-FIELD(1).",
            "           STOP RUN.",
        ])
        translated = self.run_cli(source)
        self.assertEqual(translated.returncode, 0, translated.stderr)
        with tempfile.TemporaryDirectory() as temp_dir:
            generated = Path(temp_dir) / "translated.py"
            generated.write_text(translated.stdout, encoding="utf-8")
            executed = subprocess.run(
                [sys.executable, str(generated)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(executed.returncode, 0, executed.stderr)
        self.assertEqual(executed.stdout, "123\n")

    def test_move_into_reference_modification_replaces_field_and_table_element(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. REFMOD.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            '       01 WS-TEXT PIC X(5) VALUE "ABCDE".',
            "       01 WS-TABLE PIC X(5) OCCURS 2 TIMES.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            '           MOVE "XY" TO WS-TEXT(2:2).',
            '           MOVE "12" TO WS-TABLE(1)(2:2).',
            "           DISPLAY WS-TEXT.",
            "           DISPLAY WS-TABLE(1).",
            "           STOP RUN.",
        ])
        translated = self.run_cli(source)
        self.assertEqual(translated.returncode, 0, translated.stderr)
        with tempfile.TemporaryDirectory() as temp_dir:
            generated = Path(temp_dir) / "translated.py"
            generated.write_text(translated.stdout, encoding="utf-8")
            executed = subprocess.run(
                [sys.executable, str(generated)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(executed.returncode, 0, executed.stderr)
        self.assertEqual(executed.stdout, "AXYDE\n 12  \n")

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
        self.assertTrue(
            result.stderr.startswith("["),
            f"expected JSON array on stderr; returncode={result.returncode}, "
            f"stdout={result.stdout!r}, stderr={result.stderr!r}",
        )
        diagnostics = json.loads(result.stderr)
        self.assertTrue(diagnostics)
        self.assertIn("OCCURS_DEPENDING_ON_UNSUPPORTED", {item["code"] for item in diagnostics})
        depending_on = next(
            item for item in diagnostics if item["code"] == "OCCURS_DEPENDING_ON_UNSUPPORTED"
        )
        self.assertEqual(depending_on["line"], 6)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
