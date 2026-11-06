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

    def test_set_multiple_index_names(self):
        lines = cobol2py.translate_statement("SET IDX1 IDX2 IDX3 TO 001", set())
        self.assertEqual(lines, ["idx1 = 1", "idx2 = 1", "idx3 = 1"])


if __name__ == "__main__":
    unittest.main()
