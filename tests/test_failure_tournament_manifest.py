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
        self.assertEqual(latest["source_run"], 44599918790)
        self.assertEqual(latest["skip"], 500)
        self.assertEqual(latest["target"], 500)
        self.assertTrue(latest["archive_md5_verified"])
        self.assertEqual(latest["reference_fingerprint_coverage"]["complete_cases"], 500)
        self.assertEqual(latest["current_main_sha"], "4238c8da8aec9d7a1a2de6fc1abcf04ddd6c3133")
        self.assertEqual(MANIFEST["current_baseline"]["source_run"], 44599918790)
        self.assertEqual(MANIFEST["current_baseline"]["score"], 263)
        self.assertEqual(MANIFEST["current_baseline"]["main_sha_at_audit"], "4238c8da8aec9d7a1a2de6fc1abcf04ddd6c3133")
        self.assertTrue(MANIFEST["latest_verified_code_equivalent_main"]["exact_run_on_current_main_sha"])
        self.assertEqual(MANIFEST["post_merge_casewise_comparison"]["new_pass_case_ids"], ["sq206a-3536dcf7c2"])
        self.assertEqual(MANIFEST["post_merge_casewise_comparison"]["regressed_case_ids"], ["exec84-2-03eae98697"])

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


    def test_current_main_pr_tournament_records_full_casewise_candidate_evaluation(self):
        tournament = MANIFEST["current_main_pr_tournament"]
        self.assertEqual(tournament["default_candidate_prs"], [])
        self.assertTrue(tournament["auto_discover_open_prs"])
        self.assertEqual(tournament["candidate_queue"], [])
        result = tournament["latest_candidate_evaluation"]
        self.assertEqual(result["pr"], 371)
        self.assertEqual(result["baseline_score"], 263)
        self.assertEqual(result["candidate_score"], 262)
        self.assertEqual(result["paired_run"], 44599918790)
        self.assertEqual(result["comparable_cases"], 500)
        self.assertEqual(result["new_pass_case_ids"], [])
        self.assertEqual(result["regressed_case_ids"], ["exec84-2-03eae98697"])
        self.assertFalse(result["eligible"])
        self.assertEqual(result["decision"], "ineligible_zero_gain_one_regression")
        previous = tournament["previous_candidate_evaluation"]
        self.assertEqual(previous["pr"], 398)
        self.assertEqual(previous["candidate_score"], 263)
        self.assertEqual(previous["new_passes"], 0)
        self.assertEqual(previous["regressions"], 0)
        self.assertEqual(previous["oracle_drift_count"], 8)
        self.assertFalse(previous["eligible"])
        paired = MANIFEST["latest_paired_pr_tournament"]
        self.assertEqual(paired["run"], 44599918790)
        self.assertEqual(paired["status"], "completed")
        self.assertEqual(paired["candidate_score"], 262)
        self.assertEqual(paired["comparable_cases"], 500)
        self.assertEqual(paired["new_passes"], 0)
        self.assertEqual(paired["regressions"], 1)
        self.assertEqual(paired["regressed_case_ids"], ["exec84-2-03eae98697"])
        self.assertEqual(paired["oracle_drift_count"], 9)
        self.assertFalse(paired["eligible"])

    def test_30_seed_audit_is_fresh_and_still_blocked(self):
        audit = MANIFEST["candidate_branch_audit"]
        self.assertEqual(audit["compared_against_main"], "399b55e77d47cdd15367a9b17c3b116a962a39c7")
        self.assertEqual(audit["latest_comparison"]["distinct_branch_heads"], 30)
        self.assertEqual(audit["latest_comparison"]["current_main_sha"], "399b55e77d47cdd15367a9b17c3b116a962a39c7")
        self.assertEqual(MANIFEST["readiness"]["audit_main_sha"], "399b55e77d47cdd15367a9b17c3b116a962a39c7")
        self.assertTrue(audit["all_30_exist"])
        self.assertTrue(audit["all_30_diverged"])
        self.assertEqual(audit["ahead_only_candidates"], 0)
        self.assertEqual(len(audit["branch_comparisons"]), 30)
        self.assertEqual(MANIFEST["readiness"]["candidates_without_translator_or_tests"], [11, 12, 13, 14, 15])
        self.assertEqual(MANIFEST["readiness"]["status"], "blocked")

    def test_30_seed_workflow_is_manual_and_never_promotes_automatically(self):
        workflow = (ROOT / ".github" / "workflows" / "failure-directed-30-seed-tournament.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn('readiness", {}).get("status") != "ready"', workflow)
        self.assertIn("candidate_shas", workflow)
        self.assertNotIn("gh pr merge", workflow)



if __name__ == "__main__":
    unittest.main()
