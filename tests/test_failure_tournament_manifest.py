import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads(
    (ROOT / "experiments" / "failure-tournament" / "manifest.json").read_text(encoding="utf-8")
)


class FailureTournamentManifestTests(unittest.TestCase):
    def test_historical_main_reference_is_separate_from_latest_verified_baseline(self):
        historical = MANIFEST["baseline"]
        self.assertEqual((historical["score"], historical["denominator"], historical["source_run"]), (257, 500, 42268813592))
        experimental = MANIFEST["experimental_reference"]
        self.assertEqual((experimental["score"], experimental["source_run"]), (258, 42266714599))
        self.assertEqual(experimental["kind"], "experimental_only_not_main")
        latest = MANIFEST["latest_main_remeasurement"]
        self.assertEqual((latest["score"], latest["denominator"], latest["source_run"]), (263, 500, 46061895588))
        self.assertEqual(latest["current_main_sha"], "2dcf47bf3376289aca011ea98b84aa4b52c3956c")
        self.assertEqual(latest["percent"], 52.6)
        self.assertTrue(latest["archive_md5_verified"])
        self.assertEqual(latest["reference_fingerprint_coverage"]["complete_cases"], 500)

    def test_fixed_benchmark_contract(self):
        benchmark = MANIFEST["benchmark"]
        self.assertEqual(benchmark["corpus"], "X-COBOL v2")
        self.assertEqual((benchmark["skip"], benchmark["target"]), (500, 500))
        self.assertTrue(benchmark["casewise"])
        self.assertEqual(MANIFEST["acceptance"]["regressions_allowed"], 0)
        self.assertTrue(MANIFEST["acceptance"]["complete_holdout_required"])
        self.assertTrue(MANIFEST["acceptance"]["frozen_baseline_oracle_required"])

    def test_current_main_tournament_uses_only_curated_queue(self):
        tournament = MANIFEST["current_main_pr_tournament"]
        self.assertFalse(tournament["auto_discover_open_prs"])
        self.assertTrue(tournament["auto_discover_manifest_queue"])
        self.assertEqual(tournament["candidate_queue"], [])

    def test_inspect_candidate_has_four_gains_and_zero_regressions(self):
        paired = MANIFEST["latest_paired_pr_tournament"]
        self.assertEqual(paired["run"], 46061895588)
        self.assertEqual((paired["baseline_score"], paired["candidate_score"]), (263, 266))
        self.assertEqual(paired["new_pass_case_ids"], [
            "nc122a-0a3c88dcdf",
            "nc122a-531a96359c",
            "nc2214-2-fdbb829806",
        ])
        self.assertEqual(paired["regressed_case_ids"], [])
        self.assertTrue(paired["eligible"])
        self.assertEqual(paired["promotion_status"], "merged")
        recheck = MANIFEST["latest_candidate_artifact_comparison"]
        self.assertEqual(recheck["baseline_run"], 46061895588)
        self.assertEqual((recheck["baseline_score"], recheck["candidate_score"]), (263, 266))
        self.assertEqual(recheck["new_pass_case_ids"], paired["new_pass_case_ids"])
        self.assertEqual(recheck["regressed_case_ids"], [])
        self.assertEqual(recheck["comparable_cases"], 500)
        self.assertEqual(recheck["source_hash_matches"], 500)
        self.assertEqual(recheck["oracle_drift_count"], 9)

    def test_current_main_remeasurement_after_ci_merge_is_pending(self):
        pending = MANIFEST["pending_main_remeasurement"]
        self.assertEqual(pending["target_sha"], "f3bcea96c6eaee446453b0f463839e75ea412d72")
        self.assertEqual(pending["run"], 46140063118)
        self.assertEqual(pending["status"], "in_progress")
        self.assertFalse(MANIFEST["latest_main_verified_exact_sha"])

    def test_all_thirty_seed_refs_exist_but_are_not_ready(self):
        audit = MANIFEST["latest_30_seed_audit"]
        self.assertEqual(audit["current_main_sha"], "5513b8d005dc4f24bc496f9690607b2e94d9dd6e")
        self.assertEqual(audit["total_manifest_branches"], 30)
        self.assertEqual(audit["existing_branches"], 30)
        self.assertEqual(audit["distinct_branch_heads"], 30)
        self.assertEqual(audit["diverged"], 30)
        self.assertEqual(audit["ahead_only"], 0)
        self.assertEqual(audit["without_translator_or_tests"], [11, 12, 13, 14, 15])
        self.assertEqual(audit["workflow_noise_branches"], list(range(11, 31)))
        self.assertEqual(len(audit["branch_comparisons"]), 30)
        self.assertEqual(len({item["head_sha"] for item in audit["branch_comparisons"]}), 30)
        self.assertTrue(all(item["status"] == "diverged" for item in audit["branch_comparisons"]))
        self.assertEqual(MANIFEST["readiness"]["status"], "blocked")

    def test_30_seed_workflow_is_manual_and_never_promotes_automatically(self):
        workflow = (ROOT / ".github" / "workflows" / "failure-directed-30-seed-tournament.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("candidate_shas", workflow)
        self.assertNotIn("gh pr merge", workflow)
        self.assertFalse(MANIFEST["latest_30_seed_tournament_started"])

    def test_inspect_winner_promotion_has_exact_evidence(self):
        winner = MANIFEST["latest_winner_promotion"]
        self.assertTrue(winner["merged"])
        self.assertEqual(winner["pr"], 407)
        self.assertEqual(winner["base_sha"], "2dcf47bf3376289aca011ea98b84aa4b52c3956c")
        self.assertEqual(winner["merge_sha"], "f3bcea96c6eaee446453b0f463839e75ea412d72")
        self.assertEqual((winner["baseline_score"], winner["candidate_score"]), (263, 266))
        self.assertEqual(winner["new_passes"], 3)
        self.assertEqual(winner["regressions"], 0)
        self.assertEqual(winner["suite"], "success")

    def test_current_baseline_is_explicitly_last_verified_before_new_main_run(self):
        current = MANIFEST["current_baseline"]
        self.assertEqual((current["score"], current["source_run"]), (263, 46061895588))
        self.assertEqual(current["pending_current_main_sha"], "f3bcea96c6eaee446453b0f463839e75ea412d72")
        self.assertEqual(current["pending_run"], 46140063118)
        self.assertEqual(current["pending_status"], "in_progress")

    def test_pr408_ci_merge_did_not_change_translator(self):
        merged = MANIFEST["latest_duplicate_shard_suppression_merge"]
        self.assertEqual(merged["pr"], 408)
        self.assertTrue(merged["merged"])
        self.assertFalse(merged["translator_changed"])
        self.assertEqual(merged["merge_sha"], "5513b8d005dc4f24bc496f9690607b2e94d9dd6e")


if __name__ == "__main__":
    unittest.main()
