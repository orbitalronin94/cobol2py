"""Regression guard for the highest validated external exact-match score."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "benchmarks" / "best-score.json"


class BestScoreRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
        cls.best = cls.record["best"]

    def test_record_keeps_the_validated_414_baseline_or_a_strictly_better_one(self):
        self.assertEqual(self.record["corpus"], "X-COBOL-v2")
        self.assertEqual(self.record["sample_size"], 500)
        self.assertEqual(self.record["holdout_size"], 500)
        self.assertEqual(
            self.record["exact_match"],
            "stdout-byte-for-byte-and-exit-code",
        )
        self.assertEqual(
            self.best["score"],
            self.best["primary"] + self.best["holdout"],
        )
        self.assertGreaterEqual(self.best["score"], 414)
        self.assertGreaterEqual(self.best["primary"], 197)
        self.assertGreaterEqual(self.best["holdout"], 217)
        self.assertEqual(self.best["percent"], round(self.best["score"] / 10, 2))
        self.assertEqual(self.record["acceptance_target_each_sample"], 375)
        self.assertTrue(self.best["measured_sha"])
        self.assertTrue(self.best["run_url"])

    def test_previous_validated_best_is_retained_in_history(self):
        history = self.record.get("history", [])
        self.assertTrue(history, "the previous validated score must not be discarded")
        previous = next(
            (item for item in history if item.get("benchmark_run") == 41107706787),
            None,
        )
        self.assertIsNotNone(previous)
        self.assertEqual(previous["score"], 411)
        for item in history:
            self.assertEqual(item["score"], item["primary"] + item["holdout"])
            self.assertEqual(item["percent"], round(item["score"] / 10, 2))
            self.assertLessEqual(item["score"], self.best["score"])


if __name__ == "__main__":
    unittest.main()
