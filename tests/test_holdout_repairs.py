"""Regression tests for defects isolated by the 500-case GnuCOBOL holdout."""
import ast
import unittest

import cobol2py


class HoldoutRepairRegressionTests(unittest.TestCase):
    def test_exp10_intrinsic_emits_valid_python(self):
        translated = cobol2py.translate_expr("FUNCTION EXP10(-2)")
        ast.parse(translated, mode="eval")
        self.assertAlmostEqual(eval(translated, {"__builtins__": {}}), 0.01)

    def test_evaluate_numeric_class_test_is_boolean(self):
        node = cobol2py.Node(
            kind="evaluate",
            text="EVALUATE WS-X NUMERIC",
            line=1,
            body=[
                cobol2py.Node(
                    kind="when",
                    text="TRUE",
                    line=2,
                    then_branch=[cobol2py.Node(kind="stmt", text="CONTINUE", line=3)],
                )
            ],
        )
        lines = cobol2py.translate_nodes([node], set(), indent=0)
        generated = "\n".join(lines)
        ast.parse(generated)
        self.assertIn("str(ws_x).strip().isdigit()", generated)

    def test_evaluate_not_numeric_inverts_class_test(self):
        node = cobol2py.Node(
            kind="evaluate",
            text="EVALUATE WS-X NOT NUMERIC",
            line=1,
            body=[
                cobol2py.Node(
                    kind="when",
                    text="TRUE",
                    line=2,
                    then_branch=[cobol2py.Node(kind="stmt", text="CONTINUE", line=3)],
                )
            ],
        )
        generated = "\n".join(cobol2py.translate_nodes([node], set(), indent=0))
        ast.parse(generated)
        self.assertIn("not (str(ws_x).strip().isdigit())", generated)

    def test_divide_into_literal_with_giving_does_not_assign_to_literal(self):
        lines = cobol2py.translate_statement(
            "DIVIDE 25COUNT INTO 100 GIVING RESULT REMAINDER REM",
            set(),
        )
        generated = "\n".join(lines or [])
        self.assertIn("_cobol_divide_dividend = 100", generated)
        self.assertIn("result =", generated)
        self.assertNotIn("100 =", generated)
        ast.parse(generated)

    def test_legacy_whitespace_subscripts_preserve_three_dimensions(self):
        self.assertEqual(
            cobol2py.split_cobol_subscripts("3 1 INDEX3 - 1"),
            ["3", "1", "INDEX3 - 1"],
        )

    def test_legacy_whitespace_subscripts_keep_arithmetic_with_its_index(self):
        self.assertEqual(
            cobol2py.split_cobol_subscripts("INDEX1 + 1 INDEX2 + 3"),
            ["INDEX1 + 1", "INDEX2 + 3"],
        )

    def test_legacy_whitespace_subscripts_keep_signed_literals(self):
        self.assertEqual(
            cobol2py.split_cobol_subscripts("+2 INDEX2 - 2 4"),
            ["+2", "INDEX2 - 2", "4"],
        )

    def test_numeric_literal_is_not_a_receiving_data_reference(self):
        self.assertIsNone(__import__("re").fullmatch(cobol2py.DATA_REF_PATTERN, "100.50"))

    def test_divide_numeric_literal_into_giving_does_not_emit_literal_assignment(self):
        lines = cobol2py.translate_statement(
            "DIVIDE 1.0051 INTO 100.50 GIVING DIV8 ROUNDED",
            set(),
        )
        generated = "\n".join(lines or [])
        self.assertNotIn("100.50 =", generated)
        self.assertIn("0.5 if", generated)
        ast.parse(generated)

    def test_set_multiple_index_names(self):
        lines = cobol2py.translate_statement("SET IDX1 IDX2 IDX3 TO 001", set())
        self.assertEqual(lines, ["idx1 = 1", "idx2 = 1", "idx3 = 1"])


if __name__ == "__main__":
    unittest.main()
