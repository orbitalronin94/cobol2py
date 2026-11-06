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

    def test_frozen_holdout_baseline_and_zero_regression_gate(self):
        self.assertEqual(MANIFEST["baseline"]["score"], 258)
        self.assertEqual(MANIFEST["baseline"]["denominator"], 500)
        self.assertEqual(MANIFEST["baseline"]["percent"], 51.6)
        self.assertEqual(MANIFEST["benchmark"]["skip"], 500)
        self.assertEqual(MANIFEST["benchmark"]["target"], 500)
        self.assertEqual(MANIFEST["acceptance"]["regressions_allowed"], 0)
        self.assertTrue(MANIFEST["acceptance"]["complete_holdout_required"])

    def test_every_candidate_is_a_single_named_hypothesis(self):
        for candidate in MANIFEST["candidates"]:
            with self.subTest(seed=candidate["seed"]):
                self.assertTrue(candidate["id"])
                self.assertTrue(candidate["hypothesis"].endswith(".") or candidate["hypothesis"].endswith("behavior."))
                self.assertTrue(candidate["branch"].startswith("experiment-failure-seed/"))


if __name__ == "__main__":
    unittest.main()
