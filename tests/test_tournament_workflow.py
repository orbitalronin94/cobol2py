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

    def test_current_main_pr_tournament_scores_against_frozen_main_oracle(self):
        for field in (
            "reference_stdout_sha256", "reference_stdout_length", "reference_returncode",
            "source_sha256", "candidate_stdout_sha256", "candidate_stdout_length",
            "candidate_returncode",
        ):
            self.assertIn(field, CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("baseline_reference", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("candidate_pass = (", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("oracle_drift", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("comparable_cases = sorted(base)", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("eligible_candidate = len(new_passes) >= 1 and not regressions", CURRENT_MAIN_PR_WORKFLOW)
        self.assertNotIn("eligible_candidate = oracle_stable", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("actual_merge_sha", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn('[ "$base_ref" != "main" ]', CURRENT_MAIN_PR_WORKFLOW)

    def test_current_main_pr_tournament_runs_on_protocol_push_and_daily(self):
        self.assertIn("push:", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn(".github/workflows/current-main-pr-tournament.yml", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn('cron: "30 11 * * *"', CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("inputs.candidate_prs || '395'", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("workflow_dispatch:", CURRENT_MAIN_PR_WORKFLOW)

    def test_30_seed_tournament_scores_against_frozen_main_oracle(self):
        for field in (
            "source_sha256", "baseline_sources", "source_map", "source_drift",
            "candidate_stdout_sha256", "candidate_stdout_length", "candidate_returncode",
            "baseline_reference", "candidate_pass",
        ):
            self.assertIn(field, FAILURE_30_WORKFLOW)
        self.assertIn('reference_stdout_truncated") is not False', FAILURE_30_WORKFLOW)
        self.assertIn("comparable_cases = sorted(base)", FAILURE_30_WORKFLOW)
        self.assertIn("eligible_candidate = len(new_passes) >= 1 and not regressions", FAILURE_30_WORKFLOW)
        self.assertNotIn("eligible_candidate = oracle_stable", FAILURE_30_WORKFLOW)

    def test_workflow_never_merges_or_updates_benchmark_record(self):
        self.assertIn("No PR is merged", WORKFLOW)
        self.assertIn("benchmark record is not changed", WORKFLOW)


    def test_current_main_pr_tournament_rejects_unrelated_candidate_changes(self):
        self.assertIn("Enforce isolation", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("translator implementation change", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("regression test/reproducer change", CURRENT_MAIN_PR_WORKFLOW)

    def test_30_seed_tournament_rejects_unrelated_candidate_changes(self):
        self.assertIn("Enforce isolation", FAILURE_30_WORKFLOW)
        self.assertIn("contains unrelated changes", FAILURE_30_WORKFLOW)


    def test_current_main_pr_tournament_allows_baseline_only_without_candidates(self):
        self.assertIn("No eligible candidate PRs; continuing with a baseline-only 500-case run.", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("if: needs.discover.outputs.candidates != '[]'", CURRENT_MAIN_PR_WORKFLOW)
        self.assertNotIn('echo "::error::No open, mergeable PRs were found.', CURRENT_MAIN_PR_WORKFLOW)

    def test_current_main_pr_tournament_summary_escapes_shell_backticks(self):
        self.assertIn("printf '%s\\n'", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("\\`$baseline_sha\\`", CURRENT_MAIN_PR_WORKFLOW)
        self.assertNotIn('echo "- Current main: `$baseline_sha`"', CURRENT_MAIN_PR_WORKFLOW)

    def test_current_main_pr_tournament_handles_flat_single_artifact_downloads(self):
        self.assertIn('root.rglob("external-corpus-report.json")', CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn('root.rglob("candidate-result.json")', CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn('path.parent == root', CURRENT_MAIN_PR_WORKFLOW)

    def test_current_main_pr_tournament_python_heredoc_indentation_is_valid(self):
        self.assertIn(
            '          baseline_files = [\n              path for path in root.rglob("external-corpus-report.json")\n              if path.parent == root or path.parent.name.startswith("pr-tournament-baseline-")\n          ]',
            CURRENT_MAIN_PR_WORKFLOW,
        )

    def test_current_main_pr_tournament_runs_on_candidate_pr_updates(self):
        self.assertIn("pull_request:", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("types: [opened, synchronize, reopened]", CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn('"cobol2py.py"', CURRENT_MAIN_PR_WORKFLOW)
        self.assertNotIn('"tests/**"', CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn('"web/index.html"', CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn('"ronin/**"', CURRENT_MAIN_PR_WORKFLOW)
        self.assertIn("REQUESTED_PRS: ${{ github.event.pull_request.number || inputs.candidate_prs || '395' }}", CURRENT_MAIN_PR_WORKFLOW)

    def test_current_main_pr_tournament_defaults_to_rebuilt_candidate(self):
        self.assertIn("inputs.candidate_prs || \'395\'", CURRENT_MAIN_PR_WORKFLOW)

    def test_legacy_16_candidate_tournament_is_manual_only_until_rebuilt(self):
        trigger_section = WORKFLOW.split("permissions:", 1)[0]
        self.assertIn("workflow_dispatch:", trigger_section)
        self.assertNotIn("\n  push:", trigger_section)

if __name__ == "__main__":
    unittest.main()

    def test_current_main_pr_tournament_concurrency_is_scoped_per_pr_and_main(self):
        self.assertIn(
            "group: ${{ github.event.pull_request.number && format('cobol2py-current-main-pr-tournament-pr-{0}', github.event.pull_request.number) || 'cobol2py-current-main-pr-tournament' }}",
            CURRENT_MAIN_PR_WORKFLOW,
        )
        self.assertIn("cancel-in-progress: true", CURRENT_MAIN_PR_WORKFLOW)

    def test_current_main_pr_tournament_runs_when_translator_regression_tests_change(self):
        self.assertIn('      - "tests/test_cobol2py.py"', CURRENT_MAIN_PR_WORKFLOW)
