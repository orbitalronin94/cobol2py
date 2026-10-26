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

    def test_explicit_free_format_preserves_seven_space_indentation(self):
        source = "       DISPLAY 'OK'."
        self.assertEqual(
            cobol2py.preprocess(source, source_format="free"),
            [(1, "       DISPLAY 'OK'.")],
        )

    def test_explicit_fixed_format_uses_source_columns(self):
        source = "       DISPLAY 'OK'."
        self.assertEqual(
            cobol2py.preprocess(source, source_format="fixed"),
            [(1, "DISPLAY 'OK'.")],
        )


class TranslationTests(unittest.TestCase):
    def test_simple_value_clause_initializes_variable(self):
        self.assertEqual(
            cobol2py.CobolVar(level=1, name="WS-STATUS", pic="X", value='"A"').py_default(),
            'str("A")[:1].ljust(1)',
        )
        self.assertEqual(
            cobol2py.CobolVar(level=1, name="WS-TOTAL", pic="9(3)", value="12").py_default(),
            "12",
        )

    def test_alphanumeric_pic_defaults_and_value_are_fixed_width(self):
        self.assertEqual(
            cobol2py.CobolVar(level=1, name="WS-BLANK", pic="X(3)").py_default(),
            "'   '",
        )
        self.assertEqual(
            cobol2py.CobolVar(level=1, name="WS-INITIAL", pic="X(5)", value='"A"').py_default(),
            'str("A")[:5].ljust(5)',
        )

    def test_move_pads_and_truncates_alphanumeric_receiving_pic(self):
        variables = {
            "WS-CODE": cobol2py.CobolVar(level=1, name="WS-CODE", pic="X(5)")
        }
        self.assertEqual(
            cobol2py.translate_move_value('"A"', "WS-CODE", variables),
            'str("A")[:5].ljust(5)',
        )
        self.assertEqual(
            cobol2py.translate_move_value('"ABCDEFG"', "WS-CODE", variables),
            'str("ABCDEFG")[:5].ljust(5)',
        )

    def test_move_keeps_rightmost_digits_for_unsigned_integer_pic(self):
        variables = {
            "WS-NUM": cobol2py.CobolVar(level=1, name="WS-NUM", pic="9(3)")
        }
        self.assertEqual(
            cobol2py.translate_move_value("1234", "WS-NUM", variables),
            "int(1234) % (10 ** 3)",
        )

    def test_hyphenated_identifier_and_subtraction_are_tokenized(self):
        self.assertEqual(cobol2py.translate_expr("WS-NUM - 1"), "ws_num - 1")
        self.assertEqual(cobol2py.translate_expr("WS-NUM + WS-TOTAL"), "ws_num + ws_total")

    def test_equality_condition_uses_python_operator(self):
        self.assertEqual(
            cobol2py.translate_condition("WS-NUM = 10"),
            "ws_num == 10",
        )


    def test_cobol_table_subscripts_are_converted_to_zero_based_indexes(self):
        self.assertEqual(cobol2py.normalize_name("WS-ITEM(1)"), "ws_item[0]")
        self.assertEqual(
            cobol2py.normalize_name("WS-ITEM(WS-INDEX)"),
            "ws_item[ws_index - 1]",
        )

    def test_unsupported_statement_is_explicit(self):
        output = cobol2py.translate_statement('CALL "SUBPGM"', set())
        self.assertEqual(output, ['# COBOL no traducido: CALL "SUBPGM"'])


