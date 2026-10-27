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

    def test_unicode_nested_paths_and_empty_repository(self):
        path = self.write("módulos/área/PROGRÁMA.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. PROGRAMA.
PROCEDURE DIVISION.
    STOP RUN.
""")
        plan = analyze_repository(self.root)
        self.assertIn("módulos/área/PROGRÁMA.cbl", [item["path"] for item in plan["files"]])
        self.assertEqual(plan["summary"]["cobol_programs"], 1)
        self.assertEqual(plan["unresolved_references"], [])

        with tempfile.TemporaryDirectory() as empty:
            empty_plan = analyze_repository(Path(empty))
        self.assertEqual(empty_plan["summary"]["files"], 0)
        self.assertEqual(empty_plan["dependencies"], [])
        self.assertEqual(empty_plan["unresolved_references"], [])

    def test_inventory_handles_hundreds_of_nested_sources(self):
        for index in range(200):
            self.write(f"familia-{index % 8:02d}/PROG-{index:03d}.cbl",
                       f"IDENTIFICATION DIVISION.\nPROGRAM-ID. PROG{index:03d}.\nPROCEDURE DIVISION.\n STOP RUN.\n")
        plan = analyze_repository(self.root)
        self.assertEqual(plan["summary"]["cobol_programs"], 200)
        self.assertEqual(len(plan["files"]), 200)
        self.assertEqual(plan["summary"]["unresolved_references"], 0)

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

    def test_complexity_scoring_flags_dynamic_control_flow_and_overlays(self):
        self.write("HIGH-RISK.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. HIGH-RISK.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-RAW PIC X(10).
01 WS-NUM REDEFINES WS-RAW PIC 9(10).
01 WS-STEP PIC 9.
PROCEDURE DIVISION.
MAIN-LOGIC.
    ALTER POINT-X TO PROCEED TO POINT-Y.
    GO TO POINT-A POINT-B DEPENDING ON WS-STEP.
    STOP RUN.
""")
        self.write("LOW-RISK.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. LOW-RISK.
PROCEDURE DIVISION.
    DISPLAY "ALTER X GO TO A REDEFINES B".
    *> GO TO A B DEPENDING ON WS-STEP.
    STOP RUN.
""")
        plan = analyze_repository(self.root)
        high = next(item for item in plan["files"] if item["path"] == "HIGH-RISK.cbl")
        low = next(item for item in plan["files"] if item["path"] == "LOW-RISK.cbl")

        self.assertEqual(high["complexity_level"], "HIGH")
        self.assertGreaterEqual(high["complexity_score"], 10)
        self.assertIn("alter-dynamic-control-flow", high["features"])
        self.assertIn("computed-goto", high["features"])
        self.assertIn("redefines", high["features"])
        self.assertEqual(low["complexity_level"], "LOW")
        self.assertEqual(low["complexity_score"], 0)
        self.assertEqual(plan["summary"]["high_complexity_files"], 1)
        markdown = render_markdown(plan)
        self.assertIn("High-complexity files (heuristic)", markdown)
        self.assertIn("GO TO DEPENDING ON", markdown)
        self.assertIn("HIGH", markdown)

    def test_ignores_generated_and_hidden_directories(self):
        self.write(".git/ignored.cbl", "IDENTIFICATION DIVISION. PROGRAM-ID. NOPE.")
        self.write("build/generated.cbl", "IDENTIFICATION DIVISION. PROGRAM-ID. NOPE.")
        self.write("src/ok.cbl", "IDENTIFICATION DIVISION. PROGRAM-ID. OK.")
        plan = analyze_repository(self.root)
        paths = {x["path"] for x in plan["files"]}
        self.assertEqual(paths, {"src/ok.cbl"})

    def test_ignores_dependency_keywords_inside_literals(self):
        self.write("MAIN.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. MAIN.
PROCEDURE DIVISION.
    DISPLAY "COPY GHOST".
    DISPLAY "CALL MISSING".
    DISPLAY "EXEC SQL INCLUDE SQLGHOST".
    STOP RUN.
""")
        plan = analyze_repository(self.root)
        main = next(item for item in plan["files"] if item["path"] == "MAIN.cbl")
        self.assertEqual(main["copybooks"], [])
        self.assertEqual(main["calls"], [])
        self.assertEqual(main["dynamic_calls"], [])
        self.assertEqual(main["sql_includes"], [])
        self.assertEqual(plan["unresolved_references"], [])

    def test_ignores_commented_out_references(self):
        self.write("MAIN.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. MAIN.
PROCEDURE DIVISION.
*> COPY MISSING-COPY.
*> CALL "MISSING-CALL".
    DISPLAY "LIVE". *> COPY ALSO-MISSING.
    STOP RUN.
""")
        self.write("RUN.jcl", """//* COMMENTED EXEC PGM=GHOST
//STEP1 EXEC PGM=MAIN
//* DD DSN=GHOST.DATA
""")
        self.write("query.sql", """-- INCLUDE MISSING-SQL
SELECT '-- not a comment marker in this literal' FROM SYSIBM.SYSDUMMY1;
""")
        plan = analyze_repository(self.root)
        unresolved = {(item["relation"], item["symbol"])
                      for item in plan["unresolved_references"]}
        self.assertNotIn(("copy", "MISSING-COPY"), unresolved)
        self.assertNotIn(("call", "MISSING-CALL"), unresolved)
        self.assertNotIn(("copy", "ALSO-MISSING"), unresolved)
        self.assertNotIn(("jcl-exec", "GHOST"), unresolved)
        self.assertNotIn(("sql-include", "MISSING-SQL"), unresolved)
        run = next(item for item in plan["files"] if item["path"] == "RUN.jcl")
        self.assertEqual(run["jcl_programs"], ["MAIN"])

    def test_ignores_fixed_format_comment_records(self):
        self.write("FIXED.cbl", """000100* COPY GHOST-FIXED.
000200 IDENTIFICATION DIVISION.
000300 PROGRAM-ID. FIXED.
000400 PROCEDURE DIVISION.
000500 STOP RUN.
""")
        plan = analyze_repository(self.root)
        unresolved = {(item["relation"], item["symbol"])
                      for item in plan["unresolved_references"]}
        self.assertNotIn(("copy", "GHOST-FIXED"), unresolved)
        fixed = next(item for item in plan["files"] if item["path"] == "FIXED.cbl")
        self.assertEqual(fixed["program_id"], "FIXED")

    def test_reports_ambiguous_dependency_targets(self):
        self.write("MAIN.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. MAIN.
PROCEDURE DIVISION.
    CALL "SUBPROG".
    STOP RUN.
""")
        self.write("src_a/SUBPROG.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. SUBPROG.
PROCEDURE DIVISION.
    GOBACK.
""")
        self.write("src_b/OTHER.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. SUBPROG.
PROCEDURE DIVISION.
    GOBACK.
""")
        plan = analyze_repository(self.root)
        matches = [item for item in plan["ambiguous_references"]
                   if item["source"] == "MAIN.cbl" and item["relation"] == "call"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["symbol"], "SUBPROG")
        self.assertEqual(len(matches[0]["candidates"]), 2)
        self.assertEqual(plan["summary"]["ambiguous_references"], 1)
        self.assertIn("Ambiguous references", render_markdown(plan))

    def test_separates_literal_and_dynamic_call_targets(self):
        self.write("MAIN.cbl", """IDENTIFICATION DIVISION.
PROGRAM-ID. MAIN.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-PROGRAM PIC X(8) VALUE "SUBPROG".
PROCEDURE DIVISION.
    CALL "SUBPROG".
    CALL WS-PROGRAM.
    STOP RUN.
""")
        self.write("SUBPROG.cbl", "IDENTIFICATION DIVISION.\\nPROGRAM-ID. SUBPROG.\\n")
        plan = analyze_repository(self.root)
        main = next(item for item in plan["files"] if item["path"] == "MAIN.cbl")
        self.assertEqual(main["calls"], ["SUBPROG"])
        self.assertEqual(main["dynamic_calls"], ["WS-PROGRAM"])
        self.assertFalse(any(item["relation"] == "call" and item["symbol"] == "WS-PROGRAM"
                             for item in plan["unresolved_references"]))
        self.assertEqual(plan["summary"]["dynamic_call_targets"], 1)
        report = render_markdown(plan)
        self.assertIn("Dynamic CALL targets", report)
        self.assertIn("WS-PROGRAM", report)

    def test_json_serializable(self):
        self.write("ONE.cbl", "IDENTIFICATION DIVISION. PROGRAM-ID. ONE.")
        encoded = json.dumps(analyze_repository(self.root))
        self.assertIn('"schema_version": 1', encoded)


if __name__ == "__main__":
    unittest.main()
