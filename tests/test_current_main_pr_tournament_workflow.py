import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github" / "workflows" / "current-main-pr-tournament.yml").read_text(
    encoding="utf-8"
)


class CurrentMainPRTournamentWorkflowTests(unittest.TestCase):
    def test_manual_candidate_list_is_optional_and_has_no_stale_default(self):
        block = WORKFLOW.split("candidate_prs:", 1)[1].split("max_parallel:", 1)[0]
        self.assertIn("required: false", block)
        self.assertIn('default: ""', block)
        self.assertNotIn('default: "371"', block)
        self.assertNotIn("|| '371'", WORKFLOW)

    def test_schedule_and_push_discover_all_open_prs_when_no_list_is_supplied(self):
        self.assertIn("REQUESTED_PRS: ${{ github.event.pull_request.number || inputs.candidate_prs || '' }}", WORKFLOW)
        self.assertIn("mapfile -t prs", WORKFLOW)
        self.assertIn('gh api --paginate "repos/$GITHUB_REPOSITORY/pulls?state=open&per_page=100"', WORKFLOW)
        self.assertIn("for raw in \"${prs[@]}\"; do", WORKFLOW)

    def test_auto_discovery_keeps_the_existing_strict_candidate_gates(self):
        self.assertIn('if [ "$comparison_status" != "ahead" ]', WORKFLOW)
        self.assertIn("has no translator implementation change", WORKFLOW)
        self.assertIn("has no regression test/reproducer change", WORKFLOW)
        self.assertIn("contains unrelated changes outside translator/tests", WORKFLOW)
        self.assertIn("baseline_sha", WORKFLOW)
        self.assertIn("Run exact 500-case baseline", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
