#!/usr/bin/env python3
"""Paired external-corpus differential benchmark for Python, C, and Rust."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# Import the existing, audited archive extraction and bounded process helpers.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_external_corpus import (  # noqa: E402
    ARCHIVE_MD5, extract_archive, run_process, sha256_file, case_id, stdout_matches,
)

ROOT = Path(__file__).resolve().parents[1]


def safe_reason(language: str, stage: str, process: dict[str, Any]) -> str:
    """Return a fixed, non-source-bearing diagnostic for external corpus artifacts."""
    if process.get("timeout"):
        return stage + " timeout"
    if not process.get("launched"):
        return stage + " could not launch"
    if process.get("stdout_truncated"):
        return stage + " output exceeded capture limit"
    if stage == "translation":
        stderr = process.get("stderr", "")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        if language in ("c", "rust") and "cobol2native:" in stderr:
            return "unsupported construct or native translation rejection"
        return "translator exited unsuccessfully"
    if stage == "compilation":
        return language + " compilation failed"
    return stage + " failed"


def run_language(language: str, source: Path, reference: dict[str, Any], work: Path,
                 compile_timeout: int, run_timeout: int, translator_timeout: int) -> dict[str, Any]:
    if language == "python":
        command = ["python3", "-I", str(ROOT / "cobol2py.py"), str(source), "--format", "auto"]
        suffix = ".py"
    else:
        command = ["python3", str(ROOT / "cobol2native.py"), str(source), "--lang", language, "--source-format", "auto"]
        suffix = ".c" if language == "c" else ".rs"

    translated = run_process(command, work, translator_timeout)
    result: dict[str, Any] = {"matched": False}
    if (not translated.get("launched") or translated.get("timeout")
            or translated.get("stdout_truncated") or translated.get("returncode") != 0):
        result["reason"] = safe_reason(language, "translation", translated)
        return result

    generated = work / ("translated" + suffix)
    generated.write_text(translated["stdout"], encoding="utf-8")
    if language == "python":
        try:
            compile(translated["stdout"], str(generated), "exec")
        except SyntaxError:
            result["reason"] = "generated Python syntax error"
            return result
        executable = ["python3", "-I", str(generated)]
    elif language == "c":
        executable_path = work / "translated-c"
        compiled = run_process(["cc", "-std=c11", "-w", str(generated), "-o", str(executable_path)], work, compile_timeout)
        if not compiled.get("launched") or compiled.get("timeout") or compiled.get("returncode") != 0:
            result["reason"] = safe_reason(language, "compilation", compiled)
            return result
        executable = [str(executable_path)]
    else:
        executable_path = work / "translated-rust"
        compiled = run_process(["rustc", str(generated), "-o", str(executable_path)], work, compile_timeout)
        if not compiled.get("launched") or compiled.get("timeout") or compiled.get("returncode") != 0:
            result["reason"] = safe_reason(language, "compilation", compiled)
            return result
        executable = [str(executable_path)]

    actual = run_process(executable, work, run_timeout)
    match = (
        actual.get("launched") and not actual.get("timeout")
        and not actual.get("stdout_truncated") and not reference.get("stdout_truncated")
        and stdout_matches(actual, reference)
        and actual.get("returncode") == reference.get("returncode")
    )
    result.update({
        "matched": bool(match),
        "stdout_match": stdout_matches(actual, reference),
        "returncode_match": actual.get("returncode") == reference.get("returncode"),
        "candidate_returncode": actual.get("returncode"),
    })
    if not match:
        if actual.get("timeout"):
            result["reason"] = "translated program timeout"
        elif not actual.get("launched"):
            result["reason"] = "translated program could not launch"
        elif actual.get("stdout_truncated") or reference.get("stdout_truncated"):
            result["reason"] = "output exceeded capture limit"
        else:
            result["reason"] = "stdout or return code mismatch"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target", type=int, default=500)
    parser.add_argument("--skip", type=int, default=0)
    parser.add_argument("--compile-timeout", type=int, default=8)
    parser.add_argument("--run-timeout", type=int, default=3)
    parser.add_argument("--translator-timeout", type=int, default=20)
    args = parser.parse_args()
    if args.target < 1 or args.skip < 0:
        parser.error("--target must be positive and --skip non-negative")
    for tool in ("cobc", "cc", "rustc", "python3"):
        if shutil.which(tool) is None:
            parser.error("required tool not found on PATH: " + tool)
    args.output.mkdir(parents=True, exist_ok=True)
    languages = ("python", "c", "rust")
    per_language: dict[str, list[dict[str, Any]]] = {lang: [] for lang in languages}
    report: dict[str, Any] = {
        "schema_version": 1,
        "dataset": "X-COBOL: A Dataset of Open-Source COBOL repositories, v2",
        "dataset_url": "https://zenodo.org/records/14269462",
        "archive_md5_expected": ARCHIVE_MD5,
        "archive_md5_verified": False,
        "selection": "Deterministic SHA-256 ordering of unique source contents; eligible programs must compile and terminate under GnuCOBOL.",
        "pass_definition": "Exact stdout byte stream and process return-code match against GnuCOBOL.",
        "target_per_language": args.target,
        "skip_eligible_programs": args.skip,
        "source_files_discovered": 0,
        "unique_source_contents": 0,
        "screened": 0,
        "eligible_skipped": 0,
        "reference_compile_failures": 0,
        "reference_runtime_exclusions": 0,
        "tested": 0,
        "results": [],
    }
    with tempfile.TemporaryDirectory(prefix="x-cobol-multilang-") as temp:
        temp_root = Path(temp)
        extracted_root = temp_root / "source"
        sources = extract_archive(args.archive.resolve(), extracted_root)
        report["archive_md5_verified"] = True
        report["source_files_discovered"] = len(sources)
        unique: dict[str, Path] = {}
        for source in sources:
            unique.setdefault(sha256_file(source), source)
        report["unique_source_contents"] = len(unique)
        ordered = sorted(unique.items(), key=lambda pair: hashlib.sha256(
            (pair[1].relative_to(extracted_root).as_posix() + "\0" + pair[0]).encode("utf-8")).hexdigest())
        eligible_seen = 0
        for content_hash, source in ordered:
            if report["tested"] >= args.target:
                break
            report["screened"] += 1
            relative = source.relative_to(extracted_root).as_posix()
            item: dict[str, Any] = {
                "id": case_id(relative, content_hash),
                "source": relative,
                "source_sha256": content_hash,
                "reference_compile": "pending",
                "status": {},
            }
            print("CASE START screened=" + str(report["screened"]) + " id=" + item["id"], flush=True)
            with tempfile.TemporaryDirectory(dir=temp_root, prefix="case-") as case_dir:
                case_root = Path(case_dir)
                ref_work = case_root / "reference"
                ref_work.mkdir()
                executable = ref_work / "reference"
                compiled = run_process(["cobc", "-x", "-I", str(source.parent), "-o", str(executable), str(source)],
                                       ref_work, args.compile_timeout)
                if not compiled.get("launched") or compiled.get("timeout") or compiled.get("returncode") != 0:
                    report["reference_compile_failures"] += 1
                    item["reference_compile"] = "failed"
                    item["reason"] = "GnuCOBOL reference compilation failed"
                    report["results"].append(item)
                    continue
                item["reference_compile"] = "passed"
                reference = run_process([str(executable)], ref_work, args.run_timeout)
                if not reference.get("launched") or reference.get("timeout"):
                    report["reference_runtime_exclusions"] += 1
                    item["reason"] = "GnuCOBOL reference timed out or could not launch"
                    report["results"].append(item)
                    continue
                if eligible_seen < args.skip:
                    eligible_seen += 1
                    report["eligible_skipped"] = eligible_seen
                    continue
                eligible_seen += 1
                for language in languages:
                    work = case_root / language
                    work.mkdir()
                    item["status"][language] = run_language(
                        language, source, reference, work, args.compile_timeout,
                        args.run_timeout, args.translator_timeout)
                    per_language[language].append({"id": item["id"], **item["status"][language]})
                report["results"].append(item)
                report["tested"] += 1
                if report["tested"] % 25 == 0:
                    print("PROGRESS tested=" + str(report["tested"]) + "/" + str(args.target), flush=True)

    report["sample_complete"] = report["tested"] == args.target
    report["languages"] = {}
    for language, results in per_language.items():
        passed = sum(bool(result.get("matched")) for result in results)
        failures: dict[str, int] = {}
        for result in results:
            if not result.get("matched"):
                reason = result.get("reason", "unknown failure")
                failures[reason] = failures.get(reason, 0) + 1
        report["languages"][language] = {
            "passed": passed, "total": len(results),
            "percent": round(100 * passed / len(results), 2) if results else 0.0,
            "failures_by_reason": dict(sorted(failures.items(), key=lambda pair: (-pair[1], pair[0]))),
        }
    report["source_code_republished"] = False
    report["notes"] = [
        "Only sources that compile and terminate under GnuCOBOL enter the denominator.",
        "Reference compile failures and reference timeouts are reported separately, not counted as translator failures.",
        "The same eligible sample, GnuCOBOL output, timeout and exact-match rule are used for all three languages.",
        "Only source hashes, archive-relative paths, and aggregate diagnostics are published; third-party source text and program output are not published.",
        "The native backends support an experimental subset; unsupported constructs intentionally count as failures.",
    ]
    json_path = args.output / "external-multilang-report.json"
    md_path = args.output / "external-multilang-report.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# External COBOL three-language differential benchmark", "",
        "- Dataset: [X-COBOL v2](https://zenodo.org/records/14269462)",
        "- Archive checksum verified: " + str(report["archive_md5_verified"]),
        "- Source files discovered: " + str(report["source_files_discovered"]) + "; unique contents: " + str(report["unique_source_contents"]),
        "- Candidates screened: " + str(report["screened"]),
        "- Reference compile failures: " + str(report["reference_compile_failures"]),
        "- Reference runtime exclusions: " + str(report["reference_runtime_exclusions"]),
        "- Eligible sample: " + str(report["tested"]) + "/" + str(args.target),
        "- Sample complete: " + str(report["sample_complete"]), "",
        "| Backend | Exact matches | Pass rate |", "|---|---:|---:|",
    ]
    for language in languages:
        summary = report["languages"][language]
        lines.append("| " + language + " | " + str(summary["passed"]) + "/" + str(summary["total"]) + " | " + format(summary["percent"], ".2f") + "% |")
    lines.extend(["", "## Failure families", ""])
    for language in languages:
        lines.extend(["### " + language, ""])
        for reason, count in list(report["languages"][language]["failures_by_reason"].items())[:12]:
            lines.append("- **" + str(count) + "** — " + reason)
        lines.append("")
    lines.extend(["## Per-program results", "", "| Case | Python | C | Rust |", "|---|---:|---:|---:|"])
    for item in report["results"]:
        if "status" not in item or not item["status"]:
            continue
        marks = [("PASS" if item["status"].get(lang, {}).get("matched") else "FAIL") for lang in languages]
        lines.append("| " + item["id"] + " | " + marks[0] + " | " + marks[1] + " | " + marks[2] + " |")
    lines.extend(["", "## Interpretation", "",
        "- Percentages are directly comparable because all three backends use the same selected source programs and GnuCOBOL oracle.",
        "- The score measures only this deterministic external sample; it is not universal COBOL compatibility.",
        "- A native pass with a Python failure is a candidate for cross-backend diagnosis, but GnuCOBOL remains the semantic oracle.",
        "- The sample is a baseline measurement, not a regression gate; a non-100% score still produces a report.", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:20]))
    print("\nReports: " + str(md_path) + " and " + str(json_path))
    return 0 if report["sample_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
