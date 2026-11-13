import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import cobol2py


class InspectCharactersLatin1Tests(unittest.TestCase):
    def test_inspect_characters_and_latin1_display_match_original_bytes(self):
        source_bytes = (
            b"IDENTIFICATION DIVISION.\n"
            b"PROGRAM-ID. LATIN1-INSPECT.\n"
            b"DATA DIVISION.\n"
            b"WORKING-STORAGE SECTION.\n"
            b"01 WS-STR PIC X(15) VALUE 'AEDCILIDVALDV'.\n"
            b"01 WS-N PIC 9(2) VALUE 0.\n"
            b"PROCEDURE DIVISION.\n"
            b"MAIN.\n"
            b"    INSPECT WS-STR TALLYING WS-N FOR ALL CHARACTERS.\n"
            b'    DISPLAY "N\xdaMERO caracteres: " WS-N.\n'
            b"    STOP RUN.\n"
        )
        source, encoding = cobol2py.decode_cobol_source(source_bytes)
        self.assertEqual(encoding, "latin-1")
        self.assertIn("NÚMERO caracteres", source)

        program = cobol2py.parse_cobol(source, source_format="free")
        generated = cobol2py.apply_cobol_output_encoding(
            cobol2py.emit_python(program), encoding
        )
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "translated.py"
            script.write_text(generated, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(
            result.returncode, 0,
            result.stderr.decode("latin-1", errors="replace"),
        )
        self.assertEqual(result.stdout, b"N\xdaMERO caracteres: 15\n")

    def test_utf8_source_keeps_default_utf8_output(self):
        source, encoding = cobol2py.decode_cobol_source(
            'IDENTIFICATION DIVISION.\nDISPLAY "HOLA".\n'.encode("utf-8")
        )
        self.assertEqual(encoding, "utf-8")
        self.assertIn("HOLA", source)
        generated = "print('HOLA')"
        self.assertIs(
            cobol2py.apply_cobol_output_encoding(generated, encoding),
            generated,
        )


if __name__ == "__main__":
    unittest.main()
