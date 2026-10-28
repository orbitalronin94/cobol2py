"""Integrity checks for the versioned differential benchmark corpus."""
import json
import unittest
from pathlib import Path

from benchmarks.run_benchmark import has_candidate_failures

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks" / "cases.json"


class BenchmarkManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.cases = cls.manifest.get("cases", [])

    def test_manifest_has_unique_stable_ids_and_source_paths(self):
        self.assertTrue(self.cases, "benchmark corpus must not be empty")
        ids = [case.get("id") for case in self.cases]
        paths = [case.get("path") for case in self.cases]
        self.assertTrue(all(isinstance(value, str) and value.strip() for value in ids))
        self.assertTrue(all(isinstance(value, str) and value.strip() for value in paths))
        self.assertEqual(len(ids), len(set(ids)), "duplicate benchmark case IDs")
        self.assertEqual(len(paths), len(set(paths)), "duplicate source paths in benchmark corpus")

    def test_every_manifest_entry_points_to_a_real_source_and_names_features(self):
        for case in self.cases:
            with self.subTest(case=case.get("id")):
                source = (ROOT / case["path"]).resolve()
                self.assertTrue(source.is_relative_to(ROOT.resolve()), "source path must remain inside repository")
                self.assertTrue(source.is_file(), f"missing source fixture: {case['path']}")
                self.assertTrue(
                    isinstance(case.get("features"), list) and case["features"]
                    and all(isinstance(feature, str) and feature.strip() for feature in case["features"]),
                    "each case needs explicit, non-empty feature metadata",
                )

    def test_benchmark_fails_closed_for_candidate_and_reference_errors(self):
        self.assertFalse(has_candidate_failures({
            "cases": [{
                "compile_ok": True, "reference_ok": True,
                "candidate": {"matched": True},
            }]
        }))
        self.assertTrue(has_candidate_failures({
            "cases": [{
                "compile_ok": True, "reference_ok": True,
                "candidate": {"matched": False},
            }]
        }))
        self.assertTrue(has_candidate_failures({
            "cases": [{
                "compile_ok": False, "reference_ok": False,
                "candidate": {"matched": False},
            }]
        }))
        self.assertTrue(has_candidate_failures({
            "cases": [{
                "compile_ok": True, "reference_ok": False,
                "candidate": {"matched": False},
            }]
        }))


if __name__ == "__main__":
    unittest.main()
