import json
import tempfile
import unittest
from pathlib import Path

from cobol2py_agent import analyze_repository, render_markdown


class RepositoryAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "copy").mkdir()
        (self.root / "jcl").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_inventory_and_copy_dependency(self):
        self.write("MAIN.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. MAINPROG.
DATA DIVISION.
WORKING-STORAGE SECTION.
COPY CUSTOMER-REC.
PROCEDURE DIVISION.
    CALL "SUBPROG".
    EXEC SQL INCLUDE SQLCA END-EXEC.
    STOP RUN.
""")
        self.write("copy/CUSTOMER-REC.cpy", "01 CUSTOMER-REC PIC X(10).\n")
        self.write("SUBPROG.cbl", "IDENTIFICATION DIVISION.\nPROGRAM-ID. SUBPROG.\n")
        self.write("jcl/NIGHTLY.jcl", "//STEP1 EXEC PGM=MAINPROG\n//OUT DD DSN=APP.OUT,DISP=OLD\n")
        self.write("sql/SQLCA.sql", "-- SQL include placeholder\n")

        plan = analyze_repository(self.root)
        summary = plan["summary"]
        self.assertEqual(summary["cobol_programs"], 2)
        self.assertEqual(summary["copybooks"], 1)
        self.assertEqual(summary["jcl_files"], 1)
        self.assertEqual(summary["sql_files"], 1)
        self.assertTrue(any(e["relation"] == "copy" and e["symbol"] == "CUSTOMER-REC"
                            for e in plan["dependencies"]))
        self.assertTrue(any(e["relation"] == "call" and e["symbol"] == "SUBPROG"
                            for e in plan["dependencies"]))
        self.assertTrue(any(e["relation"] == "jcl-exec" and e["symbol"] == "MAINPROG"
                            for e in plan["dependencies"]))
        nightly = next(x for x in plan["files"] if x["path"] == "jcl/NIGHTLY.jcl")
        self.assertEqual(nightly["jcl_datasets"], ["APP.OUT"])
        self.assertTrue(any(e["relation"] == "sql-include" and e["symbol"] == "SQLCA"
                            for e in plan["dependencies"]))

    def test_unresolved_reference_and_risk_flags(self):
        self.write("PAYROLL.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. PAYROLL.
PROCEDURE DIVISION.
    CALL "DYNAMIC-MISSING".
    EXEC CICS SEND MAP('PAY') END-EXEC.
""")
        plan = analyze_repository(self.root)
        self.assertTrue(any(r["symbol"] == "DYNAMIC-MISSING"
                            for r in plan["unresolved_references"]))
        payroll = next(x for x in plan["files"] if x["path"] == "PAYROLL.cbl")
        self.assertIn("cics", payroll["features"])
        self.assertIn("subprogram-calls", payroll["features"])
        self.assertIn("Limitations", render_markdown(plan))

    def test_ignores_generated_and_hidden_directories(self):
        self.write(".git/ignored.cbl", "IDENTIFICATION DIVISION. PROGRAM-ID. NOPE.")
        self.write("build/generated.cbl", "IDENTIFICATION DIVISION. PROGRAM-ID. NOPE.")
        self.write("src/ok.cbl", "IDENTIFICATION DIVISION. PROGRAM-ID. OK.")
        plan = analyze_repository(self.root)
        paths = {x["path"] for x in plan["files"]}
        self.assertEqual(paths, {"src/ok.cbl"})

    def test_json_serializable(self):
        self.write("ONE.cbl", "IDENTIFICATION DIVISION. PROGRAM-ID. ONE.")
        encoded = json.dumps(analyze_repository(self.root))
        self.assertIn('"schema_version": 1', encoded)


if __name__ == "__main__":
    unittest.main()
