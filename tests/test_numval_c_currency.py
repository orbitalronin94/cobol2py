import unittest

import cobol2py


class NumvalCCurrencyOperandTests(unittest.TestCase):
    def test_optional_currency_operand_is_translated_and_supported(self):
        translated = cobol2py.translate_expr('FUNCTION NUMVAL-C(WS-AMOUNT, "$" )')
        self.assertEqual(translated, "_cobol_numval_c(ws_amount, '$')")
        compile(translated, "<numval-c-currency>", "eval")

        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. NUMVALCURRENCYTEST.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "    STOP RUN.",
        ])
        generated = cobol2py.emit_python(cobol2py.parse_cobol(source, source_format="free"))
        namespace = {"__name__": "not_main"}
        exec(compile(generated, "<numval-c-runtime>", "exec"), namespace)
        convert = namespace["_cobol_numval_c"]
        self.assertAlmostEqual(convert("$1,234.56", "$"), 1234.56)
        self.assertAlmostEqual(convert("£98.25", "£"), 98.25)


if __name__ == "__main__":
    unittest.main()