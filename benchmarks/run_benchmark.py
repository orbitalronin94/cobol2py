#!/usr/bin/env python3
"""Differential COBOL/Python benchmark against GnuCOBOL.

A case passes only when translated Python has the same stdout and exit status
as the compiled COBOL program. Mismatches are reported, not treated as a CI
infrastructure failure; this keeps the report useful while the translator is
still incomplete.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def run(command: list[str], *, timeout: int = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, check=False,
    )


def run_translator(translator: Path, source: Path, work: Path) -> dict[str, Any]:
    generated = work / (source.stem + ".py")
    try:
        result = run([sys.executable, str(translator), str(source), "--format", "auto"])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"matched": False, "reason": f"translator launch failed: {exc}"}
    if result.returncode != 0:
        return {
            "matched": False,
            "reason": f"translator exited {result.returncode}: {result.stderr.strip()[-500:]}",
        }
    generated.write_text(result.stdout, encoding="utf-8")
    try:
        executed = run([sys.executable, str(generated)])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"matched": False, "reason": f"translated Python failed to launch: {exc}"}
    return {
        "matched": executed.returncode == 0 and executed.stdout == work.joinpath("reference.out").read_text(encoding="utf-8"),
        "returncode": executed.returncode,
        "stdout": executed.stdout,
        "stderr": executed.stderr[-500:],
        "reason": None if executed.returncode == 0 and executed.stdout == work.joinpath("reference.out").read_text(encoding="utf-8")
                  else "stdout or exit status differs from GnuCOBOL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("benchmarks/cases.json"))
    parser.add_argument("--translator", type=Path, required=True, help="Candidate translator")
    parser.add_argument("--baseline-translator", type=Path, help="Optional previous-version translator")
    parser.add_argument("--json", dest="json_path", type=Path, default=Path("benchmark-report.json"))
    parser.add_argument("--markdown", type=Path, default=Path("benchmark-report.md"))
    parser.add_argument("--baseline-label", default="baseline")
    parser.add_argument("--candidate-label", default="candidate")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    cases = manifest.get("cases", [])
    if not cases:
        parser.error("manifest must contain at least one case")

    report: dict[str, Any] = {
        "schema_version": 1,
        "definition": "Exact stdout and zero exit status match against compiled GnuCOBOL",
        "baseline_label": args.baseline_label if args.baseline_translator else None,
        "candidate_label": args.candidate_label,
        "case_count": len(cases),
        "cases": [],
    }

    with tempfile.TemporaryDirectory(prefix="cobol2py-benchmark-") as tmp:
        root = Path(tmp)
        for case in cases:
            source = Path(case["path"])
            item: dict[str, Any] = {
                "id": case["id"], "path": str(source),
                "features": case.get("features", []),
            }
            with tempfile.TemporaryDirectory(dir=root, prefix=case["id"] + "-") as case_tmp:
                work = Path(case_tmp)
                try:
                    compile_result = run(["cobc", "-x", "-o", str(work / "reference"), str(source)])
                except (OSError, subprocess.TimeoutExpired) as exc:
                    compile_result = None
                    item["compile_error"] = str(exc)
                if compile_result is None or compile_result.returncode != 0:
                    item["compile_ok"] = False
                    item["compile_error"] = item.get("compile_error") or compile_result.stderr.strip()[-1000:]
                    item["baseline"] = {"matched": False, "reason": "COBOL reference did not compile"} if args.baseline_translator else None
                    item["candidate"] = {"matched": False, "reason": "COBOL reference did not compile"}
                    report["cases"].append(item)
                    continue

                reference = run([str(work / "reference")])
                item["compile_ok"] = True
                item["reference_returncode"] = reference.returncode
                (work / "reference.out").write_text(reference.stdout, encoding="utf-8")
                if args.baseline_translator:
                    item["baseline"] = run_translator(args.baseline_translator.resolve(), source.resolve(), work)
                    # Preserve reference output if translator execution changed no file; run_translator only reads it.
                else:
                    item["baseline"] = None
                item["candidate"] = run_translator(args.translator.resolve(), source.resolve(), work)
                # A non-zero COBOL exit is still a valid reference; require exact return-code agreement.
                for key in ("baseline", "candidate"):
                    result = item.get(key)
                    if result is not None:
                        result["matched"] = bool(
                            result.get("matched")
                            and result.get("returncode") == reference.returncode
                        )
                report["cases"].append(item)

    def summary(key: str) -> dict[str, int | float]:
        results = [case[key] for case in report["cases"] if case.get(key) is not None]
        passed = sum(1 for result in results if result.get("matched"))
        total = len(results)
        return {"passed": passed, "total": total, "percent": round(100 * passed / total, 2) if total else 0.0}

    report["baseline_summary"] = summary("baseline") if args.baseline_translator else None
    report["candidate_summary"] = summary("candidate")
    if args.baseline_translator:
        report["delta_percentage_points"] = round(
            report["candidate_summary"]["percent"] - report["baseline_summary"]["percent"], 2
        )
    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    args.json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# COBOL → Python differential benchmark",
        "",
        f"> **Pass definition:** exact standard-output match and matching process exit status against compiled GnuCOBOL. "
        f"Suite size: **{len(cases)} programs**. This is a corpus score, not a claim of general COBOL equivalence.",
        "",
        "| Version | Exact matches | Corpus pass rate |",
        "|---|---:|---:|",
    ]
    if args.baseline_translator:
        base = report["baseline_summary"]
        lines.append(f"| {args.baseline_label} | {base['passed']}/{base['total']} | {base['percent']:.2f}% |")
    cand = report["candidate_summary"]
    lines.append(f"| {args.candidate_label} | {cand['passed']}/{cand['total']} | {cand['percent']:.2f}% |")
    if args.baseline_translator:
        delta = report["delta_percentage_points"]
        lines.extend(["", f"**Change:** {delta:+.2f} percentage points on the same current corpus."])
    lines.extend(["", "## Per-program results", "", "| Program | Features | Baseline | Candidate | Detail |", "|---|---|---:|---:|---|"])
    for case in report["cases"]:
        def mark(result: dict[str, Any] | None) -> str:
            if result is None:
                return "—"
            return "PASS" if result.get("matched") else "FAIL"
        base_mark = mark(case.get("baseline"))
        candidate_mark = mark(case.get("candidate"))
        reasons = []
        if not case.get("compile_ok"):
            reasons.append("GnuCOBOL compile failed: " + case.get("compile_error", "unknown error"))
        for version in ("baseline", "candidate"):
            result = case.get(version)
            if result and not result.get("matched") and result.get("reason"):
                reasons.append(f"{version}: {result['reason']}")
        detail = "; ".join(reasons).replace("|", "\\|") or "Exact match"
        features = ", ".join(case.get("features", []))
        lines.append(f"| `{case['id']}` | {features} | {base_mark} | {candidate_mark} | {detail} |")
    lines.extend([
        "", "## Interpretation", "",
        "- A pass means only that this fixture's stdout and exit status match the installed GnuCOBOL reference.",
        "- Compile errors, translator errors, runtime errors, and output differences count as failures.",
        "- The baseline and candidate use the same manifest from the tested commit, so the comparison is paired.",
        "- Add new representative fixtures to `benchmarks/cases.json`; do not remove or weaken old cases merely to improve the score.",
        "",
    ])
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"benchmark infrastructure error: {exc}", file=sys.stderr)
        raise SystemExit(2)
