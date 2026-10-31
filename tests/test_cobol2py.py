"""Regression tests for cobol2py. Run with: python -m unittest discover -s tests -v."""
import ast
import os
import tempfile
import unittest
from pathlib import Path

import cobol2py


class PreprocessTests(unittest.TestCase):
    def test_decimal_point_is_comma_normalizes_numeric_literals_only(self):
        source = "\n".join([
            "SPECIAL-NAMES. DECIMAL-POINT IS COMMA.",
            "IF AMOUNT > 806,80 DISPLAY \"literal 8,80\".",
            "COMPUTE TAX = AMOUNT * 0,21.",
        ])

        self.assertEqual(
            cobol2py.preprocess(source, source_format="free"),
            [
                (1, "SPECIAL-NAMES. DECIMAL-POINT IS COMMA."),
                (2, 'IF AMOUNT > 806.80 DISPLAY "literal 8,80".'),
                (3, "COMPUTE TAX = AMOUNT * 0.21."),
            ],
        )

    def test_decimal_comma_is_not_enabled_by_comment(self):
        source = "\n".join([
            "*> DECIMAL-POINT IS COMMA.",
            "IF AMOUNT > 806,80 DISPLAY AMOUNT.",
        ])

        self.assertEqual(
            cobol2py.preprocess(source, source_format="free"),
            [
                (2, "IF AMOUNT > 806,80 DISPLAY AMOUNT."),
            ],
        )

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

    def test_inline_comment_marker_inside_quoted_literal_is_preserved(self):
        source = 'IDENTIFICATION DIVISION.\nDISPLAY "A *> B". *> actual comment\n'
        self.assertEqual(
            cobol2py.preprocess(source),
            [(1, "IDENTIFICATION DIVISION."), (2, 'DISPLAY "A *> B".')],
        )

    def test_display_preserves_doubled_quote_literal_end_to_end(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. QUOTEDDISPLAY.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            'DISPLAY "DON""T".',
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<quoted-display>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), 'DON"T\n')

    def test_split_cobol_items_keeps_doubled_quote_literals_atomic(self):
        self.assertEqual(
            cobol2py.split_cobol_items('"DON""T" \'IT\'\'S OK\''),
            ['"DON""T"', "'IT''S OK'"],
        )

    def test_split_concat_statements_keeps_quoted_text_atomic(self):
        source = 'DISPLAY "MOVE END-IF *> inside" MOVE WS-A TO WS-B'
        self.assertEqual(
            cobol2py.split_concat_statements(source),
            ['DISPLAY "MOVE END-IF *> inside"', "MOVE WS-A TO WS-B"],
        )

    def test_inline_comment_scanner_handles_doubled_quotes(self):
        self.assertEqual(
            cobol2py.strip_inline_comment('DISPLAY "A ""*>"" B". *> comment'),
            'DISPLAY "A ""*>"" B".',
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

    def test_when_clause_splits_inline_action_from_condition(self):
        units = cobol2py.split_paragraph_into_units([
            (1, "EVALUATE 1"),
            (2, 'WHEN 1 DISPLAY "ONE"'),
            (3, "END-EVALUATE"),
        ])
        self.assertEqual(
            units,
            [(1, "EVALUATE 1"), (2, "WHEN 1"), (2, 'DISPLAY "ONE"'), (3, "END-EVALUATE")],
        )

    def test_fixed_format_hyphen_continuations_join_numeric_literal(self):
        source = "\n".join([
            "000100 IDENTIFICATION DIVISION.",
            "000200 PROGRAM-ID. CONTNUM.",
            "000300 DATA DIVISION.",
            "000400 WORKING-STORAGE SECTION.",
            "000500 01 WS-N PIC 9(5).",
            "000600 PROCEDURE DIVISION.",
            "000700 MAIN.",
            "000800     MOVE 4",
            "000900-        5",
            "001000-        6",
            "001100-        7",
            "001200-        8 TO WS-N.",
            "001300     DISPLAY WS-N.",
            "001400     STOP RUN.",
        ])
        lines = cobol2py.preprocess(source, source_format="fixed")
        self.assertIn((8, "    MOVE 45678 TO WS-N."), lines)
        generated = cobol2py.emit_python(
            cobol2py.parse_cobol(source, source_format="fixed")
        )
        self.assertIn("45678", generated)
        compile(generated, "<continued-numeric>", "exec")

    def test_file_section_record_descriptions_are_parsed(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. FILERECORD.",
            "DATA DIVISION.",
            "FILE SECTION.",
            "FD INPUT-FILE.",
            "01 INPUT-RECORD.",
            "05 INPUT-CODE PIC X(4).",
            "05 INPUT-AMOUNT PIC 9(5).",
            "WORKING-STORAGE SECTION.",
            "01 WS-COUNT PIC 9(2) VALUE 0.",
            "PROCEDURE DIVISION.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        variables = {item.name: item for item in program.variables}

        self.assertIn("INPUT-RECORD", variables)
        self.assertIn("INPUT-CODE", variables)
        self.assertIn("INPUT-AMOUNT", variables)
        self.assertIn("WS-COUNT", variables)
        self.assertEqual(variables["INPUT-CODE"].parent_name, "INPUT-RECORD")
        self.assertEqual(variables["INPUT-AMOUNT"].parent_name, "INPUT-RECORD")


    def test_select_and_fd_file_metadata_are_preserved(self):
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. FILE-METADATA.
ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
    SELECT INPUT-FILE ASSIGN TO "../database.dat"
        ORGANIZATION IS LINE SEQUENTIAL
        FILE STATUS IS WS-FILE-STATUS.
DATA DIVISION.
FILE SECTION.
FD INPUT-FILE.
01 INPUT-RECORD PIC X(100).
WORKING-STORAGE SECTION.
01 WS-FILE-STATUS PIC XX.
PROCEDURE DIVISION.
STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        self.assertEqual(
            program.file_specs["INPUT-FILE"],
            {
                "assign": "../database.dat",
                "organization": "LINE SEQUENTIAL",
                "status": "WS-FILE-STATUS",
                "record": "INPUT-RECORD",
            },
        )


class CobolFileOpenRuntimeTests(unittest.TestCase):
    def test_open_missing_input_sets_declared_file_status(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. OPEN-MISSING-STATUS.
ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
    SELECT INPUT-FILE ASSIGN TO "missing-input.dat"
        ORGANIZATION IS LINE SEQUENTIAL
        FILE STATUS IS WS-STATUS.
DATA DIVISION.
FILE SECTION.
FD INPUT-FILE.
01 INPUT-RECORD PIC X(10).
WORKING-STORAGE SECTION.
01 WS-STATUS PIC XX.
PROCEDURE DIVISION.
MAIN.
    OPEN INPUT INPUT-FILE.
    DISPLAY WS-STATUS.
    GOBACK.
"""
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        namespace = {"__name__": "generated_test"}
        compile(generated, "<open-missing-status>", "exec")
        exec(generated, namespace)
        output = StringIO()
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                with redirect_stdout(output):
                    namespace["main"]()
            finally:
                os.chdir(previous)
        self.assertEqual(output.getvalue(), "35\n", generated)

    def test_open_missing_input_without_file_status_exits_nonzero(self):
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. OPEN-MISSING-ERROR.
ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
    SELECT INPUT-FILE ASSIGN TO "missing-input.dat".
DATA DIVISION.
FILE SECTION.
FD INPUT-FILE.
01 INPUT-RECORD PIC X(10).
PROCEDURE DIVISION.
MAIN.
    OPEN INPUT INPUT-FILE.
    GOBACK.
"""
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        namespace = {"__name__": "generated_test"}
        compile(generated, "<open-missing-error>", "exec")
        exec(generated, namespace)
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                with self.assertRaises(SystemExit) as raised:
                    namespace["main"]()
            finally:
                os.chdir(previous)
        self.assertEqual(raised.exception.code, 1)


class CobolSequentialReadTests(unittest.TestCase):
    def test_read_at_end_and_not_at_end_execute_the_correct_branch(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. READ-BRANCHES.
ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
    SELECT INPUT-FILE ASSIGN TO "records.dat"
        ORGANIZATION IS LINE SEQUENTIAL
        FILE STATUS IS WS-STATUS.
DATA DIVISION.
FILE SECTION.
FD INPUT-FILE.
01 INPUT-RECORD PIC X(4).
WORKING-STORAGE SECTION.
01 WS-STATUS PIC XX.
01 WS-EOF PIC X.
PROCEDURE DIVISION.
MAIN.
    OPEN INPUT INPUT-FILE.
    READ INPUT-FILE
        AT END MOVE "Y" TO WS-EOF
        NOT AT END DISPLAY INPUT-RECORD
    END-READ.
    CLOSE INPUT-FILE.
    GOBACK.
"""
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        compile(generated, "<read-at-end>", "exec")
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        output = StringIO()
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "records.dat").write_text("AB\n", encoding="latin-1")
            try:
                os.chdir(directory)
                with redirect_stdout(output):
                    namespace["main"]()
            finally:
                os.chdir(previous)
        self.assertEqual(output.getvalue(), "AB  \n", generated)
        self.assertEqual(namespace["ws_eof"], " ")

class CobolSequentialWriteTests(unittest.TestCase):
    def test_open_output_write_and_close_emit_line_sequential_record(self):
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. WRITE-RECORD.
ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
    SELECT OUTPUT-FILE ASSIGN TO "output.dat"
        ORGANIZATION IS LINE SEQUENTIAL.
DATA DIVISION.
FILE SECTION.
FD OUTPUT-FILE.
01 OUTPUT-RECORD PIC X(4).
WORKING-STORAGE SECTION.
01 WS-TEXT PIC X(4) VALUE "AB".
PROCEDURE DIVISION.
MAIN.
    OPEN OUTPUT OUTPUT-FILE.
    MOVE WS-TEXT TO OUTPUT-RECORD.
    WRITE OUTPUT-RECORD.
    CLOSE OUTPUT-FILE.
    GOBACK.
"""
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        compile(generated, "<write-record>", "exec")
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                namespace["main"]()
                contents = Path("output.dat").read_text(encoding="latin-1")
            finally:
                os.chdir(previous)
        self.assertEqual(contents, "AB\n", generated)


class TranslationTests(unittest.TestCase):
    def test_sign_conditions_handle_positive_negative_and_not(self):
        variable = cobol2py.CobolVar(level=77, name="WS-N", pic="S9(4)")
        variables = {"WS-N": variable}
        not_negative = cobol2py.translate_condition("WS-N IS NOT NEGATIVE", variables)
        positive = cobol2py.translate_condition("WS-N IS POSITIVE", variables)
        negative = cobol2py.translate_condition("WS-N IS NEGATIVE", variables)
        zero = cobol2py.translate_condition("WS-N IS ZERO", variables)
        self.assertTrue(eval(not_negative, {"ws_n": 0}))
        self.assertTrue(eval(not_negative, {"ws_n": 3}))
        self.assertFalse(eval(not_negative, {"ws_n": -1}))
        self.assertTrue(eval(positive, {"ws_n": 3}))
        self.assertFalse(eval(positive, {"ws_n": 0}))
        self.assertTrue(eval(negative, {"ws_n": -1}))
        self.assertTrue(eval(zero, {"ws_n": 0}))

    def test_is_prefix_in_hyphenated_data_name_is_not_relation_word(self):
        variable = cobol2py.CobolVar(level=77, name="IS-LOW", pic="9")
        translated = cobol2py.translate_condition(
            "IS-LOW = 1",
            variables={"IS-LOW": variable},
        )
        self.assertTrue(eval(translated, {"is_low": 1}), translated)
        self.assertFalse(eval(translated, {"is_low": 0}), translated)

    def test_qualified_level_88_condition_consumes_parent_qualifier(self):
        variable = cobol2py.CobolVar(level=77, name="WS-D33", pic="X(4)")
        translated = cobol2py.translate_condition(
            "C OF WS-D33",
            variables={"WS-D33": variable},
            condition_names={"C": ("WS-D33", [('" "', None)])},
        )
        self.assertNotIn(" OF ", translated.upper())
        self.assertTrue(eval(translated, {"ws_d33": " "}))

    def test_unqualified_level_88_condition_still_expands(self):
        variable = cobol2py.CobolVar(level=77, name="WS-D33", pic="X(4)")
        translated = cobol2py.translate_condition(
            "C",
            variables={"WS-D33": variable},
            condition_names={"C": ("WS-D33", [('" "', None)])},
        )
        self.assertTrue(eval(translated, {"ws_d33": " "}))

    def test_simple_value_clause_initializes_variable(self):
        self.assertEqual(
            cobol2py.CobolVar(level=1, name="WS-STATUS", pic="X", value='"A"').py_default(),
            'str("A")[:1].ljust(1)',
        )
        self.assertEqual(
            cobol2py.CobolVar(level=1, name="WS-TOTAL", pic="9(3)", value="12").py_default(),
            "12",
        )
        self.assertEqual(
            cobol2py.CobolVar(level=1, name="WS-STEP", pic="9(2)", value="01").py_default(),
            "1",
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

    def test_all_literal_decodes_doubled_quotes(self):
        variable = cobol2py.CobolVar(level=1, name="WS-TEXT", pic="X(5)", value='ALL "DON""T"')
        self.assertEqual(variable.py_default(), "'DON\"T'")
        variables = {"WS-TEXT": cobol2py.CobolVar(level=1, name="WS-TEXT", pic="X(5)")}
        self.assertEqual(
            cobol2py.translate_move_value('ALL "DON""T"', "WS-TEXT", variables),
            "'DON\"T'",
        )

    def test_move_all_literal_repeats_to_fill_alphanumeric_pic(self):
        variables = {"WS-FLAG": cobol2py.CobolVar(level=1, name="WS-FLAG", pic="X(4)")}
        self.assertEqual(cobol2py.translate_move_value('ALL "Y"', "WS-FLAG", variables), "'YYYY'")

    def test_doubled_quotes_in_cobol_literals_are_decoded(self):
        self.assertEqual(cobol2py.translate_literal('"DON""T"'), '"DON\\\"T"')
        self.assertEqual(cobol2py.translate_literal("'IT''S OK'"), "\"IT'S OK\"")
        self.assertEqual(
            cobol2py.translate_java_literal('"DON""T"', {}),
            '"DON\\\"T"',
        )
        self.assertEqual(
            cobol2py.translate_java_literal("'IT''S OK'", {}),
            '"IT\'S OK"',
        )

        self.assertEqual(
            cobol2py.translate_expr('"DON""T"'),
            cobol2py.translate_literal('"DON""T"'),
        )
        self.assertEqual(
            cobol2py.translate_java_expr('"DON""T"', {}),
            cobol2py.translate_java_literal('"DON""T"', {}),
        )

    def test_string_comparison_handles_doubled_quote_literals(self):
        variables = {
            "WS-NAME": cobol2py.CobolVar(level=1, name="WS-NAME", pic="X(5)")
        }
        self.assertEqual(
            cobol2py.translate_condition('WS-NAME = "DON""T"', variables),
            'ws_name.ljust(5) == \'DON"T\'',
        )
        self.assertEqual(
            cobol2py.translate_java_condition('WS-NAME = "DON""T"', variables),
            'Objects.equals(ws_name, "DON\\\"T")',
        )
        self.assertEqual(
            cobol2py.translate_condition('WS-NAME = "NOT"', variables),
            "ws_name.ljust(5) == 'NOT  '",
        )
        self.assertEqual(
            cobol2py.translate_java_condition('WS-NAME = "AND"', variables),
            'Objects.equals(ws_name, "AND  ")',
        )
        self.assertEqual(
            cobol2py.translate_java_condition('WS-NAME NOT EQUAL TO "AND"', variables),
            '!(Objects.equals(ws_name, "AND  "))',
        )

    def test_space_figurative_constant_emits_one_space(self):
        self.assertEqual(cobol2py.translate_literal("SPACE"), '" "')
        self.assertEqual(cobol2py.translate_literal("SPACES"), '" "')
        self.assertEqual(cobol2py.translate_java_literal("SPACE", {}), '" "')
        self.assertEqual(cobol2py.translate_java_literal("SPACES", {}), '" "')

    def test_zero_padded_numeric_literals_emit_valid_python(self):
        self.assertEqual(cobol2py.translate_literal("0007"), "7")
        self.assertEqual(cobol2py.translate_literal("+0007"), "+7")
        self.assertEqual(cobol2py.translate_literal("-0007"), "-7")
        self.assertEqual(cobol2py.translate_literal("000.50"), "0.50")
        self.assertEqual(cobol2py.translate_condition("WS-NUM = 0007"), "ws_num == 7")
        self.assertEqual(cobol2py.translate_expr("WS-NUM + 000.50"), "ws_num + 0.50")
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. LEADINGZERO.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-NUM PIC 9(4).",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "MOVE 0007 TO WS-NUM.",
            "IF WS-NUM = 0007",
            'DISPLAY "OK"',
            "END-IF.",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        compile(generated, "<leading-zero-literal>", "exec")

    def test_value_space_zero_and_low_value_figuratives(self):
        self.assertEqual(cobol2py.translate_literal("ZEROES"), "0")
        self.assertEqual(cobol2py.translate_literal("LOW-VALUES"), repr("\x00"))
        self.assertEqual(cobol2py.translate_literal("HIGH-VALUES"), repr("\xff"))

    def test_value_clause_parses_doubled_quote_literal(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. QUOTEVALUE.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            '01 WS-TEXT PIC X(6) VALUE "DON""T".',
            "PROCEDURE DIVISION.",
            "STOP RUN.",
        ])
        variable = cobol2py.parse_cobol(source, source_format="free").variables[0]
        self.assertEqual(variable.value, '"DON""T"')
        self.assertEqual(eval(variable.py_default()), 'DON"T ')

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

    def test_accept_converts_numeric_input_and_fits_alphanumeric_input(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from unittest.mock import patch

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. ACCEPTTEST.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-NUM PIC 9(3).",
            "01 WS-TEXT PIC X(3).",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "ACCEPT WS-NUM.",
            "ADD 1 TO WS-NUM.",
            "DISPLAY WS-NUM.",
            "ACCEPT WS-TEXT.",
            "DISPLAY WS-TEXT.",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<accept-output>", "exec"), namespace)
        output = StringIO()
        with patch("builtins.input", side_effect=["12", "ABCD"]), redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "013\nABC\n", generated)

    def test_java_accept_applies_numeric_and_alphanumeric_receiving_types(self):
        variables = {
            "WS-NUM": cobol2py.CobolVar(level=1, name="WS-NUM", pic="9(3)"),
            "WS-TEXT": cobol2py.CobolVar(level=1, name="WS-TEXT", pic="X(3)"),
        }
        self.assertIn(
            "Integer.parseInt(SCANNER.nextLine())",
            "\n".join(cobol2py.translate_java_statement("ACCEPT WS-NUM", set(), variables)),
        )
        self.assertIn(
            "fit(SCANNER.nextLine(), 3)",
            "\n".join(cobol2py.translate_java_statement("ACCEPT WS-TEXT", set(), variables)),
        )

    def test_display_of_implied_decimal_pic_omits_decimal_point(self):
        variables = {
            "WS-RATE": cobol2py.CobolVar(level=1, name="WS-RATE", pic="9(3)V99")
        }
        self.assertEqual(
            cobol2py.translate_display_item("WS-RATE", variables),
            "format(float(ws_rate), '06.2f')",
        )

    def test_display_of_explicit_decimal_pic_preserves_decimal_point(self):
        variables = {
            "WS-RATE": cobol2py.CobolVar(level=1, name="WS-RATE", pic="999.99")
        }
        self.assertEqual(
            cobol2py.translate_display_item("WS-RATE", variables),
            "format(float(ws_rate), '06.2f')",
        )

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

    def test_reserved_words_are_normalized_for_both_backends(self):
        self.assertEqual(cobol2py.normalize_name("CLASS"), "cobol_class")
        self.assertEqual(cobol2py.normalize_name("PRINT"), "cobol_print")
        self.assertEqual(cobol2py.normalize_name("INPUT"), "cobol_input")
        self.assertEqual(cobol2py.normalize_name("WS-CLASS(1)"), "ws_class[0]")
        self.assertEqual(cobol2py.normalize_name("WS-ITEM(INT)"), "ws_item[cobol_int - 1]")

    def test_hyphenated_identifier_and_subtraction_are_tokenized(self):
        self.assertEqual(cobol2py.translate_expr("WS-NUM - 1"), "ws_num - 1")
        self.assertEqual(cobol2py.translate_expr("WS-NUM + WS-TOTAL"), "ws_num + ws_total")

    def test_generated_integer_coercion_is_restored_outside_list_subscripts(self):
        translated = cobol2py.translate_expr("int(CTR) - 1")
        self.assertIn("int(", translated)
        self.assertNotIn("cobol_int(", translated)
        # A data item named INT is still a bare COBOL identifier.
        self.assertEqual(cobol2py.normalize_name("WS-ITEM(INT)"), "ws_item[cobol_int - 1]")

    def test_java_compound_string_comparisons_use_value_equality(self):
        variables = {
            "WS-A": cobol2py.CobolVar(level=1, name="WS-A", pic="X(3)"),
            "WS-B": cobol2py.CobolVar(level=1, name="WS-B", pic="X(3)"),
        }
        self.assertEqual(
            cobol2py.translate_java_condition('WS-A = "ONE" AND WS-B = "TWO"', variables),
            'Objects.equals(ws_a, "ONE") && Objects.equals(ws_b, "TWO")',
        )

    def test_java_string_comparison_pads_left_field_when_literal_is_longer(self):
        variables = {"WS-A": cobol2py.CobolVar(level=1, name="WS-A", pic="X(3)")}
        self.assertEqual(
            cobol2py.translate_java_condition('WS-A = "LONGER"', variables),
            'Objects.equals(fit(String.valueOf(ws_a), 6), "LONGER")',
        )

    def test_java_not_can_wrap_a_predicate_with_a_string_literal(self):
        variables = {
            "WS-NAME": cobol2py.CobolVar(level=1, name="WS-NAME", pic="X(3)")
        }
        self.assertEqual(
            cobol2py.translate_java_condition('NOT WS-NAME = "A"', variables),
            '!(Objects.equals(ws_name, "A  "))',
        )

    def test_java_not_applies_to_the_full_condition(self):
        self.assertEqual(
            cobol2py.translate_java_condition("NOT WS-B = 2", {}),
            "!(ws_b == 2)",
        )

    def test_not_equal_to_does_not_become_invalid_operator(self):
        self.assertEqual(
            cobol2py.translate_condition("WS-A NOT EQUAL TO 2"),
            "ws_a != 2",
        )
        self.assertEqual(
            cobol2py.translate_java_condition("WS-A NOT EQUAL TO 2", {}),
            "ws_a != 2",
        )

    def test_logical_operators_remain_python_operators(self):
        self.assertEqual(
            cobol2py.translate_condition("WS-A = 1 AND NOT WS-B = 2"),
            "ws_a == 1 and not ws_b == 2",
        )
        self.assertEqual(cobol2py.translate_condition("TRUE"), "True")

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


class DynamicControlFlowTests(unittest.TestCase):
    def test_alter_redirects_goto_and_dispatcher_unwinds_current_paragraph(self):
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. ALTERTEST.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-COUNT PIC 9 VALUE 0.
PROCEDURE DIVISION.
MAIN-LOGIC.
    ALTER P-X TO PROCEED TO P-Y.
    GO TO P-X.
    DISPLAY "BAD".
P-X.
    GO TO P-Z.
P-Y.
    DISPLAY "Y".
    STOP RUN.
P-Z.
    DISPLAY "Z".
    STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        compile(generated, "<generated-cobol>", "exec")
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with redirect_stdout(output):
            namespace["_cobol_dispatch"]("MAIN-LOGIC")
        self.assertEqual(output.getvalue(), "Y\n")

    def test_go_to_depending_on_uses_one_based_selector(self):
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. DEPENDINGTEST.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-STEP PIC 9 VALUE 2.
PROCEDURE DIVISION.
MAIN-LOGIC.
    GO TO P-A P-B DEPENDING ON WS-STEP.
    DISPLAY "FALLTHROUGH".
P-A.
    DISPLAY "A".
    STOP RUN.
P-B.
    DISPLAY "B".
    STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        compile(generated, "<generated-cobol>", "exec")
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with redirect_stdout(output):
            namespace["_cobol_dispatch"]("MAIN-LOGIC")
        self.assertEqual(output.getvalue(), "B\n")

    def test_go_to_depending_out_of_range_does_not_transfer(self):
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. DEPENDINGRANGE.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-STEP PIC 9 VALUE 9.
PROCEDURE DIVISION.
MAIN-LOGIC.
    GO TO P-A P-B DEPENDING ON WS-STEP.
    DISPLAY "FALLTHROUGH".
P-A.
    DISPLAY "A".
    STOP RUN.
P-B.
    DISPLAY "B".
    STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        compile(generated, "<generated-cobol>", "exec")
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with redirect_stdout(output):
            namespace["_cobol_dispatch"]("MAIN-LOGIC")
        self.assertEqual(output.getvalue(), "FALLTHROUGH\nA\n")



    def test_full_laberinto_control_flow_redefines_end_to_end(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from pathlib import Path

        source_path = Path(__file__).resolve().parents[1] / "samples" / "laberinto_cobol_original.cbl"
        source = source_path.read_text(encoding="utf-8")
        program = cobol2py.parse_cobol(source, source_path=source_path)
        generated = cobol2py.emit_python(program)
        compile(generated, "<laberinto-cobol>", "exec")
        namespace = {"__name__": "generated_test"}
        output = StringIO()
        with redirect_stdout(output):
            exec(generated, namespace)
            namespace["_cobol_dispatch"]("MAIN-LOGIC")
        self.assertEqual(
            output.getvalue(),
            "INICIO DEL LABERINTO COBOL\n"
            "INICIO DEL LABERINTO COBOL\n"
            "RESULTADO FINAL ACUMULADOR: 000222240\n",
            generated,
        )
        self.assertEqual(namespace["_cobol_storage"]["WS-RAW-INPUT"], "9999911111")
        self.assertEqual(namespace["_cobol_get"]("WS-A"), 99999)
        self.assertEqual(namespace["_cobol_get"]("WS-B"), 11111)
        self.assertEqual(namespace["ws_control_vars"]["ws_accumulator"], 222240)
        self.assertEqual(namespace["_cobol_alter_targets"]["PUNTO-X"], "PUNTO-Y")

class RedefinesStorageTests(unittest.TestCase):
    def test_redefines_group_fields_share_the_base_buffer(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. REDEFINESDEMO.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-RAW-INPUT PIC X(10).
01 WS-VIEW REDEFINES WS-RAW-INPUT.
   05 WS-A PIC 9(5).
   05 WS-B PIC 9(5).
01 WS-TOTAL PIC 9(6) VALUE 0.
PROCEDURE DIVISION.
MAIN.
    MOVE "9999911111" TO WS-RAW-INPUT.
    ADD WS-A WS-B TO WS-TOTAL.
    DISPLAY WS-A.
    DISPLAY WS-B.
    DISPLAY WS-TOTAL.
    STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        compile(generated, "<redefines-storage>", "exec")
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "99999\n11111\n111110\n", generated)
        diagnostics = cobol2py.collect_diagnostics(program)
        self.assertNotIn("UNSUPPORTED_STORAGE_OVERLAY", {item["code"] for item in diagnostics})
        self.assertEqual(namespace["_cobol_storage"]["WS-RAW-INPUT"], "9999911111")

    def test_reference_modification_move_updates_occurs_redefines_view(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. REDEFINESREFMOD.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-RAW PIC X(6).
01 WS-VIEW REDEFINES WS-RAW.
   05 WS-TEXT PIC X(3) OCCURS 2 TIMES.
PROCEDURE DIVISION.
MAIN.
    MOVE "ABCDEF" TO WS-RAW.
    MOVE "xy" TO WS-TEXT(2)(2:2).
    DISPLAY WS-RAW.
    DISPLAY WS-TEXT(2).
    STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        compile(generated, "<redefines-reference-modification>", "exec")
        self.assertIn("_cobol_set('WS-TEXT'", generated)
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "ABCDxy\nDxy\n", generated)
        self.assertEqual(namespace["_cobol_storage"]["WS-RAW"], "ABCDxy")


    def test_combined_alter_computed_goto_and_redefines_storage(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from pathlib import Path

        source_path = Path(__file__).resolve().parents[1] / "samples" / "control_flow_redefines.cbl"
        source = source_path.read_text(encoding="utf-8")
        program = cobol2py.parse_cobol(source, source_format="free", source_path=source_path)
        generated = cobol2py.emit_python(program)
        compile(generated, "<combined-control-overlay>", "exec")
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)

        output = StringIO()
        with redirect_stdout(output):
            namespace["_cobol_dispatch"]("MAIN-LOGIC")

        self.assertEqual(output.getvalue(), "000146\n", generated)
        self.assertEqual(namespace["_cobol_storage"]["WS-RAW"], "1234")
        self.assertEqual(namespace["_cobol_alter_targets"]["P-X"], "P-Y")
        diagnostic_codes = {item["code"] for item in cobol2py.collect_diagnostics(program)}
        self.assertNotIn("UNSUPPORTED_STORAGE_OVERLAY", diagnostic_codes)
        self.assertNotIn("UNSUPPORTED_STATEMENT", diagnostic_codes)

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


class StrictCliTests(unittest.TestCase):
    def test_strict_mode_returns_two_for_unsupported_statement(self):
        import tempfile
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO
        from pathlib import Path
        from unittest.mock import patch

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. STRICTTEST.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            'CALL "UNKNOWN-SUBPROGRAM".',
            "STOP RUN.",
        ])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "strict.cbl"
            path.write_text(source, encoding="utf-8")
            stdout, stderr = StringIO(), StringIO()
            with patch("sys.argv", ["cobol2py", str(path), "--strict"]):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    status = cobol2py.main()
        self.assertEqual(status, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("UNSUPPORTED_STATEMENT", stderr.getvalue())

    def test_diagnostics_json_emits_machine_readable_list(self):
        import json
        import tempfile
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO
        from pathlib import Path
        from unittest.mock import patch

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. JSONTEST.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            'CALL "UNKNOWN-SUBPROGRAM".',
            "STOP RUN.",
        ])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "diagnostics.cbl"
            path.write_text(source, encoding="utf-8")
            stdout, stderr = StringIO(), StringIO()
            with patch("sys.argv", ["cobol2py", str(path), "--diagnostics-json"]):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    status = cobol2py.main()
        self.assertEqual(status, 0)
        diagnostics = json.loads(stderr.getvalue())
        self.assertTrue(any(item["code"] == "UNSUPPORTED_STATEMENT" for item in diagnostics))
        self.assertIn("def main", stdout.getvalue())


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
        self.assertIn("System.exit(0);", generated)


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

    def test_copy_replacing_applies_pseudo_text_before_parsing(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "FIELD.cpy").write_text(
                "01 :FIELD-NAME: PIC :FIELD-PIC: VALUE \"AB\".\n",
                encoding="utf-8",
            )
            source = "\n".join([
                "IDENTIFICATION DIVISION.",
                "PROGRAM-ID. REPLACETEST.",
                "DATA DIVISION.",
                "WORKING-STORAGE SECTION.",
                "COPY FIELD REPLACING "
                "==:FIELD-NAME:== BY ==WS-CODE== "
                "==:FIELD-PIC:== BY ==X(4)==.",
                "PROCEDURE DIVISION.",
                "MAIN.",
                "STOP RUN.",
            ])
            program = cobol2py.parse_cobol(
                source, source_format="free", copybook_paths=[root]
            )
            self.assertEqual([v.name for v in program.variables], ["WS-CODE"])
            self.assertEqual(program.variables[0].pic, "X(4)")
            self.assertEqual(program.unresolved_copybooks, [])

    def test_copy_replacing_unsupported_clause_is_reported(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "FIELD.cpy").write_text(
                "01 WS-CODE PIC X(4).\n", encoding="utf-8"
            )
            source = "\n".join([
                "DATA DIVISION.",
                "WORKING-STORAGE SECTION.",
                "COPY FIELD REPLACING OLD BY NEW.",
                "PROCEDURE DIVISION.",
                "MAIN.",
                "STOP RUN.",
            ])
            program = cobol2py.parse_cobol(
                source, source_format="free", copybook_paths=[root]
            )
            self.assertTrue(any(
                "COPYBOOK UNSUPPORTED CLAUSE" in warning
                for warning in program.unresolved_copybooks
            ))
            self.assertIn("COPYBOOK RESOLUTION WARNING", cobol2py.emit_python(program))

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
    def test_goback_is_not_mistaken_for_a_paragraph_label(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. GOBACKTEST.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            'DISPLAY "BEFORE".',
            "GOBACK.",
            'DISPLAY "AFTER".',
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        self.assertNotIn("GOBACK", program.paragraphs)
        generated = cobol2py.emit_python(program)
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<goback-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "BEFORE\n", generated)

    def test_stop_run_in_called_paragraph_stops_entry_paragraph(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. STOPTEST.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            'DISPLAY "BEFORE".',
            "PERFORM HALT-PARA.",
            'DISPLAY "AFTER".',
            "HALT-PARA.",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(
            cobol2py.parse_cobol(source, source_format="free")
        )
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<stop-run-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "BEFORE\n", generated)

    def test_perform_times_body_is_nested_in_loop(self):
        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. LOOPTEST.",
            "       PROCEDURE DIVISION.",
            "       MAIN-PARA.",
            "           PERFORM WORK-PARA 03 TIMES.",
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

    def test_arithmetic_results_fit_receiving_numeric_pic(self):
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. ARITHSIZE.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-COUNT PIC 99 VALUE 99.
PROCEDURE DIVISION.
    ADD 1 TO WS-COUNT.
    DISPLAY WS-COUNT.
    COMPUTE WS-COUNT = WS-COUNT + 99.
    DISPLAY WS-COUNT.
    MULTIPLY 2 BY WS-COUNT.
    DISPLAY WS-COUNT.
    SUBTRACT 1 FROM WS-COUNT.
    DISPLAY WS-COUNT.
    DIVIDE 2 INTO WS-COUNT.
    DISPLAY WS-COUNT.
    STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        namespace = {"__name__": "not_main"}
        exec(generated, namespace)
        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "00\n99\n98\n97\n48\n")

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


    def test_evaluate_resolves_unqualified_group_child(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. EVALUATEGROUP.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-CUSTOMER.",
            '05 WS-NAME PIC X(3) VALUE "BOB".',
            "PROCEDURE DIVISION.",
            "MAIN.",
            "EVALUATE WS-NAME",
            'WHEN "BOB"',
            'DISPLAY "MATCH".',
            "WHEN OTHER",
            'DISPLAY "MISS".',
            "END-EVALUATE.",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<evaluate-group-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "MATCH\n", generated)

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
            '           PERFORM 02 TIMES DISPLAY "TICK" END-PERFORM.',
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


class DiagnosticTests(unittest.TestCase):
    def test_collect_diagnostics_warns_on_literal_left_string_comparison(self):
        program = cobol2py.Program(
            variables=[cobol2py.CobolVar(level=1, name="WS-NAME", pic="X(3)")],
            paragraphs={
                "MAIN": [
                    cobol2py.Node(kind="if", text='IF "A" = WS-NAME', line=7)
                ]
            },
            paragraph_order=["MAIN"],
        )
        codes = {item["code"] for item in cobol2py.collect_diagnostics(program)}
        self.assertIn("ALPHANUMERIC_LITERAL_LEFT_COMPARISON_UNSUPPORTED", codes)

    def test_collect_diagnostics_warns_on_alphanumeric_field_comparison(self):
        program = cobol2py.Program(
            variables=[
                cobol2py.CobolVar(level=1, name="WS-A", pic="X(3)"),
                cobol2py.CobolVar(level=1, name="WS-B", pic="X(5)"),
            ],
            paragraphs={
                "MAIN": [
                    cobol2py.Node(kind="if", text="IF WS-A = WS-B", line=7)
                ]
            },
            paragraph_order=["MAIN"],
        )
        diagnostics = cobol2py.collect_diagnostics(program)
        self.assertIn(
            "ALPHANUMERIC_FIELD_COMPARISON_UNSUPPORTED",
            {item["code"] for item in diagnostics},
        )

    def test_collect_diagnostics_warns_on_alphanumeric_order_comparison(self):
        program = cobol2py.Program(
            variables=[cobol2py.CobolVar(level=1, name="WS-NAME", pic="X(5)")],
            paragraphs={
                "MAIN": [
                    cobol2py.Node(kind="if", text='IF WS-NAME < "M"', line=8)
                ]
            },
            paragraph_order=["MAIN"],
        )
        diagnostics = cobol2py.collect_diagnostics(program)
        self.assertIn(
            "ALPHANUMERIC_ORDER_COMPARISON_UNSUPPORTED",
            {item["code"] for item in diagnostics},
        )

    def test_collect_diagnostics_warns_on_normalization_collisions(self):
        program = cobol2py.Program(
            variables=[
                cobol2py.CobolVar(level=1, name="PRINT", pic="X"),
                cobol2py.CobolVar(level=1, name="COBOL-PRINT", pic="X"),
            ],
            raw_lines=[
                (5, "01 PRINT PIC X."),
                (6, "01 COBOL-PRINT PIC X."),
            ],
        )
        diagnostics = cobol2py.collect_diagnostics(program)
        item = next(
            item for item in diagnostics
            if item["code"] == "PYTHON_IDENTIFIER_COLLISION"
        )
        self.assertEqual(item["line"], 5)

    def test_collect_diagnostics_warns_on_python_identifier_collisions(self):
        program = cobol2py.Program(
            variables=[cobol2py.CobolVar(level=1, name="MAIN", pic="9")],
            paragraphs={
                "__MAIN__": [cobol2py.Node(kind="stmt", text="CONTINUE", line=2)],
                "MAIN": [cobol2py.Node(kind="stmt", text="CONTINUE", line=4)],
            },
            paragraph_order=["__MAIN__", "MAIN"],
            raw_lines=[(4, "MAIN.")],
        )
        diagnostics = cobol2py.collect_diagnostics(program)
        self.assertIn("PYTHON_IDENTIFIER_COLLISION", {item["code"] for item in diagnostics})

    def test_collect_diagnostics_warns_on_evaluate_alphanumeric_width_mismatch(self):
        program = cobol2py.Program(
            variables=[cobol2py.CobolVar(level=1, name="WS-NAME", pic="X(5)")],
            paragraphs={
                "MAIN": [
                    cobol2py.Node(
                        kind="evaluate",
                        text="EVALUATE WS-NAME",
                        line=3,
                        body=[cobol2py.Node(kind="when", text='"BOB"', line=4)],
                    )
                ]
            },
            paragraph_order=["MAIN"],
        )
        diagnostics = cobol2py.collect_diagnostics(program)
        self.assertIn(
            "EVALUATE_ALPHANUMERIC_PADDING_UNSUPPORTED",
            {item["code"] for item in diagnostics},
        )

    def test_diagnostics_ignore_operator_words_inside_literals(self):
        program = cobol2py.Program(
            variables=[
                cobol2py.CobolVar(level=1, name="WS-NAME", pic="X(20)"),
                cobol2py.CobolVar(level=1, name="WS-A", pic="X"),
                cobol2py.CobolVar(level=1, name="WS-B", pic="X"),
            ],
            paragraphs={
                "MAIN": [
                    cobol2py.Node(kind="if", text='IF WS-NAME = "WS-A = WS-B"', line=3),
                    cobol2py.Node(
                        kind="evaluate",
                        text='EVALUATE WS-NAME',
                        line=5,
                        body=[cobol2py.Node(kind="when", text='"ALSO"', line=6)],
                    ),
                ]
            },
            paragraph_order=["MAIN"],
        )
        codes = {item["code"] for item in cobol2py.collect_diagnostics(program)}
        self.assertNotIn("ALPHANUMERIC_FIELD_COMPARISON_UNSUPPORTED", codes)
        self.assertNotIn("UNSUPPORTED_EVALUATE_ALSO", codes)

    def test_collect_diagnostics_warns_on_evaluate_also(self):
        program = cobol2py.Program(
            paragraphs={
                "MAIN": [
                    cobol2py.Node(
                        kind="evaluate",
                        text="EVALUATE WS-A ALSO WS-B",
                        line=3,
                        body=[cobol2py.Node(kind="when", text="1 ALSO 2", line=4)],
                    )
                ]
            },
            paragraph_order=["MAIN"],
        )
        diagnostics = cobol2py.collect_diagnostics(program)
        self.assertIn("UNSUPPORTED_EVALUATE_ALSO", {item["code"] for item in diagnostics})

    def test_collect_diagnostics_warns_on_occurs_group(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. GROUPTABLE.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-ROWS OCCURS 2 TIMES.",
            "05 WS-CODE PIC X(3).",
            "PROCEDURE DIVISION.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        diagnostics = cobol2py.collect_diagnostics(program)
        item = next(item for item in diagnostics if item["code"] == "OCCURS_GROUP_UNSUPPORTED")
        self.assertEqual(item["line"], 5)

    def test_collect_diagnostics_warns_on_unsupported_data_declarations(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. DATAWARN.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-COUNT PIC 9 VALUE 2.",
            "01 WS-TABLE PIC X OCCURS 5 TIMES DEPENDING ON WS-COUNT.",
            "01 WS-ORIGINAL PIC X(4).",
            "66 WS-ALIAS RENAMES WS-ORIGINAL.",
            "88 WS-VALID VALUE 'Y'.",
            "PROCEDURE DIVISION.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        diagnostics = cobol2py.collect_diagnostics(program)
        by_code = {item["code"]: item for item in diagnostics}
        self.assertIn("OCCURS_DEPENDING_ON_UNSUPPORTED", by_code)
        self.assertIn("UNSUPPORTED_RENAMES", by_code)
        self.assertIn("UNSUPPORTED_CONDITION_NAME_88", by_code)
        self.assertIn("dynamic active length is not implemented", by_code["OCCURS_DEPENDING_ON_UNSUPPORTED"]["message"])
        self.assertEqual(by_code["OCCURS_DEPENDING_ON_UNSUPPORTED"]["line"], 6)

    def test_collect_diagnostics_reports_unsupported_and_malformed_constructs(self):
        program = cobol2py.Program(
            variables=[
                cobol2py.CobolVar(level=1, name="WS-DEC", pic="9(3)V99"),
            ],
            paragraphs={
                "MAIN": [
                    cobol2py.Node(kind="stmt", text="FOO BAR", line=4),
                    cobol2py.Node(kind="stmt", text="ADD 1 TO WS-DEC", line=7),
                    cobol2py.Node(kind="malformed", text="END-IF without matching open block", line=9),
                ]
            },
            paragraph_order=["MAIN"],
            raw_lines=[
                (5, "01 WS-ALT REDEFINES WS-A PIC X(3)."),
                (6, "01 WS-DEC PIC 9(3)V99."),
            ],
            unresolved_copybooks=["COPYBOOK NOT FOUND: MISSING"],
        )

        diagnostics = cobol2py.collect_diagnostics(program)
        codes = {item["code"] for item in diagnostics}
        self.assertEqual(
            codes,
            {
                "UNSUPPORTED_STATEMENT", "MALFORMED_CONTROL_FLOW", "COPYBOOK_RESOLUTION",
                "UNSUPPORTED_STORAGE_OVERLAY", "PARTIAL_NUMERIC_PIC_SEMANTICS",
                "ARITHMETIC_SIZE_ERROR_UNSUPPORTED",
            },
        )
        malformed = next(item for item in diagnostics if item["code"] == "MALFORMED_CONTROL_FLOW")
        self.assertEqual(malformed["line"], 9)



class ThreeDimensionalOccursRedefinesTests(unittest.TestCase):
    def test_three_dimensional_table_reference_and_redefines_share_storage(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. TABLE3DREDEFINES.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 3-DIMENSION-TBL.
   02 GRP-ENTRY OCCURS 2 TIMES INDEXED BY IDX-1.
      03 ENTRY-1 PIC X(5).
      03 GRP2-ENTRY OCCURS 2 TIMES INDEXED BY IDX-2.
         04 ENTRY-2 PIC X(11).
         04 3-ENTRY OCCURS 2 TIMES INDEXED BY IDX-3.
            05 ENTRY-3 PIC X(15).
01 3-DEM-TBL REDEFINES 3-DIMENSION-TBL.
   02 GRP-ENTRY-1 OCCURS 2 TIMES INDEXED BY IDX-1-1.
      03 ENTRY-1-1 PIC X(5).
      03 GRP2-ENTRY-1 OCCURS 2 TIMES INDEXED BY IDX-2-1.
         04 ENTRY-2-1 PIC X(11).
         04 GRP3-ENTRY-1 OCCURS 2 TIMES INDEXED BY IDX-3-1.
            05 ENTRY-3-1 PIC X(15).
01 ELEM-NAME PIC X(15) VALUE "ELEM (01,02,02)".
PROCEDURE DIVISION.
MAIN.
    SET IDX-1 TO 2.
    SET IDX-2 TO 1.
    SET IDX-3 TO 2.
    SET IDX-1-1 TO 2.
    SET IDX-2-1 TO 1.
    SET IDX-3-1 TO 2.
    MOVE ELEM-NAME TO ENTRY-3(IDX-1, IDX-2, IDX-3).
    DISPLAY ENTRY-3(IDX-1, IDX-2, IDX-3).
    DISPLAY ENTRY-3-1(IDX-1-1, IDX-2-1, IDX-3-1).
    STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        compile(generated, "<three-dimensional-redefines>", "exec")
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(
            output.getvalue(),
            "ELEM (01,02,02)\nELEM (01,02,02)\n",
            generated,
        )


class DataReferenceResolutionTests(unittest.TestCase):
    def test_three_level_qualified_reference_resolves_nearest_parent(self):
        variables = {
            "RECORD": cobol2py.CobolVar(level=1, name="RECORD", is_group=True),
            "GROUP": cobol2py.CobolVar(level=5, name="GROUP", is_group=True, parent_name="RECORD"),
            "FIELD": cobol2py.CobolVar(level=10, name="FIELD", pic="X(3)", parent_name="GROUP"),
        }

        translated = cobol2py.normalize_data_reference(
            "FIELD OF GROUP OF RECORD", variables
        )

        self.assertEqual(translated, "record['group']['field']")

    def test_outer_qualifier_disambiguates_duplicate_group_name(self):
        # The legacy name-keyed map can retain only one GROUP declaration.
        # A full COBOL qualification must still preserve the explicitly named
        # outer record rather than silently following that map's parent.
        variables = {
            "RECORD-A": cobol2py.CobolVar(level=1, name="RECORD-A", is_group=True),
            "RECORD-B": cobol2py.CobolVar(level=1, name="RECORD-B", is_group=True),
            "GROUP": cobol2py.CobolVar(
                level=5, name="GROUP", is_group=True, parent_name="RECORD-A"
            ),
            "FIELD": cobol2py.CobolVar(
                level=10, name="FIELD", pic="X", parent_name="GROUP"
            ),
        }

        translated = cobol2py.normalize_data_reference(
            "FIELD OF GROUP OF RECORD-B", variables
        )

        self.assertEqual(translated, "record_b['group']['field']")
        compile(translated, "<qualified-duplicate-group>", "eval")

    def test_cyclic_group_metadata_does_not_recurse_forever(self):
        variables = {
            "GROUP-A": cobol2py.CobolVar(level=1, name="GROUP-A", is_group=True, parent_name="GROUP-B"),
            "GROUP-B": cobol2py.CobolVar(level=1, name="GROUP-B", is_group=True, parent_name="GROUP-A"),
        }

        translated = cobol2py.normalize_data_reference("GROUP-A", variables)

        self.assertIsInstance(translated, str)
        self.assertIn("group", translated)

class ImpliedDecimalDisplayRegressionTests(unittest.TestCase):
    def test_unsigned_implied_decimal_displays_decimal_point_like_gnucobol(self):
        variable = cobol2py.CobolVar(
            level=1, name="WS-RATE", pic="9(3)V99"
        )
        expression = cobol2py.translate_display_item(
            "WS-RATE", {"WS-RATE": variable}
        )
        self.assertEqual(eval(expression, {"ws_rate": 234.56}), "234.56")
        self.assertIn(".", eval(expression, {"ws_rate": 234.56}))


class InlinePerformUntilRegressionTests(unittest.TestCase):
    def _run_program(self, perform_header):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. PERFORMUNTIL.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-COUNT PIC 9 VALUE 0.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            perform_header,
            "ADD 1 TO WS-COUNT",
            "END-PERFORM.",
            "DISPLAY WS-COUNT.",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(
            cobol2py.parse_cobol(source, source_format="free")
        )
        compile(generated, "<perform-until>", "exec")
        namespace = {"__name__": "not_main"}
        exec(generated, namespace)
        try:
            namespace["main"]()
        except namespace["_CobolStopRun"]:
            pass
        return namespace["ws_count"], generated

    def test_perform_until_checks_condition_before_body(self):
        count, generated = self._run_program("PERFORM UNTIL WS-COUNT >= 3")
        self.assertEqual(count, 3)
        self.assertIn("while not (", generated)

    def test_perform_test_after_executes_body_before_check(self):
        count, generated = self._run_program(
            "PERFORM WITH TEST AFTER UNTIL WS-COUNT >= 3"
        )
        self.assertEqual(count, 3)
        self.assertIn("while True:", generated)
        self.assertIn("break", generated)


class InlinePerformVaryingRegressionTests(unittest.TestCase):
    def test_perform_varying_initializes_checks_and_increments_index(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. PERFORMVARYING.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-IDX PIC 9 VALUE 0.",
            "01 WS-COUNT PIC 9 VALUE 0.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > 3",
            "ADD 1 TO WS-COUNT",
            "END-PERFORM.",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(
            cobol2py.parse_cobol(source, source_format="free")
        )
        compile(generated, "<perform-varying>", "exec")
        namespace = {"__name__": "not_main"}
        exec(generated, namespace)
        try:
            namespace["main"]()
        except namespace["_CobolStopRun"]:
            pass
        self.assertEqual(namespace["ws_count"], 3)
        self.assertEqual(namespace["ws_idx"], 4)


if __name__ == "__main__":
    unittest.main()


class MultiTableDiabolicoTests(unittest.TestCase):
    def test_dynamic_occurs_search_all_and_recursive_perform(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from pathlib import Path

        source_path = Path(__file__).resolve().parents[1] / "samples" / "el_multi_tabla_diabolico.cbl"
        source = source_path.read_text(encoding="utf-8")
        program = cobol2py.parse_cobol(source, source_path=source_path)
        table = next(variable for variable in program.variables if variable.name == "WS-ITEM")
        self.assertEqual(
            (table.is_array, table.is_group, table.depending_on, table.ascending_key, table.indexed_by),
            (True, True, "WS-TABLE-SIZE", "WS-ITEM-ID", "WS-IDX"),
            repr(table),
        )
        generated = cobol2py.emit_python(program)
        compile(generated, "<el-multi-tabla-diabolico>", "exec")
        namespace = {"__name__": "generated_test"}
        output = StringIO()
        with redirect_stdout(output):
            exec(generated, namespace)
            namespace["_cobol_dispatch"]("MAIN-LOGIC")
        self.assertEqual(
            output.getvalue(),
            "INICIO DE DIABLURA NUMERO 2\n"
            + "VALOR RECURSIVO FINAL: 700\n",
            generated,
        )
        self.assertEqual(namespace["ws_dynamic_table"]["ws_item"][3]["ws_item_id"], "EAGLE")
        self.assertEqual(namespace["ws_dynamic_table"]["ws_item"][3]["ws_item_val"], 500)
        self.assertEqual(namespace["ws_control"]["ws_found_idx"], 4)
        self.assertEqual(namespace["ws_idx"], 4)
        self.assertEqual(namespace["ws_control"]["ws_result_num"], 700)

class EmptyTryRegressionTests(unittest.TestCase):
    def test_comment_only_entrypoint_emits_valid_try_body(self):
        program = cobol2py.Program(
            paragraphs={"__MAIN__": [
                cobol2py.Node(kind="stmt", text="UNSUPPORTED VERB", line=1)
            ]},
            paragraph_order=["__MAIN__"],
        )
        generated = cobol2py.emit_python(program)
        compile(generated, "<comment-only-entrypoint>", "exec")
        self.assertIn("        pass", generated)



class ExternalCorpusSyntaxRegressionTests(unittest.TestCase):
    def test_equals_synonym_generates_python_comparison(self):
        self.assertEqual(cobol2py.translate_condition('OPCAO EQUALS "n"'), 'opcao == "n"')
        self.assertEqual(cobol2py.translate_condition('OPCAO EQUALS TO "N"'), 'opcao == "N"')

    def test_greater_shorthand_condition_generates_python_comparison(self):
        self.assertEqual(cobol2py.translate_condition("RECORD-COUNT GREATER 50"), "record_count > 50")
        self.assertEqual(cobol2py.translate_condition("RECORD-COUNT GREATER THAN 50"), "record_count > 50")
        self.assertEqual(cobol2py.translate_condition("RECORD-COUNT GREATER OR EQUAL 50"), "record_count >= 50")
        self.assertEqual(cobol2py.translate_condition("RECORD-COUNT LESS OR EQUAL 50"), "record_count <= 50")

    def test_not_equal_phrase_is_not_split_into_python_not_and_equality(self):
        self.assertEqual(cobol2py.translate_condition("WS-STAT NOT EQUAL 10"), "ws_stat != 10")
        self.assertEqual(cobol2py.translate_condition("WS-STAT NOT EQUAL TO 10"), "ws_stat != 10")

    def test_digit_leading_cobol_data_names_become_valid_python_identifiers(self):
        variables = {
            "11A": cobol2py.CobolVar(level=77, name="11A", pic="9(4)", value="9")
        }
        translated = cobol2py.translate_expr("11A", variables)
        self.assertEqual(translated, "cobol_11a")
        compile(translated + " = 9", "<generated>", "exec")
        self.assertEqual(cobol2py.normalize_name("42-DATANAMES"), "cobol_42_datanames")


class CobolIntrinsicFunctionRegressionTests(unittest.TestCase):
    def test_numval_intrinsic_is_emitted_as_a_numeric_conversion(self):
        translated = cobol2py.translate_expr("FUNCTION NUMVAL(WS-AMOUNT)")
        self.assertEqual(translated, "float(ws_amount)")
        compile(translated, "<numval-intrinsic>", "eval")

    def test_numval_c_uses_currency_aware_conversion(self):
        translated = cobol2py.translate_expr("FUNCTION NUMVAL-C(WS-AMOUNT)")
        self.assertEqual(translated, "_cobol_numval_c(ws_amount)")
        compile(translated, "<numval-c-intrinsic>", "eval")

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. NUMVALCTEST.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "    STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<numval-c-runtime>", "exec"), namespace)
        convert = namespace["_cobol_numval_c"]
        self.assertAlmostEqual(convert("$1,234.56"), 1234.56)
        self.assertAlmostEqual(convert("-$123.45"), -123.45)
        self.assertAlmostEqual(convert("(€9.50)"), -9.50)
        self.assertAlmostEqual(convert("  42.00 USD  "), 42.00)

    def test_case_and_trim_intrinsics_are_valid_python_calls(self):
        cases = {
            "FUNCTION LOWER-CASE(WS-NAME)": "(ws_name).lower()",
            "FUNCTION UPPER-CASE(WS-NAME)": "(ws_name).upper()",
            "FUNCTION TRIM(WS-NAME)": "(ws_name).strip()",
            "FUNCTION LENGTH(WS-NAME)": "len(ws_name)",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                translated = cobol2py.translate_expr(source)
                self.assertEqual(translated, expected)
                compile(translated, "<cobol-intrinsic>", "eval")

    def test_current_date_intrinsic_emits_valid_python_expression(self):
        translated = cobol2py.translate_expr("FUNCTION CURRENT-DATE")
        self.assertIn("datetime.now().astimezone()", translated)
        compile(translated, "<current-date-intrinsic>", "eval")


class StandaloneEqualConditionRegressionTests(unittest.TestCase):
    def test_standalone_equal_phrase_becomes_python_equality(self):
        translated = cobol2py.translate_condition("FIM-ARQ EQUAL 1")
        self.assertEqual(translated, "fim_arq == 1")
        compile(translated, "<standalone-equal>", "eval")


class MultidimensionalTableReferenceRegressionTests(unittest.TestCase):
    def test_multiple_numeric_subscripts_become_zero_based_python_indexes(self):
        translated = cobol2py.translate_expr("ENTRY-2(03, 05)")
        self.assertEqual(translated, "entry_2[2][4]")
        compile(translated, "<multi-subscript>", "eval")

    def test_multiple_subscripts_are_accepted_in_data_reference_parser(self):
        self.assertEqual(
            cobol2py.normalize_data_reference("ENTRY-2(03, 05)"),
            "entry_2[2][4]",
        )


class NegatedComparisonAndFigurativeConstantTests(unittest.TestCase):
    def test_not_before_comparison_operator_inverts_operator(self):
        cases = {
            "DECL-EXEC-SW NOT = SPACE": "decl_exec_sw != ' '",
            "WS-NUM NOT < 10": "ws_num >= 10",
            "WS-NUM NOT > 10": "ws_num <= 10",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                translated = cobol2py.translate_condition(source)
                self.assertEqual(translated, expected)
                compile(translated, "<not-comparison>", "eval")

    def test_figurative_constants_survive_expression_tokenization(self):
        for source, expected in [
            ("LOW-VALUES", "\x00"),
            ("HIGH-VALUES", "\xff"),
            ("SPACES", " "),
            ("ZEROS", 0),
        ]:
            with self.subTest(source=source):
                translated = cobol2py.translate_expr(source)
                self.assertEqual(ast.literal_eval(translated), expected)
                compile(translated, "<figurative-constant>", "eval")


class AllFigurativeConstantRegressionTests(unittest.TestCase):
    def test_all_quote_initializes_fixed_width_field_with_quotes(self):
        variable = cobol2py.CobolVar(level=77, name="IF-D5", pic="X(10)", value="ALL QUOTE")
        self.assertEqual(variable.py_default(), repr('"' * 10))

    def test_all_low_values_decodes_to_low_value_byte(self):
        self.assertEqual(cobol2py.decode_cobol_all_literal("ALL LOW-VALUES"), chr(0))


class CurrentDateAndNextSentenceRegressionTests(unittest.TestCase):
    def test_current_date_value_clause_emits_valid_python_expression(self):
        translated = cobol2py.translate_literal("FUNCTION CURRENT-DATE")
        compile(translated, "<current-date-value>", "eval")

    def test_next_sentence_is_not_included_in_if_condition(self):
        translated = cobol2py.translate_condition("A = 'A' NEXT SENTENCE")
        self.assertEqual(translated, 'a == "A"')
        compile(translated, "<next-sentence-condition>", "eval")


class ParenthesizedNumericLiteralRegressionTests(unittest.TestCase):
    def test_parenthesized_leading_zero_number_is_normalized(self):
        translated = cobol2py.translate_literal("(01)")
        self.assertEqual(translated, "(1)")
        compile(translated, "<parenthesized-number>", "eval")


class CobolNumericIntrinsicRegressionTests(unittest.TestCase):
    def test_common_math_intrinsics_emit_valid_python(self):
        cases = {
            "FUNCTION ASIN(1.0)": "__import__('math').asin(1.0)",
            "FUNCTION SQRT(9)": "__import__('math').sqrt(9)",
            "FUNCTION COS(0)": "__import__('math').cos(0)",
            "FUNCTION ABS(-3)": "__import__('math').fabs(-3)",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                translated = cobol2py.translate_expr(source)
                self.assertEqual(translated, expected)
                compile(translated, "<numeric-intrinsic>", "eval")


class CobolOrdinalAndFinanceIntrinsicRegressionTests(unittest.TestCase):
    def test_ordinal_and_integer_intrinsics_emit_valid_python(self):
        cases = {
            'FUNCTION ORD("A")': '(ord("A") + 1)',
            "FUNCTION CHAR(66)": "chr(int(66) - 1)",
            "FUNCTION INTEGER(123.456)": "__import__('math').floor(123.456)",
            "FUNCTION INTEGER-PART(-123.456)": "int(-123.456)",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                translated = cobol2py.translate_expr(source)
                self.assertEqual(translated, expected)
                compile(translated, "<ordinal-intrinsic>", "eval")

    def test_present_value_intrinsic_handles_multiple_payments(self):
        translated = cobol2py.translate_expr("FUNCTION PRESENT-VALUE(0, 23, 12, 9)")
        self.assertIn("enumerate(_payments, 1)", translated)
        compile(translated, "<present-value-intrinsic>", "eval")


class IntrinsicLiteralRoutingRegressionTests(unittest.TestCase):
    def test_function_intrinsics_pass_through_expression_translation(self):
        cases = {
            "FUNCTION LOWER-CASE(WS-NAME)": "(ws_name).lower()",
            "FUNCTION ASIN(1.0)": "__import__('math').asin(1.0)",
            "FUNCTION PRESENT-VALUE(0, 23, 12, 9)": None,
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                translated = cobol2py.translate_literal(source)
                if expected is not None:
                    self.assertEqual(translated, expected)
                compile(translated, "<intrinsic-literal>", "eval")


class NestedIntrinsicArgumentRegressionTests(unittest.TestCase):
    def test_math_intrinsic_accepts_nested_parenthesized_argument(self):
        translated = cobol2py.translate_expr("FUNCTION ASIN((3 / 3) - 1)")
        self.assertIn("__import__('math').asin(", translated)
        compile(translated, "<nested-math-intrinsic>", "eval")

    def test_present_value_accepts_parenthesized_payment_expressions(self):
        translated = cobol2py.translate_expr("FUNCTION PRESENT-VALUE(-0.5, (2 + 3), (6 / 3), (9 - 3))")
        self.assertIn("enumerate(_payments, 1)", translated)
        compile(translated, "<nested-present-value>", "eval")


class ReferenceModificationRegressionTests(unittest.TestCase):
    def test_numeric_reference_modification_becomes_python_slice(self):
        translated = cobol2py.translate_expr("WS-TEXT(1:2)")
        self.assertEqual(translated, "ws_text[0:(0) + (2)]")
        compile(translated, "<reference-modification>", "eval")

    def test_variable_reference_modification_becomes_python_slice(self):
        translated = cobol2py.translate_expr("WS-TEXT(WS-START:1)")
        self.assertEqual(translated, "ws_text[ws_start - 1:(ws_start - 1) + (1)]")
        compile(translated, "<variable-reference-modification>", "eval")


class AbbreviatedCombinedConditionRegressionTests(unittest.TestCase):
    def test_or_literal_repeats_previous_condition_subject(self):
        variables = {
            "WS-OPCAO": cobol2py.CobolVar(level=1, name="WS-OPCAO", pic="X(1)")
        }
        translated = cobol2py.translate_condition("WS-OPCAO = 'S' OR 'N'", variables)
        self.assertIn("or ws_opcao.ljust(1) ==", translated)
        self.assertNotIn("or ==", translated)
        compile(translated, "<abbreviated-condition>", "eval")

    def test_numeric_range_repeats_subject_and_relation(self):
        translated = cobol2py.translate_condition("WS-NUM > 10 AND < 21")
        self.assertEqual(translated, "ws_num > 10 and ws_num < 21")
        self.assertTrue(eval(translated, {"ws_num": 15}))
        self.assertFalse(eval(translated, {"ws_num": 25}))

    def test_numeric_or_value_repeats_subject_and_equality(self):
        translated = cobol2py.translate_condition("WS-NUM = 1 OR 2")
        self.assertEqual(translated, "ws_num == 1 or ws_num == 2")
        self.assertTrue(eval(translated, {"ws_num": 2}))
        self.assertFalse(eval(translated, {"ws_num": 3}))

    def test_two_complete_conditions_are_not_treated_as_abbreviated(self):
        translated = cobol2py.translate_condition("WS-A > 1 AND WS-B > 2")
        self.assertEqual(translated, "ws_a > 1 and ws_b > 2")


class DigitLeadingHyphenatedNameRegressionTests(unittest.TestCase):
    def test_digit_leading_hyphenated_identifier_is_not_split_as_arithmetic(self):
        translated = cobol2py.translate_condition("0-C = 1")
        self.assertEqual(translated, "cobol_0_c == 1")
        compile(translated, "<digit-leading-hyphenated-name>", "eval")


class ReferenceModificationSliceSemanticsTests(unittest.TestCase):
    def test_arithmetic_expression_in_table_subscript_is_preserved(self):
        variables = {
            "WS-TABLE": cobol2py.CobolVar(
                level=1, name="WS-TABLE", pic="9(2)", is_array=True, occurs=5
            ),
            "WS-INDEX": cobol2py.CobolVar(level=1, name="WS-INDEX", pic="9(2)"),
        }
        translated = cobol2py.translate_expr("WS-TABLE(WS-INDEX + 1)", variables)
        self.assertEqual(translated, "ws_table[ws_index + 1 - 1]")
        compile(translated, "<arithmetic-table-subscript>", "eval")

    def test_variable_start_and_length_become_zero_based_python_slice(self):
        translated = cobol2py.translate_expr("NEW-STRING(SUB-1:1)")
        self.assertEqual(translated, "new_string[sub_1 - 1:(sub_1 - 1) + (1)]")
        compile(translated, "<reference-modification>", "eval")

    def test_numeric_reference_modification_uses_one_based_cobol_positions(self):
        translated = cobol2py.translate_expr("WS-TEXT(2:3)")
        self.assertEqual(translated, "ws_text[1:(1) + (3)]")
        self.assertEqual(eval(translated, {"ws_text": "abcdef"}), "bcd")


class AbbreviatedRelationOperatorRegressionTests(unittest.TestCase):
    def test_greater_or_equal_sign_phrase_is_normalized_before_greater(self):
        translated = cobol2py.translate_condition("WS-NUM GREATER OR = WS-NUM2")
        self.assertEqual(translated, "ws_num >= ws_num2")
        compile(translated, "<greater-or-equal>", "eval")

    def test_less_or_equal_sign_phrase_is_normalized_before_less(self):
        translated = cobol2py.translate_condition("WS-NUM LESS OR = WS-NUM2")
        self.assertEqual(translated, "ws_num <= ws_num2")
        compile(translated, "<less-or-equal>", "eval")


class DisplayOperandSplittingRegressionTests(unittest.TestCase):
    def test_parenthesized_numeric_operands_remain_separate(self):
        self.assertEqual(cobol2py.split_cobol_items("(01) (01) ERASE"), ["(01)", "(01)", "ERASE"])

    def test_quoted_spaces_and_nested_commas_are_preserved(self):
        self.assertEqual(
            cobol2py.split_cobol_items('"HELLO WORLD" WS-TEXT(1, 2), ERASE'),
            ['"HELLO WORLD"', "WS-TEXT(1, 2)", "ERASE"],
        )

    def test_parenthesized_numeric_display_generates_valid_python(self):
        translated = cobol2py.translate_statement("DISPLAY (01) (01) ERASE", set(), {})
        self.assertIsNotNone(translated)
        compile("\\n".join(translated or []), "<display-operands>", "exec")


class ComputeSizeErrorClauseRegressionTests(unittest.TestCase):
    def test_size_error_phrase_is_not_translated_as_expression_tokens(self):
        translated = cobol2py.translate_statement(
            "COMPUTE WS-TOTAL = WS-LEFT + WS-RIGHT ON SIZE ERROR",
            set(),
            {},
        )
        self.assertIsNotNone(translated)
        self.assertEqual(translated, ["ws_total = ws_left + ws_right"])
        compile("\\n".join(translated or []), "<compute-size-error>", "exec")


class FigurativeConstantIdentifierBoundaryTests(unittest.TestCase):
    def test_hyphenated_data_names_starting_with_zero_are_not_constants(self):
        self.assertEqual(cobol2py.translate_expr("ZERO-C"), "zero_c")
        self.assertEqual(cobol2py.translate_condition("ZERO-C = 1"), "zero_c == 1")

    def test_hyphenated_data_names_starting_with_space_are_not_constants(self):
        self.assertEqual(cobol2py.translate_expr("SPACE-C"), "space_c")


class MoveMultipleTargetsRegressionTests(unittest.TestCase):
    def test_move_literal_to_multiple_receivers_applies_each_pic_width(self):
        variables = {
            "WS-SHORT": cobol2py.CobolVar(level=1, name="WS-SHORT", pic="X(2)"),
            "WS-LONG": cobol2py.CobolVar(level=1, name="WS-LONG", pic="X(5)"),
        }
        translated = cobol2py.translate_statement('MOVE "ABCDE" TO WS-SHORT WS-LONG', set(), variables)
        self.assertEqual(len(translated or []), 2, translated)
        namespace = {}
        exec("\n".join(translated or []), namespace)
        self.assertEqual(namespace["ws_short"], "AB")
        self.assertEqual(namespace["ws_long"], "ABCDE")

    def test_to_inside_quoted_source_is_not_mistaken_for_clause_separator(self):
        variables = {
            "WS-A": cobol2py.CobolVar(level=1, name="WS-A", pic="X(2)"),
            "WS-B": cobol2py.CobolVar(level=1, name="WS-B", pic="X(4)"),
        }
        translated = cobol2py.translate_statement('MOVE "TO" TO WS-A WS-B', set(), variables)
        self.assertEqual(len(translated or []), 2, translated)
        namespace = {}
        exec("\n".join(translated or []), namespace)
        self.assertEqual(namespace["ws_a"], "TO")
        self.assertEqual(namespace["ws_b"], "TO  ")


class MoveCorrespondingRegressionTests(unittest.TestCase):
    def test_matching_group_fields_are_copied_with_target_width(self):
        variables = {
            "SRC": cobol2py.CobolVar(level=1, name="SRC", is_group=True),
            "SRC-CODE": cobol2py.CobolVar(level=5, name="CODE", pic="X(3)", parent_name="SRC"),
            "DST": cobol2py.CobolVar(level=1, name="DST", is_group=True),
            "DST-CODE": cobol2py.CobolVar(level=5, name="CODE", pic="X(5)", parent_name="DST"),
        }
        translated = cobol2py.translate_statement("MOVE CORRESPONDING SRC TO DST", set(), variables)
        self.assertEqual(translated, ["dst['code'] = str(src['code'])[:5].ljust(5)"])
        namespace = {"src": {"code": "ABC"}, "dst": {"code": "     "}}
        exec("\n".join(translated or []), namespace)
        self.assertEqual(namespace["dst"]["code"], "ABC  ")


class QualifiedDisplayOperandRegressionTests(unittest.TestCase):
    def test_of_qualified_reference_remains_one_display_operand(self):
        self.assertEqual(
            cobol2py.split_cobol_items("WS-NAME OF WS-CUSTOMER ERASE"),
            ["WS-NAME OF WS-CUSTOMER", "ERASE"],
        )


class CrossBackendIdentifierNormalizationTests(unittest.TestCase):
    def test_java_reserved_word_does_not_change_python_identifier(self):
        self.assertEqual(cobol2py.normalize_identifier("record"), "record")
        self.assertEqual(cobol2py.normalize_name("FILE-RECORD-INFORMATION-REC"), "file_record_information_rec")
        self.assertEqual(cobol2py.translate_expr("RECORD"), "record")

    def test_java_reserved_word_is_escaped_for_java(self):
        self.assertEqual(cobol2py.normalize_java_identifier("record"), "cobol_record")
        self.assertEqual(cobol2py.normalize_java_name("record"), "cobol_record")
        self.assertEqual(cobol2py.normalize_java_name("ITEM(IDX)"), "item[idx - 1]")
        self.assertEqual(cobol2py.translate_java_expr("RECORD", {}), "cobol_record")
        self.assertEqual(cobol2py.normalize_java_name("FILE-RECORD-INFORMATION-REC"), "file_record_information_rec")


class SubscriptedRedefinesGroupMoveTests(unittest.TestCase):
    def test_group_move_to_multidimensional_redefines_element_keeps_subscripts(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. OVERLAYGROUPMOVE.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 SOURCE-REC.
   05 SOURCE-ALPHA PIC X(2) VALUE "AB".
   05 SOURCE-NUM PIC 9(2) VALUE 12.
01 BASE-TABLE.
   05 BASE-ROW OCCURS 2 TIMES.
      10 BASE-SUBROW OCCURS 2 TIMES.
         15 BASE-ENTRY PIC X(4).
01 VIEW-TABLE REDEFINES BASE-TABLE.
   05 VIEW-ROW OCCURS 2 TIMES.
      10 VIEW-SUBROW OCCURS 2 TIMES.
         15 VIEW-ENTRY PIC X(4).
01 IDX-1 PIC 9 VALUE 1.
01 IDX-2 PIC 9 VALUE 2.
PROCEDURE DIVISION.
MAIN.
    MOVE SOURCE-REC TO VIEW-ENTRY(IDX-1, IDX-2).
    DISPLAY BASE-ENTRY(1, 2).
    GOBACK.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        compile(generated, "<subscripted-redefines-group-move>", "exec")
        self.assertIn("_cobol_set('VIEW-ENTRY'", generated)
        self.assertRegex(generated, r"_cobol_set\('VIEW-ENTRY'.*int\(idx_1\) - 1, int\(idx_2\) - 1\)")
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "AB12\n", generated)


class NestedRedefinesGroupMoveTests(unittest.TestCase):
    def test_group_move_reads_and_writes_base_fields_of_nested_redefines(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. NESTEDOVERLAYMOVE.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 SOURCE-GROUP.
   02 SOURCE-BASE PIC X(20).
   02 SOURCE-NUM REDEFINES SOURCE-BASE PIC 9(20).
   02 SOURCE-TAIL PIC X(2).
01 TARGET-RECORD.
   02 TARGET-GROUP.
      03 TARGET-BASE PIC X(20).
      03 TARGET-NUM REDEFINES TARGET-BASE PIC 9(20).
      03 TARGET-TAIL PIC X(2).
PROCEDURE DIVISION.
MAIN.
    MOVE "ABCDEFGHIJKLMNOPQRST" TO SOURCE-BASE.
    MOVE "UV" TO SOURCE-TAIL.
    MOVE SOURCE-GROUP TO TARGET-GROUP.
    DISPLAY TARGET-BASE.
    DISPLAY TARGET-TAIL.
    GOBACK.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        compile(generated, "<nested-redefines-group-move>", "exec")
        self.assertIn("_cobol_set('TARGET-BASE'", generated)
        self.assertIn("_cobol_get('SOURCE-BASE')", generated)
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "ABCDEFGHIJKLMNOPQRST\nUV\n", generated)


class NestedOccursGroupMoveTests(unittest.TestCase):
    def test_group_move_to_nested_occurs_field_keeps_all_ancestor_subscripts(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. NESTEDOCCURSMOVE.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 SOURCE-REC.
   05 SOURCE-ALPHA PIC X(2) VALUE "AB".
   05 SOURCE-NUM PIC X(2) VALUE "CD".
01 TABLE-REC.
   05 GRP-ENTRY OCCURS 2 TIMES.
      10 ENTRY-1 PIC X(2).
      10 GRP2-ENTRY OCCURS 2 TIMES.
         15 ENTRY-2 PIC X(4).
01 IDX-1 PIC 9 VALUE 1.
01 IDX-2 PIC 9 VALUE 2.
PROCEDURE DIVISION.
MAIN.
    MOVE SOURCE-REC TO ENTRY-2 (IDX-1, IDX-2).
    DISPLAY ENTRY-2 (IDX-1, IDX-2).
    GOBACK.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        compile(generated, "<nested-occurs-group-move>", "exec")
        self.assertIn(
            "table_rec['grp_entry'][int(idx_1) - 1]['grp2_entry'][int(idx_2) - 1]['entry_2']",
            generated,
        )
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "ABCD\n", generated)


class SpaceSeparatedSubscriptRegressionTests(unittest.TestCase):
    def test_numeric_subscripts_separated_by_spaces(self):
        self.assertEqual(cobol2py.normalize_data_reference("TABLE(1 2)"), "table[0][1]")

    def test_identifier_subscripts_separated_by_spaces(self):
        self.assertEqual(
            cobol2py.normalize_data_reference("TABLE(IDX1 IDX2 IDX3)"),
            "table[int(idx1) - 1][int(idx2) - 1][int(idx3) - 1]",
        )

    def test_text_backed_identifier_subscript_is_coerced_to_integer(self):
        variables = {
            "TABLE": cobol2py.CobolVar(
                level=1, name="TABLE", is_array=True, occurs=3
            ),
            "WS-INDEX": cobol2py.CobolVar(
                level=1, name="WS-INDEX", pic="X"
            ),
        }
        translated = cobol2py.normalize_data_reference("TABLE(WS-INDEX)", variables)
        self.assertEqual(translated, "table[int(ws_index) - 1]")
        self.assertEqual(eval(translated, {"table": ["A", "B", "C"], "ws_index": "2"}), "B")

    def test_arithmetic_subscript_is_not_split_on_spaces(self):
        self.assertEqual(
            cobol2py.normalize_data_reference("TABLE(IDX + 1)"),
            "table[idx + 1 - 1]",
        )


class NestedAndMiscIntrinsicRegressionTests(unittest.TestCase):
    def test_nested_function_intrinsics_do_not_leave_function_keyword(self):
        translated = cobol2py.translate_expr("FUNCTION ASIN(FUNCTION ASIN(PI - 3))")
        self.assertNotIn("function asin", translated.lower())
        compile(translated, "<nested-intrinsic>", "eval")

    def test_mod_intrinsic_becomes_python_remainder(self):
        translated = cobol2py.translate_expr("FUNCTION MOD(5, 3)")
        self.assertEqual(translated, "(5 % (3))")
        self.assertEqual(eval(translated), 2)

    def test_rem_intrinsic_truncates_quotient_toward_zero(self):
        positive = cobol2py.translate_expr("FUNCTION REM(7, 3)")
        negative = cobol2py.translate_expr("FUNCTION REM(-7, 3)")
        self.assertEqual(eval(positive), 1)
        self.assertEqual(eval(negative), -1)

    def test_statistical_intrinsics_accept_space_separated_arguments(self):
        translated = cobol2py.translate_expr("FUNCTION MEAN(1 2 6)")
        self.assertEqual(eval(translated), 3)

    def test_statistical_intrinsics_match_expected_values(self):
        cases = {
            "FUNCTION MEAN(1, 2, 6)": 3,
            "FUNCTION MEDIAN(1, 5, 9)": 5,
            "FUNCTION MIDRANGE(1, 5, 9)": 5,
            "FUNCTION RANGE(1, 5, 9)": 8,
            "FUNCTION SUM(1, 2, 6)": 9,
            "FUNCTION VARIANCE(1, 2, 3)": 2 / 3,
            "FUNCTION STANDARD-DEVIATION(1, 2, 3)": (2 / 3) ** 0.5,
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                translated = cobol2py.translate_expr(source)
                self.assertAlmostEqual(eval(translated), expected)

    def test_concatenate_intrinsic_becomes_string_join(self):
        translated = cobol2py.translate_expr('FUNCTION CONCATENATE(WS-A, ",")')
        self.assertEqual(translated, """''.join(str(_item) for _item in [ws_a, ","])""")
        compile(translated, "<concatenate-intrinsic>", "eval")

    def test_random_intrinsic_without_arguments_is_valid_python(self):
        translated = cobol2py.translate_expr("FUNCTION RANDOM")
        self.assertEqual(translated, "__import__('random').random()")
        compile(translated, "<random-intrinsic>", "eval")

    def test_reverse_intrinsic_reverses_the_argument(self):
        translated = cobol2py.translate_expr('FUNCTION REVERSE("abc")')
        self.assertEqual(eval(translated), "cba")

    def test_factorial_intrinsic_returns_exact_integer(self):
        translated = cobol2py.translate_expr("FUNCTION FACTORIAL(5)")
        self.assertEqual(eval(translated), 120)

    def test_stored_char_length_ignores_trailing_spaces(self):
        translated = cobol2py.translate_expr('FUNCTION STORED-CHAR-LENGTH("abc   ")')
        self.assertEqual(eval(translated), 3)


class HexadecimalLiteralRegressionTests(unittest.TestCase):
    def test_hexadecimal_literal_with_double_quotes(self):
        translated = cobol2py.translate_literal('X"0D"')
        self.assertEqual(eval(translated), "\r")
        compile(translated, "<hex-literal>", "eval")

    def test_hexadecimal_literal_survives_expression_tokenization(self):
        translated = cobol2py.translate_expr('X"0D"')
        self.assertEqual(eval(translated), "\r")
        compile(translated, "<hex-expression>", "eval")

    def test_hexadecimal_literal_with_single_quotes(self):
        translated = cobol2py.translate_literal("X'4142'")
        self.assertEqual(eval(translated), "AB")

    def test_hexadecimal_literal_is_kept_as_one_display_operand(self):
        items = cobol2py.split_cobol_items('X"0D" ERASE')
        self.assertEqual(items, ['X"0D"', "ERASE"])
        translated = cobol2py.translate_statement('DISPLAY X"0D" ERASE', set(), {})
        compile("\\n".join(translated or []), "<hex-display>", "exec")


class ParenthesizedDisplayListRegressionTests(unittest.TestCase):
    def test_parenthesized_comma_list_expands_into_display_operands(self):
        self.assertEqual(cobol2py.split_cobol_items("(01, 01) ERASE"), ["01", "01", "ERASE"])
        translated = cobol2py.translate_statement("DISPLAY (01, 01) ERASE", set(), {})
        self.assertIsNotNone(translated)
        compile("\\n".join(translated or []), "<parenthesized-display-list>", "exec")


class CobolAcceptEofRegressionTests(unittest.TestCase):
    def test_accept_at_eof_uses_cobol_numeric_and_alphanumeric_defaults(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from unittest.mock import patch

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. ACCEPTEOF.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-NUM PIC 9(3).",
            "01 WS-TEXT PIC X(3).",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "ACCEPT WS-NUM.",
            "ADD 1 TO WS-NUM.",
            "DISPLAY WS-NUM.",
            "ACCEPT WS-TEXT.",
            "DISPLAY WS-TEXT.",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<accept-eof-output>", "exec"), namespace)
        output = StringIO()
        with patch("builtins.input", side_effect=EOFError), redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "001\n   \n", generated)


class CobolLevel88ConditionRegressionTests(unittest.TestCase):
    def test_level_88_condition_name_compares_parent_field(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. COND88.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-STATUS PIC X VALUE 'Y'.",
            "   88 WS-OK VALUE 'Y'.",
            "   88 WS-NO VALUE 'N'.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "IF WS-OK",
            "    DISPLAY 'OK'",
            "ELSE",
            "    DISPLAY 'NO'",
            "END-IF.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        self.assertEqual(program.condition_names["WS-OK"], ("WS-STATUS", [("'Y'", None)]))
        generated = cobol2py.emit_python(program)
        compile(generated, "<level-88>", "exec")
        namespace = {"__name__": "not_main"}
        exec(generated, namespace)
        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "OK\n", generated)

    def test_level_88_condition_name_supports_value_ranges(self):
        condition_names = {
            "WS-IN-RANGE": ("WS-NUM", [("1", "5")]),
        }
        translated = cobol2py.translate_condition(
            "WS-IN-RANGE", {"WS-NUM": cobol2py.CobolVar(level=1, name="WS-NUM", pic="9")},
            condition_names,
        )
        self.assertIn("ws_num >= 1", translated)
        self.assertIn("ws_num <= 5", translated)
        compile(translated, "<level-88-range>", "eval")


class CompoundComparisonRegressionTests(unittest.TestCase):
    def test_greater_or_equal_phrase_is_not_split_at_equal(self):
        translated = cobol2py.translate_condition("IRC-PARAMS GREATER OR EQUAL TO 1")
        self.assertEqual(translated, "irc_params >= 1")
        compile(translated, "<greater-or-equal>", "eval")

    def test_less_or_equal_phrase_is_not_split_at_equal(self):
        translated = cobol2py.translate_condition("IRC-PARAMS LESS OR EQUAL TO 1")
        self.assertEqual(translated, "irc_params <= 1")
        compile(translated, "<less-or-equal>", "eval")


class CobolDateIntrinsicRegressionTests(unittest.TestCase):
    def test_date_of_integer_converts_day_one_to_16010101(self):
        translated = cobol2py.translate_expr("FUNCTION DATE-OF-INTEGER(1)")
        compile(translated, "<date-of-integer>", "eval")
        self.assertEqual(eval(translated), 16010101)

    def test_integer_of_date_converts_16010101_to_day_one(self):
        translated = cobol2py.translate_expr("FUNCTION INTEGER-OF-DATE(16010101)")
        compile(translated, "<integer-of-date>", "eval")
        self.assertEqual(eval(translated), 1)

    def test_seconds_past_midnight_emits_valid_python(self):
        translated = cobol2py.translate_expr("FUNCTION SECONDS-PAST-MIDNIGHT")
        compile(translated, "<seconds-past-midnight>", "eval")
        self.assertGreaterEqual(eval(translated), 0)
        self.assertLess(eval(translated), 86400)


class ChainedReferenceModificationRegressionTests(unittest.TestCase):
    def test_reference_modification_after_table_subscript_is_valid_python(self):
        translated = cobol2py.translate_expr("WS-TEXT(WS-I)(WS-J:1)")
        compile(translated, "<chained-reference-modification>", "eval")
        self.assertIn("[(ws_j) - 1:", translated)


class CobolSetLevel88RegressionTests(unittest.TestCase):
    def test_set_condition_name_true_assigns_a_permitted_value(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. SETCOND88.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-STATUS PIC X VALUE 'N'.",
            "   88 WS-OK VALUE 'Y'.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "SET WS-OK TO TRUE.",
            "IF WS-OK",
            "    DISPLAY 'OK'",
            "ELSE",
            "    DISPLAY 'NO'",
            "END-IF.",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        compile(generated, "<set-level-88>", "exec")
        namespace = {"__name__": "not_main"}
        exec(generated, namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "OK\n", generated)


class CompoundRelationEqualityRegressionTests(unittest.TestCase):
    def test_redundant_equality_before_greater_or_equal_is_collapsed(self):
        translated = cobol2py.translate_condition("IRC-PARAMS = GREATER OR EQUAL TO 1")
        self.assertEqual(translated, "irc_params >= 1")
        compile(translated, "<compound-relation-equality>", "eval")

    def test_redundant_equality_before_less_or_equal_is_collapsed(self):
        translated = cobol2py.translate_condition("IRC-PARAMS = LESS OR EQUAL TO 1")
        self.assertEqual(translated, "irc_params <= 1")
        compile(translated, "<compound-relation-equality>", "eval")


class SemicolonSeparatedSubscriptRegressionTests(unittest.TestCase):
    def test_semicolon_separated_table_subscripts_become_valid_python_indexes(self):
        translated = cobol2py.translate_expr("GRP-TAB2(S21; S22)")
        self.assertEqual(translated, "grp_tab2[int(s21) - 1][int(s22) - 1]")
        compile(translated, "<semicolon-subscript>", "eval")


class CobolClassConditionRegressionTests(unittest.TestCase):
    def test_numeric_class_condition_accepts_signed_decimal_values(self):
        translated = cobol2py.translate_condition("WS-VALUE IS NUMERIC")
        compile(translated, "<numeric-class-condition>", "eval")
        self.assertTrue(eval(translated, {"ws_value": "-12.5"}))
        self.assertFalse(eval(translated, {"ws_value": "12A"}))

    def test_not_alphabetic_class_condition_rejects_digits(self):
        translated = cobol2py.translate_condition("WS-FUNC IS NOT ALPHABETIC")
        compile(translated, "<not-alphabetic-class-condition>", "eval")
        self.assertFalse(eval(translated, {"ws_func": "ABC"}))
        self.assertTrue(eval(translated, {"ws_func": "AB2"}))

    def test_alphanumeric_class_condition_allows_spaces_and_digits(self):
        translated = cobol2py.translate_condition("WS-VALUE IS ALPHANUMERIC")
        compile(translated, "<alphanumeric-class-condition>", "eval")
        self.assertTrue(eval(translated, {"ws_value": "A 12"}))
        self.assertFalse(eval(translated, {"ws_value": "A-12"}))


class CobolScopeTerminatorRegressionTests(unittest.TestCase):
    def test_end_multiply_and_end_add_do_not_get_absorbed_as_operands(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. ENDOPS.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-A PIC 9 VALUE 3.",
            "01 WS-B PIC 9 VALUE 2.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "MULTIPLY WS-A BY WS-B",
            "END-MULTIPLY",
            "ADD WS-A TO WS-B",
            "END-ADD",
            "DISPLAY WS-B",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        compile(generated, "<scope-terminators>", "exec")
        namespace = {"__name__": "not_main"}
        exec(generated, namespace)
        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "9\n", generated)


class CobolDisplayNoAdvancingRegressionTests(unittest.TestCase):
    def test_with_no_advancing_suppresses_newline_until_next_display(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. DISP-NL.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "DISPLAY 'A' WITH NO ADVANCING",
            "DISPLAY 'B'",
            "STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        compile(generated, "<display-no-advancing>", "exec")
        namespace = {"__name__": "not_main"}
        exec(generated, namespace)
        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "AB\n", generated)


class ResidualIsRelationRegressionTests(unittest.TestCase):
    def test_is_relation_word_never_becomes_python_identifier(self):
        translated = cobol2py.translate_expr("WS-STATUS IS WS-EXPECTED")
        self.assertEqual(translated, "ws_status == ws_expected")
        compile(translated, "<residual-is-relation>", "eval")


class NegatedRelationalPhraseRegressionTests(unittest.TestCase):
    def test_is_not_greater_than_maps_to_less_or_equal(self):
        self.assertEqual(
            cobol2py.translate_condition("WS-A IS NOT GREATER THAN WS-B"),
            "ws_a <= ws_b",
        )

    def test_is_not_less_than_maps_to_greater_or_equal(self):
        self.assertEqual(
            cobol2py.translate_condition("WS-A IS NOT LESS THAN WS-B"),
            "ws_a >= ws_b",
        )

    def test_negated_compound_comparison_maps_to_inverse_relation(self):
        cases = {
            "WS-A IS NOT GREATER THAN OR EQUAL TO WS-B": "ws_a < ws_b",
            "WS-A IS NOT LESS THAN OR EQUAL TO WS-B": "ws_a > ws_b",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(cobol2py.translate_condition(source), expected)


class EvaluateRelationalWhenRegressionTests(unittest.TestCase):
    def test_evaluate_supports_is_greater_than_selection(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. EVALRELATION.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 WS-CODE PIC 9 VALUE 2.",
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           EVALUATE WS-CODE",
            "               WHEN IS GREATER THAN 1",
            '                   DISPLAY "HIGH".',
            "               WHEN OTHER",
            '                   DISPLAY "LOW".',
            "           END-EVALUATE.",
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<evaluate-relational-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "HIGH\n", generated)


class FullProgramIsKeywordRegressionTests(unittest.TestCase):
    def test_is_in_pic_value_and_if_condition_does_not_become_identifier(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. ISKEYWORDTEST.",
            "       DATA DIVISION.",
            "       WORKING-STORAGE SECTION.",
            "       01 ERROR-COUNTER PIC 9 VALUE 0.",
            "       01 DELETE-COUNTER PIC 9 VALUE 0.",
            '       01 WS-CHAR PIC IS X VALUE IS "A".',
            "       PROCEDURE DIVISION.",
            "       MAIN.",
            "           IF ERROR-COUNTER IS EQUAL TO ZERO",
            '               DISPLAY "PASS".',
            "           END-IF.",
            "           IF DELETE-COUNTER IS EQUAL TO ZERO",
            '               DISPLAY "DELETE".',
            "           END-IF.",
            "           STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="fixed"))
        self.assertNotIn("cobol_is", generated)
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<is-keyword-output>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "PASS\nDELETE\n", generated)


class ResidualIsDataReferenceFallbackRegressionTests(unittest.TestCase):
    def test_relation_is_in_data_reference_fallback_becomes_comparison(self):
        translated = cobol2py.normalize_data_reference("WS-STATUS IS WS-EXPECTED")
        self.assertEqual(translated, "ws_status == ws_expected")
        compile(translated, "<data-reference-is-relation>", "eval")

    def test_is_equal_to_in_data_reference_fallback_becomes_comparison(self):
        translated = cobol2py.normalize_data_reference("ERROR-COUNTER IS EQUAL TO ZERO")
        self.assertEqual(translated, "error_counter == 0")
        compile(translated, "<data-reference-is-equal>", "eval")


class TruncatedValueIsClauseRegressionTests(unittest.TestCase):
    def test_value_is_at_end_of_truncated_declaration_is_not_a_literal(self):
        variables = cobol2py.parse_variables([(1, "01 WS-CHAR PIC X VALUE IS")])
        self.assertEqual(len(variables), 1)
        self.assertIsNone(variables[0].value)
        self.assertEqual(variables[0].py_default(), repr(" "))

    def test_value_is_keyword_is_not_mistaken_for_a_data_literal(self):
        variables = cobol2py.parse_variables([
            (1, '01 WS-CHAR PIC X(3) VALUE IS "ABC".'),
            (2, "01 WS-NEXT PIC X VALUE IS"),
        ])
        self.assertEqual(variables[0].value, '"ABC"')
        self.assertEqual(variables[0].py_default(), 'str("ABC")[:3].ljust(3)')
        self.assertIsNone(variables[1].value)
        self.assertEqual(variables[1].py_default(), repr(" "))
        # If punctuation or a following clause follows IS, regex backtracking
        # must not reinterpret the clause keyword as a literal data-name.
        self.assertIsNone(cobol2py.RE_VALUE.search("VALUE IS, OCCURS 3 TIMES"))


class InitializeStatementRegressionTests(unittest.TestCase):
    def test_initialize_elementary_item_uses_category_default_not_value_clause(self):
        variables = {
            item.name: item
            for item in cobol2py.parse_variables([
                (1, '01 WS-NAME PIC X(3) VALUE "ABC".')
            ])
        }
        translated = cobol2py.translate_statement("INITIALIZE WS-NAME", set(), variables)
        self.assertEqual(translated, ["ws_name = '   '"])
        compile(translated[0], "<initialize-elementary>", "exec")

    def test_initialize_simple_group_resets_alphanumeric_and_numeric_children(self):
        variables = {
            item.name: item
            for item in cobol2py.parse_variables([
                (1, "01 WS-REC."),
                (2, "05 WS-NAME PIC X(3) VALUE 'ABC'."),
                (3, "05 WS-COUNT PIC 9(2) VALUE 12."),
            ])
        }
        translated = cobol2py.translate_statement("INITIALIZE WS-REC", set(), variables)
        self.assertEqual(
            translated,
            ["ws_rec['ws_name'] = '   '", "ws_rec['ws_count'] = 0"],
        )
        compile("\n".join(translated), "<initialize-group>", "exec")


class BareAlphanumericValueRegressionTests(unittest.TestCase):
    def test_unquoted_word_value_does_not_emit_unbound_python_name(self):
        variable = cobol2py.CobolVar(
            level=2, name="COBOL-IS", pic="X(99)", value="COBOL-IS"
        )
        generated = variable.py_default()
        compile(generated, "<cobol-value-default>", "eval")
        self.assertEqual(eval(generated), "COBOL-IS".ljust(99))


class GroupMoveFillRegressionTests(unittest.TestCase):
    def test_move_space_to_group_preserves_group_and_child_fields(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. GROUPFILL.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 TEST-RESULTS.",
            "   02 FEATURE PIC X(20).",
            "   02 P-OR-F PIC X(5).",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "   MOVE SPACE TO TEST-RESULTS.",
            '   MOVE "PASS" TO FEATURE OF TEST-RESULTS.',
            "   DISPLAY FEATURE OF TEST-RESULTS.",
            "   STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        self.assertNotIn("test_results = ' '", generated)
        self.assertIn("test_results['feature'] = '                    '", generated)
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<group-move-space>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "PASS                \n")
    def test_move_alphanumeric_literal_to_group_preserves_nested_storage(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. GROUPLITERAL.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 TEST-RESULTS.",
            "   02 FEATURE PIC X(4).",
            "   02 P-OR-F PIC X.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            '   MOVE "AB" TO TEST-RESULTS.',
            "   DISPLAY FEATURE OF TEST-RESULTS.",
            "   STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        self.assertNotIn('test_results = "AB"', generated)
        # Group MOVE is emitted as one padded byte sequence and distributed
        # into the elementary fields; assert the storage-preserving path rather
        # than requiring a particular direct-assignment implementation.
        self.assertIn('_cobol_group_move_value = (str("AB"))[:5].ljust(5)', generated)
        self.assertIn("test_results['feature'] = _cobol_group_move_value[0:4].ljust(4)", generated)
        self.assertIn("test_results['p_or_f'] = _cobol_group_move_value[4:5].ljust(1)", generated)
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<group-move-literal>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "AB  \n")

    def test_move_space_to_occurs_group_fills_each_row_without_replacing_table(self):
        variables = {
            "TEST-RESULTS": cobol2py.CobolVar(
                level=1, name="TEST-RESULTS", is_group=True
            ),
            "RESULT-ROW": cobol2py.CobolVar(
                level=2, name="RESULT-ROW", is_group=True, is_array=True,
                occurs=2, parent_name="TEST-RESULTS"
            ),
            "FEATURE": cobol2py.CobolVar(
                level=3, name="FEATURE", pic="X(4)", parent_name="RESULT-ROW"
            ),
            "P-OR-F": cobol2py.CobolVar(
                level=3, name="P-OR-F", pic="X", parent_name="RESULT-ROW"
            ),
        }
        assignments = cobol2py.translate_group_fill_move(
            "SPACE", "TEST-RESULTS", variables
        )
        self.assertEqual(assignments, [
            "test_results['result_row'][0]['feature'] = '    '",
            "test_results['result_row'][0]['p_or_f'] = ' '",
            "test_results['result_row'][1]['feature'] = '    '",
            "test_results['result_row'][1]['p_or_f'] = ' '",
        ])


class NistGroupStorageRegressionTests(unittest.TestCase):
    def test_fixed_format_nist_test_results_remains_a_group(self):
        from contextlib import redirect_stdout
        from io import StringIO

        fixture = Path(__file__).parent / "fixtures" / "IC222A-working-storage.cbl"
        source = fixture.read_text(encoding="utf-8")
        program = cobol2py.parse_cobol(source, source_format="auto")
        variables = {variable.name.upper(): variable for variable in program.variables}
        self.assertIn("TEST-RESULTS", variables)
        self.assertTrue(variables["TEST-RESULTS"].is_group)
        self.assertIsNone(variables["TEST-RESULTS"].parent_name)
        self.assertTrue(any(
            (variable.parent_name or "").upper() == "TEST-RESULTS"
            for variable in program.variables
        ))

        generated = cobol2py.emit_python(program)
        self.assertIn("test_results: dict", generated)
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<nist-group-storage>", "exec"), namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "PASS                \n")


    def test_nist_move_sequence_never_assigns_test_results_as_a_scalar(self):
        fixture = Path(__file__).parent / "fixtures" / "IC222A-working-storage.cbl"
        data_source = fixture.read_text(encoding="utf-8").split("025600 PROCEDURE DIVISION.")[0]
        procedure = "\n".join([
            "025600 PROCEDURE DIVISION.",
            "025700 CCVS1 SECTION.",
            "025800 OPEN-FILES.",
            "025900 MOVE CCVS-PGM-ID TO TEST-ID. MOVE CCVS-PGM-ID TO ID-AGAIN.",
            "026000 MOVE SPACE TO TEST-RESULTS.",
            "026100 GO TO CCVS1-EXIT.",
            "026200 PASS.",
            '026300 MOVE "PASS " TO P-OR-F.',
            "026400 PRINT-DETAIL.",
            "026500 MOVE TEST-RESULTS TO PRINT-REC. PERFORM WRITE-LINE.",
            "026600 MOVE SPACE TO P-OR-F. MOVE SPACE TO COMPUTED-X.",
            "026700 CCVS1-EXIT.",
            "026800 STOP RUN.",
        ])
        source = data_source + procedure
        program = cobol2py.parse_cobol(source, source_format="auto")
        generated = cobol2py.emit_python(program)
        scalar_assignments = [
            line for line in generated.splitlines()
            if line.lstrip().startswith("test_results =")
        ]
        self.assertEqual(scalar_assignments, [])


class GroupToGroupMoveRegressionTests(unittest.TestCase):
    def test_move_group_to_occurs_record_preserves_target_record_shape(self):
        from contextlib import redirect_stdout
        from io import StringIO

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. GROUPCOPY.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 ROOT-AREA.",
            "   03 SKELETON.",
            "      05 FILLER PIC X(3) VALUE",
            '         "ABC".',
            "      05 FILLER PIC X(3) VALUE",
            '         "DEF".',
            "   03 TABLE-AREA OCCURS 2 TIMES.",
            "      05 FIELD-ONE PIC X(3).",
            "      05 FIELD-TWO PIC X(3).",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "   MOVE SKELETON TO TABLE-AREA(1).",
            '   MOVE "XYZ" TO FIELD-ONE(1).',
            "   DISPLAY FIELD-ONE(1).",
            "   DISPLAY FIELD-TWO(1).",
            "   STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<group-to-group-move>", "exec"), namespace)
        output = StringIO()
        try:
            with redirect_stdout(output):
                namespace["main"]()
        except Exception as error:
            self.fail(f"{error}\nGenerated Python:\n{generated}")
        self.assertEqual(output.getvalue(), "XYZ\nDEF\n")


class ElementaryOccursMoveRegressionTests(unittest.TestCase):
    def test_move_space_to_whole_alphanumeric_table_fills_each_occurrence(self):
        variables = {
            "WS-RESULTS": cobol2py.CobolVar(
                level=1, name="WS-RESULTS", pic="X", is_array=True, occurs=3
            )
        }
        translated = cobol2py.translate_move_value("SPACE", "WS-RESULTS", variables)
        self.assertEqual(translated, "[' '] * 3")
        compile(translated, "<move-space-table>", "eval")
        self.assertEqual(eval(translated), [" ", " ", " "])

    def test_move_space_to_one_table_occurrence_stays_scalar(self):
        variables = {
            "WS-RESULTS": cobol2py.CobolVar(
                level=1, name="WS-RESULTS", pic="X", is_array=True, occurs=3
            )
        }
        self.assertEqual(
            cobol2py.translate_move_value("SPACE", "WS-RESULTS(2)", variables),
            "' '",
        )


class InitializeOccursGroupRegressionTests(unittest.TestCase):
    def setUp(self):
        self.variables = {
            item.name: item
            for item in cobol2py.parse_variables([
                (1, "01 WS-ROWS OCCURS 2 TIMES."),
                (2, "05 WS-CODE PIC X(3) VALUE 'ABC'."),
                (2, "05 WS-COUNT PIC 9(2) VALUE 12."),
            ])
        }

    def test_initialize_occurs_group_resets_every_row_and_child(self):
        translated = cobol2py.translate_statement("INITIALIZE WS-ROWS", set(), self.variables)
        self.assertEqual(translated, [
            "ws_rows[0]['ws_code'] = '   '",
            "ws_rows[0]['ws_count'] = 0",
            "ws_rows[1]['ws_code'] = '   '",
            "ws_rows[1]['ws_count'] = 0",
        ])
        compile("\n".join(translated), "<initialize-occurs-group>", "exec")

    def test_initialize_one_occurs_group_resets_only_selected_row(self):
        translated = cobol2py.translate_statement("INITIALIZE WS-ROWS(2)", set(), self.variables)
        self.assertEqual(translated, [
            "ws_rows[1]['ws_code'] = '   '",
            "ws_rows[1]['ws_count'] = 0",
        ])
        compile("\n".join(translated), "<initialize-one-occurs-group>", "exec")


class FillerStorageRegressionTests(unittest.TestCase):
    def test_repeated_filler_items_get_distinct_storage_keys(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. FILLERTEST.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-REC.",
            '05 FILLER PIC X(2) VALUE "AB".',
            "05 WS-TABLE OCCURS 2 TIMES.",
            '10 FILLER PIC X(3) VALUE "XYZ".',
            "PROCEDURE DIVISION.",
            "MAIN.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        filler_items = [item for item in program.variables if item.name.startswith("FILLER-")]
        self.assertEqual(len(filler_items), 2)
        self.assertEqual(len({item.name for item in filler_items}), 2)

        generated = cobol2py.emit_python(program)
        for item in filler_items:
            self.assertIn(repr(cobol2py.normalize_name(item.name)), generated)
        compile(generated, "<filler-storage>", "exec")


class AlternateStorageSectionRegressionTests(unittest.TestCase):
    def test_local_storage_only_program_emits_its_variables(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. LOCALONLY.",
            "DATA DIVISION.",
            "LOCAL-STORAGE SECTION.",
            "01 LS-COUNT PIC 9 VALUE 7.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "DISPLAY LS-COUNT.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        self.assertIn("LS-COUNT", {item.name for item in program.variables})
        generated = cobol2py.emit_python(program)
        self.assertIn("ls_count: int = 7", generated)
        compile(generated, "<local-storage-only>", "exec")

    def test_linkage_only_program_parses_linkage_variables(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. LINKONLY.",
            "DATA DIVISION.",
            "LINKAGE SECTION.",
            "01 LK-COUNT PIC 9.",
            "PROCEDURE DIVISION USING LK-COUNT.",
            "MAIN.",
            "DISPLAY LK-COUNT.",
            "GOBACK.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        self.assertIn("LK-COUNT", {item.name for item in program.variables})
        compile(cobol2py.emit_python(program), "<linkage-only>", "exec")


class AnnuityIntrinsicRegressionTests(unittest.TestCase):
    def test_annuity_intrinsic_generates_valid_formula(self):
        translated = cobol2py.translate_expr("FUNCTION ANNUITY(0.05, 10)")
        compile(translated, "<annuity-intrinsic>", "eval")
        self.assertAlmostEqual(eval(translated, {}), 0.05 / (1.0 - (1.05 ** -10)))

    def test_annuity_intrinsic_handles_zero_rate(self):
        translated = cobol2py.translate_expr("FUNCTION ANNUITY(0, 10)")
        compile(translated, "<annuity-zero-rate>", "eval")
        self.assertAlmostEqual(eval(translated, {}), 0.1)


class TestNumvalIntrinsicRegressionTests(unittest.TestCase):
    def test_test_numval_returns_zero_for_numeric_text(self):
        translated = cobol2py.translate_expr("FUNCTION TEST-NUMVAL('123.45')")
        compile(translated, "<test-numval-valid>", "eval")
        self.assertEqual(eval(translated, {}), 0)

    def test_test_numval_returns_first_invalid_character_position(self):
        translated = cobol2py.translate_expr("FUNCTION TEST-NUMVAL('12X45')")
        compile(translated, "<test-numval-invalid>", "eval")
        self.assertEqual(eval(translated, {}), 3)


class NestedQualifiedOccursSubscriptRegressionTests(unittest.TestCase):
    def test_nested_group_fields_are_resolved_when_used_as_table_subscripts(self):
        variables = {
            "GRP-TABLE1": cobol2py.CobolVar(
                level=1, name="GRP-TABLE1", is_group=True
            ),
            "ELEM1": cobol2py.CobolVar(
                level=2, name="ELEM1", pic="S999", is_array=True, occurs=100,
                parent_name="GRP-TABLE1",
            ),
            "GRP-SUB": cobol2py.CobolVar(
                level=1, name="GRP-SUB", is_group=True
            ),
            "S1": cobol2py.CobolVar(
                level=2, name="S1", pic="S999", parent_name="GRP-SUB"
            ),
        }

        translated = cobol2py.normalize_data_reference("ELEM1(S1)", variables)

        self.assertEqual(
            translated,
            "grp_table1['elem1'][int(grp_sub['s1']) - 1]",
        )
        compile(translated, "<nested-group-subscript>", "eval")

    def test_nested_group_fields_resolve_all_dimensions_of_table_subscripts(self):
        variables = {
            "GRP-TABLE2": cobol2py.CobolVar(
                level=1, name="GRP-TABLE2", is_group=True
            ),
            "GROUP1": cobol2py.CobolVar(
                level=2, name="GROUP1", is_group=True, is_array=True, occurs=10,
                parent_name="GRP-TABLE2",
            ),
            "ELEM2": cobol2py.CobolVar(
                level=3, name="ELEM2", pic="S999", is_array=True, occurs=10,
                parent_name="GROUP1",
            ),
            "GRP-SUB": cobol2py.CobolVar(
                level=1, name="GRP-SUB", is_group=True
            ),
            "S21": cobol2py.CobolVar(
                level=2, name="S21", pic="S999", parent_name="GRP-SUB"
            ),
            "S22": cobol2py.CobolVar(
                level=2, name="S22", pic="S999", parent_name="GRP-SUB"
            ),
        }

        translated = cobol2py.normalize_data_reference("ELEM2(S21 S22)", variables)

        self.assertEqual(
            translated,
            "grp_table2['group1'][int(grp_sub['s21']) - 1]['elem2'][int(grp_sub['s22']) - 1]",
        )
        compile(translated, "<nested-group-multidimensional-subscript>", "eval")

    def test_each_qualified_occurs_level_keeps_its_own_subscript(self):
        variables = {
            "PARENT-TABLE": cobol2py.CobolVar(
                level=1, name="PARENT-TABLE", is_group=True, is_array=True, occurs=4
            ),
            "CHILD-TABLE": cobol2py.CobolVar(
                level=5, name="CHILD-TABLE", is_group=True, is_array=True,
                occurs=5, parent_name="PARENT-TABLE",
            ),
            "FIELD": cobol2py.CobolVar(
                level=10, name="FIELD", pic="X", parent_name="CHILD-TABLE"
            ),
        }
        translated = cobol2py.normalize_data_reference(
            "FIELD OF CHILD-TABLE(2) OF PARENT-TABLE(3)", variables
        )
        self.assertEqual(
            translated,
            "parent_table[2]['child_table'][1]['field']",
        )
        compile(translated, "<nested-qualified-occurs>", "eval")


class QualifiedParentSubscriptRegressionTests(unittest.TestCase):
    def test_qualified_child_uses_subscript_on_parent_table(self):
        variables = {
            "TABLE": cobol2py.CobolVar(
                level=1, name="TABLE", is_group=True, is_array=True, occurs=2
            ),
            "PARAM": cobol2py.CobolVar(
                level=5, name="PARAM", pic="X", parent_name="TABLE"
            ),
        }
        expected = "table[1]['param']"
        self.assertEqual(
            cobol2py.normalize_data_reference("PARAM OF TABLE(2)", variables),
            expected,
        )
        self.assertEqual(cobol2py.translate_expr("PARAM OF TABLE(2)", variables), expected)

    def test_qualified_parent_subscript_expression_compiles(self):
        translated = cobol2py.translate_expr("PARAM OF TABLE(INDEX)")
        compile(translated, "<qualified-parent-subscript>", "eval")
        self.assertEqual(translated, "table[int(index) - 1]['param']")


class SearchAllNextSentenceRegressionTests(unittest.TestCase):
    def test_next_sentence_is_not_part_of_search_key_expression(self):
        variables = {
            "WS-TABLE": cobol2py.CobolVar(
                level=1, name="WS-TABLE", is_group=True, is_array=True, occurs=3,
                ascending_key="WS-KEY", indexed_by="WS-IDX",
            ),
            "WS-KEY": cobol2py.CobolVar(
                level=5, name="WS-KEY", pic="X", parent_name="WS-TABLE"
            ),
        }
        node = cobol2py.Node(
            kind="search_all",
            text="SEARCH ALL WS-TABLE",
            line=10,
            body=[
                cobol2py.Node(
                    kind="when",
                    text="WS-KEY(WS-IDX) = WS-TARGET NEXT SENTENCE",
                    line=11,
                )
            ],
        )
        generated = "\n".join(cobol2py.translate_nodes([node], set(), 0, variables))
        compile(generated, "<search-all-next-sentence>", "exec")
        self.assertIn("== ws_target", generated)
        self.assertNotIn("next sentence", generated.lower())


class OrdinalIntrinsicRegressionTests(unittest.TestCase):
    def test_ord_min_returns_one_based_position_of_first_minimum(self):
        translated = cobol2py.translate_expr("FUNCTION ORD-MIN(4, 2, 1, 7, 2, 0)")
        self.assertEqual(eval(translated), 6)
        compile(translated, "<ord-min>", "eval")

    def test_ord_max_returns_one_based_position_of_first_maximum(self):
        translated = cobol2py.translate_expr("FUNCTION ORD-MAX(4, 2, 7, 7, 2)")
        self.assertEqual(eval(translated), 3)
        compile(translated, "<ord-max>", "eval")

class ScreenSectionParsingRegressionTests(unittest.TestCase):
    def test_screen_section_items_are_parsed_without_leaking_hierarchy(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. SCREENDECL.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-COUNT PIC 9 VALUE 1.",
            "SCREEN SECTION.",
            "01 MENU-SCREEN.",
            '   05 MENU-OPTION PIC X(1) VALUE "Y".',
            "PROCEDURE DIVISION.",
            "DISPLAY MENU-OPTION.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        variables = {item.name: item for item in program.variables}
        self.assertIn("WS-COUNT", variables)
        self.assertIn("MENU-SCREEN", variables)
        self.assertIn("MENU-OPTION", variables)
        self.assertEqual(variables["MENU-OPTION"].parent_name, "MENU-SCREEN")
        generated = cobol2py.emit_python(program)
        compile(generated, "<screen-section>", "exec")


class DebugNameSpecialRegisterRegressionTests(unittest.TestCase):
    def test_referenced_debug_name_is_added_as_implicit_storage(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. DEBUGNAME.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "PROCEDURE DIVISION.",
            "DISPLAY DEBUG-NAME.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        variables = {item.name: item for item in program.variables}
        self.assertIn("DEBUG-NAME", variables)
        self.assertEqual(variables["DEBUG-NAME"].pic, "X(30)")
        generated = cobol2py.emit_python(program)
        compile(generated, "<debug-name-special-register>", "exec")


class ExternalBenchmarkConditionRegressionTests(unittest.TestCase):
    def test_multiple_abbreviated_relations_remain_valid_python(self):
        variables = {
            "WS-YEAR": cobol2py.CobolVar(level=77, name="WS-YEAR", pic="9(4)"),
            "WS-MONTH": cobol2py.CobolVar(level=77, name="WS-MONTH", pic="99"),
            "WS-DAY": cobol2py.CobolVar(level=77, name="WS-DAY", pic="99"),
        }
        condition = (
            "WS-YEAR >= 1990 AND <= 9999 AND "
            "WS-MONTH >= 1 AND <= 12 AND WS-DAY >= 1 AND <= 31"
        )
        translated = cobol2py.translate_condition(condition, variables)
        ast.parse(translated, mode="eval")
        self.assertIn("ws_year >= 1990", translated)
        self.assertIn("ws_year <= 9999", translated)
        self.assertIn("ws_month <= 12", translated)
        self.assertIn("ws_day <= 31", translated)

    def test_abbreviated_string_alternatives_keep_all_values(self):
        variables = {
            "WS-FLAG": cobol2py.CobolVar(level=77, name="WS-FLAG", pic="X(1)")
        }
        translated = cobol2py.translate_condition(
            'WS-FLAG = "A" OR "B" OR "C"', variables
        )
        ast.parse(translated, mode="eval")
        namespace = {"ws_flag": "C"}
        self.assertTrue(eval(translated, namespace))
        self.assertIn("'B'", translated)
        self.assertIn("'C'", translated)

    def test_four_abbreviated_string_alternatives_keep_every_value(self):
        variables = {
            "WS-FLAG": cobol2py.CobolVar(level=77, name="WS-FLAG", pic="X(1)")
        }
        translated = cobol2py.translate_condition(
            'WS-FLAG = "A" OR "B" OR "C" OR "D"', variables
        )
        ast.parse(translated, mode="eval")
        for value in ("A", "B", "C", "D"):
            with self.subTest(value=value):
                self.assertTrue(eval(translated, {"ws_flag": value}))
        self.assertFalse(eval(translated, {"ws_flag": "Z"}))

    def test_abbreviated_negated_string_alternatives_remain_valid_python(self):
        variables = {
            "WS-OPCAO": cobol2py.CobolVar(level=77, name="WS-OPCAO", pic="X(1)")
        }
        translated = cobol2py.translate_condition(
            'WS-OPCAO NOT = "N" AND "S"', variables
        )
        ast.parse(translated, mode="eval")
        self.assertTrue(eval(translated, {"ws_opcao": "A"}))
        self.assertFalse(eval(translated, {"ws_opcao": "N"}))
        self.assertFalse(eval(translated, {"ws_opcao": "S"}))


class MultipleIndexedNamesCandidateTests(unittest.TestCase):
    def test_legacy_indexed_clause_collects_every_name(self):
        variables = cobol2py.parse_variables([
            (1, "01 WS-TABLE OCCURS 50 INDEXED IDX-1 IDX-2 IDX-3 IDX-4.")
        ])
        self.assertEqual(variables[0].indexed_by, "IDX-1")
        self.assertEqual(
            variables[0].indexed_by_names,
            ["IDX-1", "IDX-2", "IDX-3", "IDX-4"],
        )

    def test_by_spelling_and_clause_continuation_keep_all_indexes(self):
        variables = cobol2py.parse_variables([
            (1, "01 WS-TABLE OCCURS 10 INDEXED BY IDX-A IDX-B"),
            (2, "   ASCENDING KEY IS WS-KEY."),
        ])
        self.assertEqual(variables[0].indexed_by_names, ["IDX-A", "IDX-B"])
        program = cobol2py.Program(variables=variables)
        generated = cobol2py.emit_python(program)
        self.assertIn("idx_a = 1", generated)
        self.assertIn("idx_b = 1", generated)
        compile(generated, "<multiple-indexed-names>", "exec")

    def test_abbreviated_negated_relation_repeats_operator(self):
        variables = {
            "WS-OPCAO": cobol2py.CobolVar(level=77, name="WS-OPCAO", pic="X(1)")
        }
        translated = cobol2py.translate_condition(
            'WS-OPCAO NOT = "N" AND NOT = "S"', variables
        )
        ast.parse(translated, mode="eval")
        self.assertTrue(eval(translated, {"ws_opcao": "A"}))
        self.assertFalse(eval(translated, {"ws_opcao": "N"}))
        self.assertFalse(eval(translated, {"ws_opcao": "S"}))


class DebugContentsSpecialRegisterCandidateTests(unittest.TestCase):
    def test_debug_contents_is_added_as_implicit_storage(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. DEBUGCONTENTS.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "PROCEDURE DIVISION.",
            "DISPLAY DEBUG-CONTENTS.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        variables = {item.name: item for item in program.variables}
        self.assertIn("DEBUG-CONTENTS", variables)
        self.assertEqual(variables["DEBUG-CONTENTS"].pic, "X(10)")
        generated = cobol2py.emit_python(program)
        self.assertIn("debug_contents", generated)
        compile(generated, "<debug-contents-register>", "exec")
