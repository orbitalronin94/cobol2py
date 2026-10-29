"""Smoke tests for the experimental C/Rust backend prototypes."""
import unittest

import cobol2native


SOURCE = """IDENTIFICATION DIVISION.
PROGRAM-ID. NATIVE-DEMO.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-NAME PIC X(3) VALUE "HI".
01 WS-COUNT PIC 9(2) VALUE 1.
PROCEDURE DIVISION.
MAIN.
DISPLAY WS-NAME.
ADD 1 TO WS-COUNT.
STOP RUN.
"""


class NativeBackendTests(unittest.TestCase):
    def test_c_backend_emits_c_and_preserves_pic_width(self):
        import cobol2py
        program = cobol2py.parse_cobol(SOURCE, source_format="free")
        output = cobol2native.emit_native(program, "c")
        self.assertIn("#include <stdio.h>", output)
        self.assertIn("char ws_name[4]", output)
        self.assertIn('printf("%s\\n", ws_name);', output)
        self.assertIn("ws_count += 1;", output)

    def test_rust_backend_emits_rust(self):
        import cobol2py
        program = cobol2py.parse_cobol(SOURCE, source_format="free")
        output = cobol2native.emit_native(program, "rust")
        self.assertIn("fn main()", output)
        self.assertIn('let mut ws_name: String = "HI ".to_string();', output)
        self.assertIn('print!("{}\\n", ws_name);', output)
        self.assertIn("ws_count += 1;", output)


    def test_c_numeric_display_literals_use_matching_varargs_types(self):
        import cobol2py
        source = SOURCE.replace('DISPLAY WS-NAME.', 'DISPLAY 123 1.5.')
        program = cobol2py.parse_cobol(source, source_format="free")
        output = cobol2native.emit_native(program, "c")
        self.assertIn('printf("%lld%g\\n", (long long)(123), (double)(1.5));', output)

    def test_if_control_flow_is_emitted_for_c_and_rust(self):
        import cobol2py
        source = SOURCE.replace(
            "ADD 1 TO WS-COUNT.",
            'IF WS-COUNT = 1 DISPLAY "YES" ELSE DISPLAY "NO" END-IF.',
        )
        program = cobol2py.parse_cobol(source, source_format="free")
        c_output = cobol2native.emit_native(program, "c")
        rust_output = cobol2native.emit_native(program, "rust")
        self.assertIn("if ((ws_count == 1)) {", c_output)
        self.assertIn('printf("%s\\n", "YES");', c_output)
        self.assertIn("} else {", c_output)
        self.assertIn("if (ws_count == 1) {", rust_output)
        self.assertIn('print!("{}\\n", "YES");', rust_output)
        self.assertIn("} else {", rust_output)


if __name__ == "__main__":
    unittest.main()
