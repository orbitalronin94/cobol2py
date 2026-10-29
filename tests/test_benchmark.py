"""Tests for the differential benchmark's CI exit policy."""
import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "cobol2py_run_benchmark", Path(__file__).resolve().parents[1] / "benchmarks" / "run_benchmark.py"
)
_benchmark = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_benchmark)
has_candidate_failures = _benchmark.has_candidate_failures


class BenchmarkExitPolicyTests(unittest.TestCase):
    def test_all_candidate_cases_matching_is_success(self):
        report = {
            "cases": [
                {"compile_ok": True, "candidate": {"matched": True}},
                {"compile_ok": True, "candidate": {"matched": True}},
            ]
        }
        self.assertFalse(has_candidate_failures(report))

    def test_candidate_mismatch_fails(self):
        report = {"cases": [{"compile_ok": True, "candidate": {"matched": False}}]}
        self.assertTrue(has_candidate_failures(report))

    def test_reference_compile_failure_fails(self):
        report = {"cases": [{"compile_ok": False, "candidate": {"matched": False}}]}
        self.assertTrue(has_candidate_failures(report))

    def test_reference_runtime_failure_fails(self):
        report = {
            "cases": [{
                "compile_ok": True,
                "reference_ok": False,
                "candidate": {"matched": False},
            }]
        }
        self.assertTrue(has_candidate_failures(report))

    def test_legacy_report_without_reference_ok_remains_compatible(self):
        report = {"cases": [{"compile_ok": True, "candidate": {"matched": True}}]}
        self.assertFalse(has_candidate_failures(report))

    def test_missing_candidate_result_fails_closed(self):
        report = {"cases": [{"compile_ok": True, "candidate": None}]}
        self.assertTrue(has_candidate_failures(report))


if __name__ == "__main__":
    unittest.main()
