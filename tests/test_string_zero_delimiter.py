import unittest

import cobol2py


class StringZeroDelimiterTests(unittest.TestCase):
    def test_string_delimited_by_zeroes_stops_at_character_zero(self):
        variables = {
            "WS-SOURCE": cobol2py.CobolVar(level=1, name="WS-SOURCE", pic="X(8)"),
            "WS-DEST": cobol2py.CobolVar(level=1, name="WS-DEST", pic="X(8)"),
        }
        lines = cobol2py.translate_statement(
            "STRING WS-SOURCE DELIMITED BY ZEROES INTO WS-DEST",
            set(),
            variables,
        )
        namespace = {"ws_source": "A0B     ", "ws_dest": "        "}
        exec("\n".join(lines or []), namespace)
        self.assertEqual(namespace["ws_dest"], "A       ")


if __name__ == "__main__":
    unittest.main()
