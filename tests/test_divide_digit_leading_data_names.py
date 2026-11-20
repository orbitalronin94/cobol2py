import unittest
from contextlib import redirect_stdout
from io import StringIO

import cobol2py


class DivideIntoDigitLeadingDataNameRegressionTests(unittest.TestCase):
    def test_numeric_leading_names_are_valid_giving_and_remainder_targets(self):
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. DIVLIT.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 25COUNT PIC 999 VALUE 3.
01 25ANS PIC 99 VALUE ZERO.
01 25REM PIC 99 VALUE ZERO.
PROCEDURE DIVISION.
MAIN.
    DIVIDE 25COUNT INTO 100 GIVING 25ANS REMAINDER 25REM.
    DISPLAY 25ANS.
    DISPLAY 25REM.
    STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.emit_python(program)
        compile(generated, "<divide-digit-leading-data-name>", "exec")
        namespace = {"__name__": "generated_test"}
        exec(generated, namespace)
        output = StringIO()
        with redirect_stdout(output):
            namespace["main"]()
        self.assertEqual(output.getvalue(), "33\n01\n", generated)


if __name__ == "__main__":
    unittest.main()
