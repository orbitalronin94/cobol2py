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

    def test_value_all_literal_repeats_to_fill_alphanumeric_pic(self):
        variable = cobol2py.CobolVar(level=1, name="WS-FLAG", pic="X(4)", value='ALL "Y"')
        self.assertEqual(variable.py_default(), "'YYYY'")

    def test_move_all_literal_repeats_to_fill_alphanumeric_pic(self):
        variables = {"WS-FLAG": cobol2py.CobolVar(level=1, name="WS-FLAG", pic="X(4)")}
        self.assertEqual(cobol2py.translate_move_value('ALL "Y"', "WS-FLAG", variables), "'YYYY'")

    def test_value_space_zero_and_low_value_figuratives(self):
        self.assertEqual(cobol2py.translate_literal("ZEROES"), "0")
        self.assertEqual(cobol2py.translate_literal("LOW-VALUES"), repr("\x00"))
        self.assertEqual(cobol2py.translate_literal("HIGH-VALUES"), repr("\xff"))

    def test_value_clause_parses_signed_and_decimal_literals(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. VALUEDECIMAL.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-SIGNED PIC S9(3) VALUE -12.",
            "       01 WS-RATE PIC 9(3)V99 VALUE +12.50.",
            "       PROCEDURE DIVISION.",
            "           STOP RUN.",
        ])
        variables = cobol2py.parse_cobol(source).variables
        self.assertEqual([item.value for item in variables], ["-12", "+12.50"])
        self.assertEqual([item.py_default() for item in variables], ["-12", "+12.50"])

    def test_move_truncates_signed_and_implied_decimal_receiving_fields(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. NUMERICMOVE.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-SIGNED PIC S9(3) VALUE 0.",
            "       01 WS-RATE PIC 9(3)V99 VALUE 0.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           MOVE -1234 TO WS-SIGNED.",
            "           MOVE 1234.567 TO WS-RATE.",
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<numeric-move-output>", "exec"), namespace)
        namespace["main"]()
        self.assertEqual(namespace["ws_signed"], -234, generated)
        self.assertAlmostEqual(namespace["ws_rate"], 234.56, places=2, msg=generated)

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


class GnuCobolTraceTests(unittest.TestCase):
    def test_trace_instrumentation_emits_each_scalar_before_program_exit(self):
        from tools.gnucobol_trace import instrument_source

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. TRACETEST.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            '01 WS-NAME PIC X(5) VALUE "AL".',
            "01 WS-COUNT PIC 9(3) VALUE 0.",
            "01 WS-GROUP.",
            "   05 WS-CHILD PIC X(3).",
            "01 WS-TABLE PIC 9 OCCURS 2 TIMES.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            'DISPLAY "HELLO".',
            "STOP RUN.",
        ])
        instrumented, traced, skipped, unresolved, actual_format = instrument_source(
            source, source_format="free"
        )
        self.assertEqual(actual_format, "free")
        self.assertEqual(traced, ["WS-NAME", "WS-COUNT", "WS-GROUP", "WS-CHILD", "WS-TABLE(1)", "WS-TABLE(2)"])
        self.assertEqual(skipped, [])
        self.assertEqual(unresolved, [])
        self.assertLess(instrumented.index('TRACE_VAR|WS-COUNT|'), instrumented.index("STOP RUN"))
        self.assertIn('DISPLAY "TRACE_VAR|WS-NAME|" WS-NAME.', instrumented)
        self.assertIn('DISPLAY "TRACE_VAR|WS-COUNT|" WS-COUNT.', instrumented)
        self.assertIn('DISPLAY "TRACE_VAR|WS-CHILD|" WS-CHILD.', instrumented)
        self.assertIn('DISPLAY "TRACE_VAR|WS-TABLE(2)|" WS-TABLE(2).', instrumented)


