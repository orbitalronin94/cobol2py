#!/usr/bin/env python3
"""Aggregate the four fixed X-COBOL holdout shards into an error topography.

Feature tags are conservative source-pattern associations, not causal claims.
Only report metadata and stable case IDs are emitted; third-party source is not copied.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EXPECTED_SHARDS = {"holdout-0": 500, "holdout-1": 625, "holdout-2": 750, "holdout-3": 875}
SHARD_SIZE = 125
EXPECTED_TOTAL = 500


def load_shards(directory: Path) -> list[dict[str, Any]]:
    reports = []
    for shard, skip in EXPECTED_SHARDS.items():
        path = directory / shard / "external-corpus-report.json"
        if not path.is_file():
            raise ValueError(f"Missing required shard report: {path}")
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("skip") != skip or report.get("target") != SHARD_SIZE:
            raise ValueError(f"Unexpected selection parameters in {path}")
        if report.get("archive_md5_verified") is not True or report.get("sample_complete") is not True:
            raise ValueError(f"Incomplete or unverified shard: {path}")
        if report.get("tested") != SHARD_SIZE or len(report.get("results", [])) != SHARD_SIZE:
            raise ValueError(f"Shard does not contain exactly {SHARD_SIZE} tested cases: {path}")
        reports.append(report)
    return reports


def build_topography(reports: list[dict[str, Any]], candidate_sha: str = "unknown") -> dict[str, Any]:
    results = [item for report in reports for item in report["results"]]
    ids = [item["id"] for item in results]
    if len(results) != EXPECTED_TOTAL or len(set(ids)) != EXPECTED_TOTAL:
        raise ValueError("Holdout must contain exactly 500 unique tested case IDs")
    passed = [item for item in results if item.get("status") == "passed"]
    failed = [item for item in results if item.get("status") != "passed"]
    reason_counts = Counter(item.get("reason") or "unspecified failure" for item in failed)
    exception_counts = Counter(item.get("candidate_exception_type") for item in failed if item.get("candidate_exception_type"))
    feature_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"tested": 0, "passed": 0, "failed": 0})
    for item in results:
        for feature in item.get("source_features", []):
            stats = feature_stats[feature]
            stats["tested"] += 1
            stats["passed" if item.get("status") == "passed" else "failed"] += 1
    features = []
    for name, stats in feature_stats.items():
        features.append({
            "feature": name, **stats,
            "pass_rate_percent": round(100 * stats["passed"] / stats["tested"], 2),
            "failure_rate_percent": round(100 * stats["failed"] / stats["tested"], 2),
        })
    features.sort(key=lambda item: (-item["failed"], -item["tested"], item["feature"]))
    categories = Counter()
    for item in failed:
        reason = (item.get("reason") or "").lower()
        if "syntax error" in reason or "syntax" in reason:
            category = "generated_python_syntax"
        elif "translator timeout" in reason:
            category = "translator_timeout"
        elif "timed out" in reason:
            category = "translated_program_timeout"
        elif "capture limit" in reason or "exceeded capture" in reason:
            category = "output_capture_limit"
        elif "could not launch" in reason or "launch" in reason:
            category = "launch_failure"
        elif "differs from gnucobol" in reason:
            category = "stdout_or_returncode_mismatch"
        else:
            category = "other"
        categories[category] += 1
    return {
        "schema_version": 1,
        "dataset": reports[0].get("dataset"),
        "archive_md5_verified": all(r.get("archive_md5_verified") is True for r in reports),
        "candidate_sha": candidate_sha,
        "holdout": {"tested": len(results), "passed": len(passed), "failed": len(failed),
                    "pass_rate_percent": round(100 * len(passed) / len(results), 2)},
        "shards": [{"skip": r["skip"], "target": r["target"], "passed": r["passed"],
                    "failed": r["failed"], "pass_rate_percent": r["pass_rate_percent"]} for r in reports],
        "failure_categories": dict(sorted(categories.items())),
        "failure_reasons": dict(reason_counts.most_common()),
        "exception_types": dict(exception_counts.most_common()),
        "feature_topography": features,
        "failed_cases": [{
            "id": item.get("id"), "reason": item.get("reason"),
            "exception_type": item.get("candidate_exception_type"),
            "missing_name": item.get("candidate_missing_name"),
            "error_line": item.get("candidate_error_line"),
            "source_features": item.get("source_features", []),
            "source_sha256": item.get("source_sha256"),
        } for item in failed],
        "interpretation": (
            "Feature associations are based on conservative source-pattern detection. "
            "They describe where failures occur, not proven root causes. Confirm causes "
            "with GnuCOBOL traces and minimal reproducible fixtures."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    holdout = report["holdout"]
    lines = [
        "# X-COBOL v2 — Holdout error topography", "",
        f"- Candidate SHA: `{report['candidate_sha']}`",
        f"- Archive checksum verified: **{report['archive_md5_verified']}**",
        f"- Exact GnuCOBOL matches: **{holdout['passed']}/{holdout['tested']} ({holdout['pass_rate_percent']:.2f}%)**",
        f"- Failures: **{holdout['failed']}**", "",
        "## Four-shard scorecard", "",
        "| Shard | Skip | Passed | Failed | Exact-match rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for shard in report["shards"]:
        lines.append(f"| holdout-{shard['skip']} | {shard['skip']} | {shard['passed']} | {shard['failed']} | {shard['pass_rate_percent']:.2f}% |")
    lines.extend(["", "## Failure categories", "", "| Category | Cases |", "|---|---:|"])
    for name, count in report["failure_categories"].items():
        lines.append(f"| {name} | {count} |")
    lines.extend(["", "## Exception classes", "", "| Exception | Cases |", "|---|---:|"])
    for name, count in report["exception_types"].items():
        lines.append(f"| {name} | {count} |")
    lines.extend(["", "## COBOL feature topography", "",
        "Associations only; a feature appearing in a failing program does not prove it caused the failure.",
        "", "| Feature | Tested | Failed | Failure rate | Passed |", "|---|---:|---:|---:|---:|"])
    for item in report["feature_topography"]:
        lines.append(f"| {item['feature']} | {item['tested']} | {item['failed']} | {item['failure_rate_percent']:.2f}% | {item['passed']} |")
    lines.extend(["", "## Failed case index", "", "| Case ID | Failure | Exception | Feature tags |", "|---|---|---|---|"])
    for item in report["failed_cases"]:
        reason = (item.get("reason") or "").replace("|", "\\|")
        tags = ", ".join(item.get("source_features", []))
        lines.append(f"| {item['id']} | {reason} | {item.get('exception_type') or '—'} | {tags} |")
    lines.extend(["", "## Interpretation", "", report["interpretation"], "",
        "The score uses exact stdout bytes and exact process return code against GnuCOBOL. "
        "No whitespace normalization or denominator adjustment is applied.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, required=True, help="Directory containing four holdout-N shard folders")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-sha", default="unknown")
    args = parser.parse_args()
    reports = load_shards(args.reports)
    result = build_topography(reports, args.candidate_sha)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "holdout-topography.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output / "holdout-topography.md").write_text(render_markdown(result), encoding="utf-8")
    print(render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
