import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads(
    (ROOT / "experiments" / "failure-tournament" / "manifest.json").read_text(encoding="utf-8")
)


class FailureTournamentManifestTests(unittest.TestCase):
    def test_exactly_thirty_distinct_hypotheses(self):
        candidates = MANIFEST["candidates"]
        self.assertEqual(len(candidates), 30)
        self.assertEqual([item["seed"] for item in candidates], list(range(1, 31)))
        self.assertEqual(len({item["id"] for item in candidates}), 30)
        self.assertEqual(len({item["branch"] for item in candidates}), 30)

    def test_historical_main_reference_and_latest_remeasurement_are_separate(self):
        baseline = MANIFEST["baseline"]
        self.assertEqual(baseline["score"], 257)
        self.assertEqual(baseline["denominator"], 500)
        self.assertEqual(baseline["percent"], 51.4)
        self.assertEqual(baseline["source_run"], 42268813592)
        self.assertNotEqual(baseline["source_run"], 42266714599)

        latest = MANIFEST["latest_main_remeasurement"]
        self.assertEqual(latest["score"], 263)
        self.assertEqual(latest["denominator"], 500)
        self.assertEqual(latest["percent"], 52.6)
        self.assertEqual(latest["source_run"], 43578366403)
        self.assertEqual(latest["skip"], 500)
        self.assertEqual(latest["target"], 500)
        self.assertTrue(latest["archive_md5_verified"])
        self.assertEqual(latest["reference_fingerprint_coverage"]["complete_cases"], 500)

        historical = MANIFEST["historical_main_remeasurement"]
        self.assertEqual(historical["score"], 258)
        self.assertEqual(historical["source_run"], 42272058313)
        self.assertEqual(historical["skip"], 500)
        self.assertEqual(historical["target"], 500)

    def test_zero_regression_gate_and_blocked_readiness(self):
        self.assertEqual(MANIFEST["benchmark"]["skip"], 500)
        self.assertEqual(MANIFEST["benchmark"]["target"], 500)
        self.assertEqual(MANIFEST["acceptance"]["regressions_allowed"], 0)
        self.assertTrue(MANIFEST["acceptance"]["complete_holdout_required"])
        self.assertEqual(MANIFEST["readiness"]["status"], "blocked")
        self.assertEqual(MANIFEST["last_tournament_attempt"]["eligible_candidates"], 0)

    def test_frozen_main_oracle_is_required_for_ranking(self):
        self.assertTrue(MANIFEST["acceptance"]["frozen_baseline_oracle_required"])
        self.assertTrue(MANIFEST["acceptance"]["candidate_run_oracle_drift_is_diagnostic"])
        self.assertEqual(
            MANIFEST["benchmark"]["reference_oracle_fields"],
            ["reference_stdout_sha256", "reference_stdout_length", "reference_returncode"],
        )

    def test_every_candidate_is_a_single_named_hypothesis(self):
        for candidate in MANIFEST["candidates"]:
            with self.subTest(seed=candidate["seed"]):
                self.assertTrue(candidate["id"])
                self.assertTrue(candidate["hypothesis"].endswith(".") or candidate["hypothesis"].endswith("behavior."))
                self.assertTrue(candidate["branch"].startswith("experiment-failure-seed/"))


if __name__ == "__main__":
    unittest.main()
