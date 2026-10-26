import unittest

from tools.gnucobol_trace import instrument_source


class TraceInstrumentationTests(unittest.TestCase):
    def test_inserts_snapshot_before_each_distinct_exit_path(self):
        source = "\n".join([
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. MULTIEXIT.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01 WS-COUNT PIC 9 VALUE 1.",
            "PROCEDURE DIVISION.",
            "MAIN.",
            "IF WS-COUNT = 1",
            "    STOP RUN.",
            "ELSE",
            "    GOBACK.",
            "END-IF.",
        ])
        instrumented, variables, skipped, unresolved, actual_format = instrument_source(
            source, source_format="free"
        )
        snapshots = [
            line for line in instrumented.splitlines()
            if 'DISPLAY "TRACE_VAR|WS-COUNT|"' in line
        ]
        self.assertEqual(variables, ["WS-COUNT"])
        self.assertEqual(len(snapshots), 2, instrumented)
        self.assertEqual(actual_format, "free")


if __name__ == "__main__":
    unittest.main()