class JavaBackendTests(unittest.TestCase):
    def test_java_backend_emits_valid_shape_for_shared_ast(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. JAVATEST.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            '01 WS-NAME PIC X(5) VALUE "AL".',
            "01 WS-COUNT PIC 9(3) VALUE 0.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            'MOVE "BOB" TO WS-NAME.',
            "ADD 2 TO WS-COUNT.",
            "IF WS-COUNT = 2",
            'DISPLAY "MATCH".',
            "ELSE",
            'DISPLAY "MISS".',
            "END-IF.",
            "EVALUATE WS-COUNT",
            "WHEN 2",
            'DISPLAY "TWO".',
            "WHEN OTHER",
            'DISPLAY "OTHER".',
            "END-EVALUATE.",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_java(cobol2py.parse_cobol(source, source_format="free"))
        self.assertIn("class Cobol2PyProgram", generated)
        self.assertIn("private static int ws_count", generated)
        self.assertIn("if (ws_count == 2)", generated)
        self.assertIn("evalEquals(_cobolEvaluate", generated)
        self.assertIn('System.out.println(String.join("", Arrays.asList', generated)
        self.assertNotIn("EVALUATE no traducido", generated)


class CopybookTests(unittest.TestCase):
    def test_resolves_copybook_from_explicit_search_path(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp:
            root = Path(temp)
            source_dir = root / "src"
            copy_dir = root / "copybooks"
            source_dir.mkdir()
            copy_dir.mkdir()
            (copy_dir / "CUSTOMER.cpy").write_text(
                '01 WS-NAME PIC X(5) VALUE "AL".\n', encoding="utf-8"
            )
            source = "\n".join([
                "IDENTIFICATION DIVISION.",
                "PROGRAM-ID. COPYTEST.",
                "DATA DIVISION.",
                "WORKING-STORAGE SECTION.",
                "COPY CUSTOMER.",
                "PROCEDURE DIVISION.",
                "MAIN.",
                "STOP RUN.",
            ])
            program = cobol2py.parse_cobol(
                source,
                source_format="free",
                copybook_paths=[copy_dir],
                source_path=source_dir / "main.cbl",
            )
            self.assertEqual([v.name for v in program.variables], ["WS-NAME"])
            self.assertEqual(program.unresolved_copybooks, [])

    def test_resolves_nested_copybooks_and_reports_cycles(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "A.cpy").write_text("COPY B.\n", encoding="utf-8")
            (root / "B.cpy").write_text('01 WS-ID PIC 9 VALUE 7.\nCOPY A.\n', encoding="utf-8")
            source = "\n".join([
                "DATA DIVISION.",
                "WORKING-STORAGE SECTION.",
                "COPY A.",
                "PROCEDURE DIVISION.",
                "MAIN.",
                "STOP RUN.",
            ])
            program = cobol2py.parse_cobol(
                source, source_format="free", copybook_paths=[root]
            )
            self.assertEqual([v.name for v in program.variables], ["WS-ID"])
            self.assertTrue(any("COPYBOOK CYCLE" in item for item in program.unresolved_copybooks))
            self.assertIn("COPYBOOK RESOLUTION WARNING", cobol2py.emit_python(program))

    def test_missing_copybook_is_explicit_and_not_silently_dropped(self):
        source = "\n".join([
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "COPY DOES-NOT-EXIST.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free", copybook_paths=[])
        self.assertTrue(any("COPYBOOK NOT FOUND: DOES-NOT-EXIST" in item for item in program.unresolved_copybooks))
        self.assertIn("COPYBOOK RESOLUTION WARNING", cobol2py.emit_python(program))


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

    def test_group_fields_are_nested_and_can_be_read_or_written(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. GROUPTEST.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-CUSTOMER.",
            '   05 WS-NAME PIC X(5) VALUE "AL".',
            "   05 WS-DETAILS.",
            "      10 WS-AGE PIC 9(3) VALUE 7.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            '   MOVE "BOB" TO WS-NAME OF WS-CUSTOMER.',
            "   MOVE 42 TO WS-AGE.",
            '   DISPLAY WS-NAME OF WS-CUSTOMER.',
            "   DISPLAY WS-AGE.",
            '   IF WS-NAME = "BOB"',
            '      DISPLAY "MATCH".',
            "   END-IF.",
            "   STOP RUN.",
        ])
        generated = cobol2py.emit_python(
            cobol2py.parse_cobol(source, source_format="free")
        )
        compile(generated, "<group-output>", "exec")
        self.assertIn("ws_customer: dict = {'ws_name':", generated)
        self.assertNotIn("ws_name: str =", generated)
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<group-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "BOB  \n042\nMATCH\n", generated)
        self.assertEqual(namespace["ws_customer"]["ws_details"]["ws_age"], 42)

    def test_variable_model_tracks_group_parent_names(self):
        source = "\n".join([
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-RECORD.",
            "   05 WS-ADDRESS.",
            "      10 WS-ZIP PIC 9(5).",
            "PROCEDURE DIVISION.",
        ])
        variables = cobol2py.parse_cobol(source, source_format="free").variables
        by_name = {variable.name: variable for variable in variables}
        self.assertIsNone(by_name["WS-RECORD"].parent_name)
        self.assertEqual(by_name["WS-ADDRESS"].parent_name, "WS-RECORD")
        self.assertEqual(by_name["WS-ZIP"].parent_name, "WS-ADDRESS")

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


    def test_evaluate_when_and_when_other_execute_matching_branch(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. EVALUATETEST.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-CODE PIC 9 VALUE 2.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           EVALUATE WS-CODE",
            "               WHEN 1",
            '                   DISPLAY "ONE".',
            "               WHEN 2",
            '                   DISPLAY "TWO".',
            "               WHEN OTHER",
            '                   DISPLAY "OTHER".',
            "           END-EVALUATE.",
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<evaluate-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "TWO\n", generated)

    def test_evaluate_true_supports_nested_if_and_else(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. EVALUATENESTED.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-NUM PIC 9 VALUE 2.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           EVALUATE TRUE",
            "               WHEN WS-NUM > 1",
            "                   IF WS-NUM < 4",
            '                       DISPLAY "IN".',
            "                   ELSE",
            '                       DISPLAY "OUT".',
            "                   END-IF",
            "               WHEN OTHER",
            '                   DISPLAY "OTHER".',
            "           END-EVALUATE.",
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<evaluate-nested-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "IN\n", generated)

    def test_three_level_nested_if_preserves_each_else_scope(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. DEEPNEST.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-A PIC 9 VALUE 1.",
            "       01 WS-B PIC 9 VALUE 1.",
            "       01 WS-C PIC 9 VALUE 1.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           IF WS-A = 1",
            "               IF WS-B = 1",
            "                   IF WS-C = 1",
            '                       DISPLAY "DEEP".',
            "                   ELSE",
            '                       DISPLAY "C".',
            "                   END-IF",
            "               ELSE",
            '                   DISPLAY "B".',
            "               END-IF",
            "           ELSE",
            '               DISPLAY "A".',
            "           END-IF.",
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<deep-if-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "DEEP\n", generated)

    def test_unclosed_if_generates_valid_python_and_explicit_comment(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. BROKEN.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           IF 1 = 1",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        compile(generated, "<malformed-if-output>", "exec")
        self.assertIn("Unclosed IF opened at source line", generated)

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
