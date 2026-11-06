import unittest

import cobol2py


class DivideVerbCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.variables = {
            name: cobol2py.CobolVar(level=1, name=name, pic="9(9)")
            for name in ("WS-NUM1", "WS-NUM2", "WS-NUM3", "WS-NUM4", "WS-NUMB", "WS-NUMC", "WS-NUMT", "WS-RES1")
        }

    def run_statement(self, statement, values):
        translated = cobol2py.translate_statement(statement, set(), self.variables)
        self.assertIsNotNone(translated)
        namespace = {name.lower().replace("-", "_"): value for name, value in values.items()}
        exec("\n".join(translated or []), namespace)
        return namespace

    def test_divide_into_multiple_receivers(self):
        ns = self.run_statement(
            "DIVIDE WS-NUM1 INTO WS-NUM2 WS-NUM4",
            {"WS-NUM1": 5, "WS-NUM2": 2208, "WS-NUM4": 911},
        )
        self.assertEqual(ns["ws_num2"], 441)
        self.assertEqual(ns["ws_num4"], 182)

    def test_divide_into_snapshots_divisor_when_it_is_also_receiver(self):
        ns = self.run_statement(
            "DIVIDE WS-NUM2 INTO WS-NUM2 WS-NUM3 WS-NUM4",
            {"WS-NUM2": 2208, "WS-NUM3": 3007, "WS-NUM4": 911},
        )
        self.assertEqual(ns["ws_num2"], 1)
        self.assertEqual(ns["ws_num3"], 1)
        self.assertEqual(ns["ws_num4"], 0)

    def test_divide_by_giving_remainder(self):
        ns = self.run_statement(
            "DIVIDE WS-NUMC BY WS-NUMB GIVING WS-NUMT REMAINDER WS-RES1",
            {"WS-NUMC": 17, "WS-NUMB": 5, "WS-NUMT": 0, "WS-RES1": 0},
        )
        self.assertEqual(ns["ws_numt"], 3)
        self.assertEqual(ns["ws_res1"], 2)

    def test_divide_into_giving_remainder(self):
        ns = self.run_statement(
            "DIVIDE WS-NUMB INTO WS-NUMC GIVING WS-NUMT REMAINDER WS-RES1",
            {"WS-NUMC": 17, "WS-NUMB": 5, "WS-NUMT": 0, "WS-RES1": 0},
        )
        self.assertEqual(ns["ws_numt"], 3)
        self.assertEqual(ns["ws_res1"], 2)



    def test_divide_into_giving_accepts_decimal_literal_dividend(self):
        ns = self.run_statement(
            "DIVIDE WS-NUM1 INTO 864.36 GIVING WS-NUMT",
            {"WS-NUM1": 44.1, "WS-NUMT": 0},
        )
        self.assertEqual(ns["ws_numt"], 19)

    def test_divide_into_giving_accepts_integer_literal_dividend_and_remainder(self):
        ns = self.run_statement(
            "DIVIDE WS-NUM1 INTO 100 GIVING WS-NUMT REMAINDER WS-RES1",
            {"WS-NUM1": 22, "WS-NUMT": 0, "WS-RES1": 0},
        )
        self.assertEqual(ns["ws_numt"], 4)
        self.assertEqual(ns["ws_res1"], 12)

if __name__ == "__main__":
    unittest.main()