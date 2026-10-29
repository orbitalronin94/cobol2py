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


    def test_scalar_group_fields_are_flattened_for_c_and_rust(self):
        import cobol2py
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. GROUP-DEMO.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-RECORD.
   05 WS-NAME PIC X(3) VALUE "HI".
   05 WS-COUNT PIC 9(2) VALUE 1.
PROCEDURE DIVISION.
MAIN.
DISPLAY WS-NAME.
ADD 1 TO WS-COUNT.
STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        c_output = cobol2native.emit_native(program, "c")
        rust_output = cobol2native.emit_native(program, "rust")
        self.assertIn("char ws_record_ws_name[4]", c_output)
        self.assertIn("long long ws_record_ws_count = 1;", c_output)
        self.assertIn('printf("%s\\n", ws_record_ws_name);', c_output)
        self.assertIn("ws_record_ws_count += 1;", c_output)
        self.assertIn("let mut ws_record_ws_name: String", rust_output)
        self.assertIn("ws_record_ws_count += 1;", rust_output)

    def test_c_numeric_display_literals_use_matching_varargs_types(self):
        import cobol2py
        source = SOURCE.replace('DISPLAY WS-NAME.', 'DISPLAY 123 1.5.')
        program = cobol2py.parse_cobol(source, source_format="free")
        output = cobol2native.emit_native(program, "c")
        self.assertIn('printf("%lld%g\\n", (long long)(123), (double)(1.5));', output)

    def test_perform_until_and_varying_are_emitted_for_c_and_rust(self):
        import cobol2py
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. PERFORM-UNTIL-DEMO.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-IDX PIC 9 VALUE 0.
01 WS-COUNT PIC 9 VALUE 0.
PROCEDURE DIVISION.
MAIN.
PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > 3
ADD 1 TO WS-COUNT
END-PERFORM.
PERFORM UNTIL WS-COUNT >= 5
ADD 1 TO WS-COUNT
END-PERFORM.
STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        c_output = cobol2native.emit_native(program, "c")
        rust_output = cobol2native.emit_native(program, "rust")
        self.assertIn("while (!((ws_idx > 3))) {", c_output)
        self.assertIn("ws_idx += 1;", c_output)
        self.assertIn("while (!(ws_count >= 5)) {", c_output)
        self.assertIn("while !((ws_idx > 3)) {", rust_output)
        self.assertIn("ws_idx += 1;", rust_output)
        self.assertIn("while !(ws_count >= 5) {", rust_output)

    def test_perform_times_inline_is_emitted_for_c_and_rust(self):
        import cobol2py
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. PERFORM-DEMO.
PROCEDURE DIVISION.
MAIN.
PERFORM 3 TIMES
DISPLAY "X"
END-PERFORM.
STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        c_output = cobol2native.emit_native(program, "c")
        rust_output = cobol2native.emit_native(program, "rust")
        self.assertIn("for (int _cobol_perform_", c_output)
        self.assertIn("< 3;", c_output)
        self.assertIn('printf("%s\\n", "X");', c_output)
        self.assertIn("in 0..3 {", rust_output)
        self.assertIn('print!("{}\\n", "X");', rust_output)

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


    def test_add_multiple_operands_and_move_multiple_targets(self):
        import cobol2py
        source = """IDENTIFICATION DIVISION.
PROGRAM-ID. MULTI-OPERAND-DEMO.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-A PIC 9 VALUE 1.
01 WS-B PIC 9 VALUE 2.
01 WS-C PIC 9 VALUE 0.
01 WS-D PIC 9 VALUE 0.
01 WS-TEXT-A PIC X(4) VALUE SPACES.
01 WS-TEXT-B PIC X(4) VALUE SPACES.
PROCEDURE DIVISION.
MAIN.
ADD WS-A WS-B TO WS-C.
MOVE 7 TO WS-C WS-D.
MOVE "OK" TO WS-TEXT-A WS-TEXT-B.
DISPLAY WS-C WS-D WS-TEXT-A WS-TEXT-B.
STOP RUN.
"""
        program = cobol2py.parse_cobol(source, source_format="free")
        c_output = cobol2native.emit_native(program, "c")
        rust_output = cobol2native.emit_native(program, "rust")
        self.assertIn("ws_c += ws_a + ws_b;", c_output)
        self.assertIn("ws_c = 7;", c_output)
        self.assertIn("ws_d = 7;", c_output)
        self.assertIn('snprintf(ws_text_a, sizeof(ws_text_a), "%-4.4s", "OK");', c_output)
        self.assertIn('snprintf(ws_text_b, sizeof(ws_text_b), "%-4.4s", "OK");', c_output)
        self.assertIn("ws_c += ws_a + ws_b;", rust_output)
        self.assertIn("ws_c = 7;", rust_output)
        self.assertIn("ws_d = 7;", rust_output)
        self.assertIn('ws_text_a = format!("{:<4}", "OK");', rust_output)
        self.assertIn('ws_text_b = format!("{:<4}", "OK");', rust_output)


if __name__ == "__main__":
    unittest.main()
