"""Tests for the differential benchmark's CI exit policy."""
import unittest

from benchmarks.run_benchmark import has_candidate_failures


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

    def test_missing_candidate_result_fails_closed(self):
        report = {"cases": [{"compile_ok": True, "candidate": None}]}
        self.assertTrue(has_candidate_failures(report))


if __name__ == "__main__":
    unittest.main()
