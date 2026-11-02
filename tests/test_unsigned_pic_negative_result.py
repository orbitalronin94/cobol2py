import unittest

import cobol2py


class UnsignedPicNegativeResultTests(unittest.TestCase):
    def test_negative_arithmetic_result_preserves_magnitude_for_unsigned_pic(self):
        target = cobol2py.CobolVar(level=1, name="WS-NUM4", pic="9(9)")
        expression = cobol2py.fit_numeric_expression(
            "-2737164", "WS-NUM4", {"WS-NUM4": target}
        )
        self.assertEqual(eval(expression, {}), 2737164)


if __name__ == "__main__":
    unittest.main()