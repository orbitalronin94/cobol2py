import unittest

from benchmarks.holdout_topography import build_topography, render_markdown


def report(skip, items):
    return {
        "dataset": "X-COBOL v2",
        "archive_md5_verified": True,
        "skip": skip,
        "target": 125,
        "tested": 125,
        "sample_complete": True,
        "passed": sum(item["status"] == "passed" for item in items),
        "failed": sum(item["status"] != "passed" for item in items),
        "pass_rate_percent": round(100 * sum(item["status"] == "passed" for item in items) / 125, 2),
        "results": items,
    }


class HoldoutTopographyTests(unittest.TestCase):
    def test_aggregates_exact_score_and_feature_failure_rates(self):
        shards = []
        skips = [500, 625, 750, 875]
        for index, skip in enumerate(skips):
            items = []
            for number in range(125):
                passed = number < 100
                items.append({
                    "id": f"{index}-{number}",
                    "status": "passed" if passed else "failed",
                    "reason": None if passed else "stdout or return code differs from GnuCOBOL",
                    "candidate_exception_type": None if passed else "KeyError",
                    "source_features": ["CALL", "FILE_IO"] if number % 2 == 0 else ["PERFORM"],
                    "source_sha256": f"{index}-{number}",
                })
            shards.append(report(skip, items))
        result = build_topography(shards, "abc123")
        self.assertEqual(result["holdout"], {
            "tested": 500, "passed": 400, "failed": 100, "pass_rate_percent": 80.0
        })
        features = {item["feature"]: item for item in result["feature_topography"]}
        self.assertEqual(features["CALL"]["tested"], 252)
        self.assertEqual(features["CALL"]["failed"], 52)
        self.assertEqual(result["exception_types"], {"KeyError": 100})
        self.assertIn("not proven root causes", result["interpretation"])
        self.assertIn("400/500", render_markdown(result))

    def test_rejects_duplicate_case_ids(self):
        item = {"id": "duplicate", "status": "passed", "source_features": []}
        shards = [report(skip, [item] * 125) for skip in [500, 625, 750, 875]]
        with self.assertRaises(ValueError):
            build_topography(shards)


if __name__ == "__main__":
    unittest.main()
