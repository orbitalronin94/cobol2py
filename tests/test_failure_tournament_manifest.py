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
        self.assertEqual(MANIFEST["experimental_reference"]["source_run"], 42266714599)
        self.assertEqual(MANIFEST["experimental_reference"]["head_branch"], "experiment/holdout-error-topography")
        self.assertEqual(MANIFEST["experimental_reference"]["score"], 258)
        self.assertEqual(MANIFEST["experimental_reference"]["kind"], "experimental_only_not_main")

        latest = MANIFEST["latest_main_remeasurement"]
        self.assertEqual(latest["score"], 263)
        self.assertEqual(latest["denominator"], 500)
        self.assertEqual(latest["percent"], 52.6)
        self.assertEqual(latest["source_run"], 45696510554)
        self.assertEqual(latest["skip"], 500)
        self.assertEqual(latest["target"], 500)
        self.assertTrue(latest["archive_md5_verified"])
        self.assertEqual(latest["reference_fingerprint_coverage"]["complete_cases"], 500)
        self.assertEqual(latest["current_main_sha"], "cb1691258bde56901e0e4e3f124e8f79e96016d4")
        self.assertEqual(MANIFEST["current_baseline"]["source_run"], 45696510554)
        self.assertEqual(MANIFEST["current_baseline"]["score"], 263)
        self.assertEqual(MANIFEST["current_baseline"]["main_sha_at_audit"], "cb1691258bde56901e0e4e3f124e8f79e96016d4")
        self.assertTrue(MANIFEST["latest_verified_code_equivalent_main"]["exact_run_on_current_main_sha"])
        self.assertEqual(MANIFEST["post_merge_casewise_comparison"]["new_pass_case_ids"], ["sq206a-3536dcf7c2"])
        self.assertEqual(MANIFEST["post_merge_casewise_comparison"]["regressed_case_ids"], ["exec84-2-03eae98697"])

        historical = MANIFEST["historical_main_remeasurement"]
        self.assertEqual(historical["score"], 258)
        self.assertEqual(historical["source_run"], 42272058313)
        self.assertEqual(historical["skip"], 500)
        self.assertEqual(historical["target"], 500)
        self.assertEqual(historical["workflow_conclusion"], "cancelled")
        self.assertTrue(historical["baseline_artifact_complete"])

    def test_latest_exact_main_repeat_records_timeout_and_oracle_drift(self):
        repeat = MANIFEST["latest_baseline_repeat_diagnostic"]
        self.assertEqual(repeat["main_sha"], "b26cc0335708dab99737cc902c1d96186fec9f94")
        self.assertEqual(repeat["previous_run"], 45056162017)
        self.assertEqual(repeat["current_run"], 45283644192)
        self.assertEqual(repeat["previous_score"], 263)
        self.assertEqual(repeat["current_score"], 262)
        self.assertTrue(repeat["same_500_case_ids"])
        self.assertTrue(repeat["same_500_source_hashes"])
        self.assertEqual(repeat["status_flip_case_ids"], ["exec84-2-03eae98697"])
        self.assertEqual(repeat["oracle_drift_count"], 12)
        self.assertEqual(repeat["status_flip_details"]["current_failure_reason"], "translator timeout")

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
        self.assertTrue(tournament["auto_discover_manifest_queue"])
        self.assertFalse(tournament["auto_discover_open_prs"])
        self.assertEqual(tournament["discovery_source"], "current_main_pr_tournament.candidate_queue")
        self.assertRegex(tournament["workflow_sha"], r"^[0-9a-f]{40}$")
        self.assertEqual(tournament["candidate_queue"], [])
        result = tournament["latest_candidate_evaluation"]
        self.assertEqual(result["pr"], 407)
        self.assertEqual(result["baseline_score"], 263)
        self.assertEqual(result["candidate_score"], 265)
        self.assertEqual(result["paired_run"], 45609355925)
        self.assertEqual(result["comparable_cases"], 500)
        self.assertEqual(result["new_pass_case_ids"], ["nc122a-0a3c88dcdf", "nc122a-531a96359c", "nc2214-2-fdbb829806"])
        self.assertEqual(result["regressed_case_ids"], ["exec84-2-03eae98697"])
        self.assertEqual(result["revalidated_new_passes"], 3)
        self.assertEqual(result["revalidated_regressions"], 1)
        self.assertFalse(result["closed_unmerged"])
        self.assertEqual(result["status"], "completed")
        self.assertFalse(result["eligible"])
        self.assertEqual(result["decision"], "ineligible_one_timeout_regression")
        previous = tournament["previous_candidate_evaluation"]
        self.assertEqual(previous["pr"], 398)
        self.assertEqual(previous["candidate_score"], 263)
        self.assertEqual(previous["new_passes"], 0)
        self.assertEqual(previous["regressions"], 0)
        self.assertEqual(previous["oracle_drift_count"], 8)
        self.assertFalse(previous["eligible"])
        paired = MANIFEST["latest_paired_pr_tournament"]
        self.assertEqual(paired["run"], 45609355925)
        self.assertEqual(paired["status"], "completed")
        self.assertEqual(paired["candidate_score"], 265)
        self.assertEqual(paired["comparable_cases"], 500)
        self.assertEqual(paired["new_passes"], 3)
        self.assertEqual(paired["regressions"], 1)
        self.assertEqual(paired["regressed_case_ids"], ["exec84-2-03eae98697"])
        self.assertEqual(paired["oracle_drift_count"], 9)
        self.assertFalse(paired["eligible"])

    def test_30_seed_audit_is_fresh_and_still_blocked(self):
        audit = MANIFEST["candidate_branch_audit"]
        self.assertEqual(audit["compared_against_main"], "cb1691258bde56901e0e4e3f124e8f79e96016d4")
        self.assertEqual(audit["latest_comparison"]["distinct_branch_heads"], 30)
        self.assertEqual(audit["latest_comparison"]["current_main_sha"], "cb1691258bde56901e0e4e3f124e8f79e96016d4")
        self.assertEqual(MANIFEST["readiness"]["audit_main_sha"], "cb1691258bde56901e0e4e3f124e8f79e96016d4")
        self.assertTrue(audit["all_30_exist"])
        self.assertTrue(audit["all_30_diverged"])
        self.assertEqual(audit["ahead_only_candidates"], 0)
        self.assertEqual(len(audit["branch_comparisons"]), 30)
        self.assertTrue(all(item["status"] == "diverged" for item in audit["branch_comparisons"]))
        self.assertEqual(MANIFEST["readiness"]["candidates_without_translator_or_tests"], [11, 12, 13, 14, 15])
        self.assertEqual(MANIFEST["readiness"]["status"], "blocked")

    def test_30_seed_workflow_is_manual_and_never_promotes_automatically(self):
        workflow = (ROOT / ".github" / "workflows" / "failure-directed-30-seed-tournament.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn('readiness", {}).get("status") != "ready"', workflow)
        self.assertIn("candidate_shas", workflow)
        self.assertNotIn("gh pr merge", workflow)


    def test_audited_main_head_waits_for_exact_sha_remeasurement(self):
        head = MANIFEST["audited_main_head"]
        self.assertEqual(head["sha"], "cb1691258bde56901e0e4e3f124e8f79e96016d4")
        self.assertEqual(head["translator_blob_sha"], "4a7562627d161580470f1b0522cda0b094f635b0")
        self.assertTrue(head["translator_blob_unchanged_since_previous_exact_baseline"])
        self.assertTrue(head["exact_500_case_run_on_this_sha"])
        pending = MANIFEST["pending_main_remeasurement"]
        self.assertEqual(pending["status"], "completed")
        self.assertEqual(MANIFEST["latest_main_remeasurement"]["source_run"], 45696510554)
        self.assertEqual(pending["target_sha"], "cb1691258bde56901e0e4e3f124e8f79e96016d4")
        self.assertTrue(pending["queue_empty"])
        self.assertEqual(pending["skip"], 500)
        self.assertEqual(pending["target"], 500)

    def test_legacy_105_case_screen_is_manual_only_after_pr_403(self):
        merged = MANIFEST["latest_infrastructure_merge"]
        self.assertEqual(merged["pr"], 403)
        self.assertTrue(merged["merged"])
        self.assertFalse(merged["translator_changed"])
        self.assertTrue(merged["checks"]["all_success"])
        self.assertTrue(merged["followup_main_checks"]["all_success"])


if __name__ == "__main__":
    unittest.main()

    def test_latest_exact_baseline_and_pending_inspect_performance_recheck(self):
        self.assertEqual(MANIFEST["latest_main_remeasurement"]["source_run"], 45696510554)
        self.assertEqual(MANIFEST["latest_main_remeasurement"]["score"], 263)
        repeat = MANIFEST["latest_same_sha_repeat_diagnostic"]
        self.assertTrue(repeat["same_500_case_ids"])
        self.assertTrue(repeat["same_500_source_hashes"])
        self.assertEqual(repeat["oracle_drift_count"], 9)
        self.assertEqual(
            repeat["status_flip_case_ids"],
            ["exec84-2-03eae98697", "rock-paper-scissors-ad6321acf1"],
        )
        pending = MANIFEST["pending_candidate_remeasurement"]
        self.assertEqual(pending["pr"], 407)
        self.assertEqual(pending["head_sha"], "a431d2f8f7cac6e720a212baad76fa447e5f98ee")
        self.assertEqual(pending["paired_run"], 45812887898)
        self.assertEqual(pending["unit_suite_conclusion"], "success")
        self.assertEqual(pending["status"], "in_progress")
        self.assertIsNone(pending["score"])