class EndToEndTests(unittest.TestCase):
    def test_perform_times_body_is_nested_in_loop(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. LOOPTEST.",
            "       PROCEDURE DIVISION.",
            "       MAIN-PARA.",
            "           PERFORM WORK-PARA 3 TIMES.",
            "           STOP RUN.",
            "       WORK-PARA.",
            '           DISPLAY "OK".',
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        compile(generated, "<perform-times-output>", "exec")
        self.assertRegex(generated, r"for _ in range\(3\):\n\s+work_para\(\)")

    def test_repository_samples_generate_syntactically_valid_python(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        for sample in ("hello.cbl", "realtest.cbl"):
            with self.subTest(sample=sample):
                source = (root / "samples" / sample).read_text(encoding="utf-8")
                generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
                compile(generated, f"<{sample}-output>", "exec")


    def test_generated_program_matches_cobol_output_for_add_and_if(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. BEHAVIOR.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-COUNT PIC 9(3) VALUE 0.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           ADD 1 TO WS-COUNT.",
            "           ADD 2 TO WS-COUNT.",
            "           IF WS-COUNT = 3 THEN",
            '               DISPLAY "COUNT=" WS-COUNT.',
            "           END-IF.",
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<behavior-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        # COBOL DISPLAY concatenates its operands without Python's print separator.
        self.assertEqual(output.getvalue(), "COUNT=003\n")


    def test_generated_program_executes_perform_times_against_shared_storage(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. LOOPBEHAVIOR.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-TOTAL PIC 9(3) VALUE 0.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           PERFORM INCREMENT 3 TIMES.",
            '           DISPLAY "TOTAL=" WS-TOTAL.',
            "           STOP RUN.",
            "       INCREMENT.",
            "           ADD 1 TO WS-TOTAL.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<perform-behavior-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "TOTAL=003\n")


    def test_realtest_sample_matches_expected_console_output(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        source = (root / "samples" / "realtest.cbl").read_text(encoding="utf-8")
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<realtest-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["inicio"]()
        self.assertEqual(
            output.getvalue(),
            "INICIO DEL PROGRAMA\n"
            "PROCESANDO...\n"
            "ACUMULADO: 000010\n"
            "ACUMULADO: 000020\n"
            "ACUMULADO: 000030\n"
            "CODIGO ALTO\n"
            "TOTAL FINAL: 000030\n"
            "STATUS ACTIVO\n",
            generated,
        )

    def test_move_numeric_pic_keeps_rightmost_digits(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. MOVENUMERIC.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-NUM PIC 9(3).",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           MOVE 1234 TO WS-NUM.",
            '           DISPLAY WS-NUM.',
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<move-numeric-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "234\n", generated)

    def test_move_alphanumeric_pic_matches_fixed_width_display(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. MOVEPADDING.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-CODE PIC X(5).",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            '           MOVE "ABCDEFG" TO WS-CODE.',
            '           DISPLAY WS-CODE.',
            "           MOVE " + '"A"' + " TO WS-CODE.",
            '           DISPLAY WS-CODE.',
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<move-padding-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "ABCDE\nA    \n", generated)

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
        self.assertIn('print("".join([str("OK")]))', generated)
        self.assertIn("def main_para():", generated)


    def test_standard_if_else_without_then_matches_cobol_control_flow(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. IFTEST.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-NUM PIC 9 VALUE 2.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           IF WS-NUM = 2",
            '               DISPLAY "MATCH".',
            "           ELSE",
            '               DISPLAY "OTHER".',
            "           END-IF.",
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<if-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "MATCH\n", generated)

    def test_inline_perform_times_executes_body_exactly_n_times(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. INLINELOOP.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            '           PERFORM 2 TIMES DISPLAY "TICK" END-PERFORM.',
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<inline-perform-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "TICK\nTICK\n", generated)

    def test_table_subscript_in_condition_is_one_based_in_cobol(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. TABLEIF.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-TABLE.",
            "          05 WS-ITEM PIC X(4) OCCURS 2 TIMES.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            '           MOVE "RED" TO WS-ITEM(1).',
            '           MOVE "BLU" TO WS-ITEM(2).',
            '           IF WS-ITEM(2) = "BLU"',
            '               DISPLAY "TABLE-OK".',
            "           ELSE",
            '               DISPLAY "TABLE-NO".',
            "           END-IF.",
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<table-if-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "TABLE-OK\n", generated)


if __name__ == "__main__":
    unittest.main()
