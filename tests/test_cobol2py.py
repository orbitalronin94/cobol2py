"""Regression tests for cobol2py. Run with: python -m unittest discover -s tests -v."""
import unittest

import cobol2py


class PreprocessTests(unittest.TestCase):
    def test_fixed_format_with_blank_sequence_area_skips_indicator_comments(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "      * THIS IS A FIXED-FORMAT COMMENT",
            "       PROGRAM-ID. DEMO.",
        ])

        lines = cobol2py.preprocess(source)

        self.assertEqual(
            lines,
            [(1, "IDENTIFICATION DIVISION."), (3, "PROGRAM-ID. DEMO.")],
        )

    def test_free_format_preserves_source_and_removes_inline_comment(self):
        source = "IDENTIFICATION DIVISION.\nDISPLAY 'OK'. *> comment\n"

        self.assertEqual(
            cobol2py.preprocess(source),
            [(1, "IDENTIFICATION DIVISION."), (2, "DISPLAY 'OK'.")],
        )


class TranslationTests(unittest.TestCase):
    def test_numeric_move_is_not_stringified(self):
        self.assertEqual(
            cobol2py.translate_statement("MOVE 123 TO WS-CODIGO", set()),
            ["ws_codigo = 123"],
        )

    def test_simple_value_clause_initializes_variable(self):
        self.assertEqual(
            cobol2py.CobolVar(level=1, name="WS-STATUS", pic="X", value='"A"').py_default(),
            '"A"',
        )
        self.assertEqual(
            cobol2py.CobolVar(level=1, name="WS-TOTAL", pic="9(3)", value="12").py_default(),
            "12",
        )

    def test_equality_condition_uses_python_operator(self):
        self.assertEqual(
            cobol2py.translate_condition("WS-NUM = 10"),
            "ws_num == 10",
        )

    def test_unsupported_statement_is_explicit(self):
        output = cobol2py.translate_statement('CALL "SUBPGM"', set())
        self.assertEqual(output, ['# COBOL no traducido: CALL "SUBPGM"'])


class EndToEndTests(unittest.TestCase):
    def test_repository_samples_generate_syntactically_valid_python(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        for sample in ("hello.cbl", "realtest.cbl"):
            with self.subTest(sample=sample):
                source = (root / "samples" / sample).read_text(encoding="utf-8")
                generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
                compile(generated, f"<{sample}-output>", "exec")

    def test_fixed_format_program_generates_valid_python(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. DEMO.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-NUM PIC 9(3).",
            "       PROCEDURE DIVISION.",
            "       MAIN-PARA.",
            '           DISPLAY "OK".',
            "           STOP RUN.",
        ])

        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        compile(generated, "<cobol2py-output>", "exec")
        self.assertIn('print("OK")', generated)
        self.assertIn("def main_para():", generated)


if __name__ == "__main__":
    unittest.main()
