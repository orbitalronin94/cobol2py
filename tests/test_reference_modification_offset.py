"""Regression coverage for arithmetic COBOL reference-modification offsets."""
import unittest

import cobol2py


class ArithmeticReferenceModificationOffsetTests(unittest.TestCase):
    def test_arithmetic_offset_is_translated_as_an_expression(self):
        translated = cobol2py.translate_expr("WS-TEXT(WS-START + WS-OFFSET * 2:2)")
        compile(translated, "<arithmetic-reference-offset>", "eval")
        self.assertEqual(
            eval(translated, {}, {"ws_text": "ABCDEFG", "ws_start": 1, "ws_offset": 1}),
            "CD",
        )


if __name__ == "__main__":
    unittest.main()
