import unittest

import cobol2py


class DataLevelTests(unittest.TestCase):
    def test_level_77_is_standalone_not_nested_under_previous_group(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. LEVEL77.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-GROUP.",
            "05 WS-CHILD PIC X.",
            "77 WS-COUNT PIC 9(3) VALUE 7.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "STOP RUN.",
        ])
        program = cobol2py.parse_cobol(source, source_format="free")
        variable = next(item for item in program.variables if item.name == "WS-COUNT")
        self.assertEqual(variable.level, 77)
        self.assertIsNone(variable.parent_name)
        self.assertFalse(variable.is_group)
        self.assertEqual(variable.value, "7")


if __name__ == "__main__":
    unittest.main()
