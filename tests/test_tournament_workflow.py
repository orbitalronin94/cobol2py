import json
import unittest
from pathlib import Path


MANIFEST = json.loads(
    (Path(__file__).resolve().parents[1] / "experiments" / "massive-cohorts" / "16" / "manifest.json").read_text(encoding="utf-8")
)

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "seven-candidate-tournament.yml"
).read_text(encoding="utf-8")

CURRENT_MAIN_PR_WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "current-main-pr-tournament.yml"
).read_text(encoding="utf-8")

FAILURE_30_WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "failure-directed-30-seed-tournament.yml"
).read_text(encoding="utf-8")


class MassiveTournamentWorkflowContractTests(unittest.TestCase):
    def test_dispatch_has_safe_default_and_allowed_cohort_sizes(self):
        self.assertIn('batch_size="${{ inputs.cohort_size || \'16\' }}"', WORKFLOW)
        self.assertIn('case "$batch_size" in', WORKFLOW)
        self.assertIn("16|32|64|100)", WORKFLOW)

    def test_candidate_output_is_single_line_json(self):
        self.assertIn("candidates=$(jq -cn --arg main_sha", WORKFLOW)
        self.assertIn('--slurpfile pulls "$RUNNER_TEMP/open-pulls.json"', WORKFLOW)
        self.assertIn("$pulls[0][]", WORKFLOW)
        self.assertNotIn("previous-main-baseline", WORKFLOW)
        self.assertIn('{name:"main-baseline",branch:"main",sha:$main_sha,pr:0}', WORKFLOW)
        self.assertIn('echo "candidates=$candidates" >> "$GITHUB_OUTPUT"', WORKFLOW)

    def test_push_discovery_includes_massive_experiment_branches(self):
        self.assertIn("experiments/massive-cohorts/16/manifest.json", WORKFLOW)
        self.assertIn("$manifest[0].candidates", WORKFLOW)

    def test_manifest_has_seventeen_entries_and_fifteen_unmerged_candidates(self):
        candidates = MANIFEST["candidates"]
        active = [candidate for candidate in candidates if candidate.get("merged") is not True]
        branches = [candidate["branch"] for candidate in active]
        self.assertEqual(len(candidates), 17)
        self.assertEqual(len(active), 15)
        self.assertEqual(len(set(branches)), 15)
        self.assertTrue(all(branch.startswith("experiment-massive-16/") for branch in branches))

    def test_both_fixed_disjoint_samples_are_evaluated(self):
        self.assertIn("- { name: primary, skip: 0 }", WORKFLOW)
        self.assertIn("- { name: holdout, skip: 500 }", WORKFLOW)

    def test_aggregate_requires_paired_casewise_zero_regressions(self):
        self.assertIn('required_samples = ("primary", "holdout")', WORKFLOW)
        self.assertIn('report.get("archive_md5_verified") is True', WORKFLOW)
        self.assertIn('row["regressions"] == 0', WORKFLOW)
        self.assertIn('row["combined"] > baseline_total', WORKFLOW)

    def test_current_main_pr_tournament_requires_stable_oracle_and_exact_source_ids(self):
        for field in ("reference_stdout_sha256", "reference_stdout_length", "reference_returncode", "source_sha256"):
            self.assertIn(field, CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("oracle_drift", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("oracle_stable = not oracle_drift", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("eligible_candidate = oracle_stable", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("actual_merge_sha", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn('[ "$base_ref" != "main" ]', CURRENT_MAIN_PR_WORKFLOW)

    def test_30_seed_tournament_requires_source_identity_and_untruncated_oracle(self):
        self.assertIn("source_sha256", FAILURE_30_WORKFLOW)
        self.assertIn("baseline_sources", FAILURE_30_WORKFLOW)
        self.assertIn("source_map", FAILURE_30_WORKFLOW)
        self.assertIn("source_drift", FAILURE_30_WORKFLOW)
        self.assertIn('reference_stdout_truncated") is not False', FAILURE_30_WORKFLOW)

    def test_workflow_never_merges_or_updates_benchmark_record(self):
        self.assertIn("No PR is merged", WORKFLOW)
        self.assertIn("benchmark record is not changed", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
