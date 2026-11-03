import unittest

import cobol2py


class ExitSectionTests(unittest.TestCase):
    def test_exit_section_emits_return(self):
        self.assertEqual(cobol2py.translate_statement("EXIT SECTION", set()), ["return"])


if __name__ == "__main__":
    unittest.main()
