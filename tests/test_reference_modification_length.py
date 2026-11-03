"""Regression coverage for arithmetic COBOL reference-modification lengths."""
import unittest

import cobol2py


class ArithmeticReferenceModificationLengthTests(unittest.TestCase):
    def test_arithmetic_length_is_translated_as_an_expression(self):
        translated = cobol2py.translate_expr("WS-TEXT(1:WS-LENGTH + WS-EXTRA * 2)")
        compile(translated, "<arithmetic-reference-length>", "eval")
        self.assertEqual(
            eval(translated, {}, {"ws_text": "ABCDEFG", "ws_length": 1, "ws_extra": 1}),
            "ABC",
        )


if __name__ == "__main__":
    unittest.main()
