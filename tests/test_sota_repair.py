from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ronin.behavioral_spec_graph import BehavioralSpecGraph
from ronin.compiler_guided_repair import repair_python_source
from ronin.smt_feedback_loop import propose_local_repair
from ronin.symbolic_executor import delta_debug_input, generate_path_cases
from ronin.repair_pipeline import RepairPipeline
from ronin.translation_cache import TranslationCache


class SotaRepairTests(unittest.TestCase):
    def test_translation_cache_exact_hit_and_fingerprint_invalidation(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache.sqlite3"
            with TranslationCache(cache_path) as cache:
                self.assertIsNone(cache.get("DISPLAY A", "build-1"))
                cache.put("DISPLAY A", "print(a)", "build-1")
                self.assertEqual(cache.get("DISPLAY A", "build-1"), "print(a)")
                self.assertIsNone(cache.get("DISPLAY B", "build-1"))
                self.assertIsNone(cache.get("DISPLAY A", "build-2"))

    def test_translation_cache_persists_between_instances(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "cache.sqlite3"
            with TranslationCache(cache_path) as cache:
                cache.put("MOVE 1 TO A", "a = 1", "sha256:translator")
            with TranslationCache(cache_path) as cache:
                self.assertEqual(cache.get("MOVE 1 TO A", "sha256:translator"), "a = 1")

    def test_behavioral_graph_captures_rules_and_io(self):
        graph = BehavioralSpecGraph.from_cobol(
            "IF AMOUNT > 50\n MOVE 10 TO DISCOUNT\nEND-IF\nDISPLAY DISCOUNT")
        kinds = {node.kind for node in graph.nodes}
        self.assertTrue({"condition", "transform", "output"} <= kinds)
        self.assertEqual(graph.source_map()[1], "n1")
        self.assertEqual(json.loads(graph.to_json())["schema_version"], 1)

    def test_compiler_guided_local_repair(self):
        result = repair_python_source("print(x = 1\n")
        self.assertTrue(result.compiled)
        self.assertEqual(result.source, "x = 1\nprint(x)\n")

    def test_reciprocal_repair_is_narrow(self):
        self.assertEqual(propose_local_repair("A / 3", "A * 0.333"), "A / 3")
        self.assertIsNone(propose_local_repair("A + 3", "A * 0.333"))

    def test_symbolic_cases_cover_both_branches(self):
        cases = generate_path_cases("IF AMOUNT > 50")
        self.assertEqual({case.branch for case in cases}, {"true", "false"})
        self.assertTrue(all("AMOUNT" in case.inputs for case in cases))

    def test_delta_debugging_reduces_failure(self):
        source = "keep\nremove\nkeep-too\n"
        result = delta_debug_input(source, lambda candidate: "keep" in candidate)
        self.assertIn("keep", result.minimized)
        self.assertLess(len(result.minimized), len(source))

    def test_pipeline_reports_compiler_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "repair_report.json"
            pipeline = RepairPipeline(report_path=report)
            result = pipeline.repair_case("syntax-1", "print(x = 1\n")
            self.assertTrue(result.repaired)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["cases"][0]["technique"], "compiler")


if __name__ == "__main__":
    unittest.main()
