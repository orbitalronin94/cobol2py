#!/usr/bin/env python3
"""Paired COBOL differential benchmark for Python, C, and Rust backends."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

def run(command: list[str], cwd: Path, timeout: int = 10) -> dict[str, Any]:
    try:
        p = subprocess.run(command, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True,
            text=False, timeout=timeout,
            env={**os.environ, "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8", "TZ": "UTC"})
        return {"launched": True, "returncode": p.returncode, "stdout": p.stdout,
                "stderr": p.stderr, "timeout": False}
    except subprocess.TimeoutExpired as e:
        return {"launched": True, "returncode": None, "stdout": e.stdout or b"",
                "stderr": e.stderr or b"", "timeout": True}
    except OSError as e:
        return {"launched": False, "returncode": None, "stdout": b"",
                "stderr": str(e).encode(), "timeout": False}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "benchmarks/cases.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "benchmark-results/multilang")
    parser.add_argument("--compile-timeout", type=int, default=15)
    parser.add_argument("--run-timeout", type=int, default=3)
    args = parser.parse_args()
    for tool in ("cobc", "cc", "rustc", "python3"):
        if shutil.which(tool) is None:
            parser.error(f"required tool not found on PATH: {tool}")
    cases = json.loads(args.manifest.read_text(encoding="utf-8"))["cases"]
    report: dict[str, Any] = {
        "schema_version": 1, "corpus": str(args.manifest),
        "pass_definition": "Exact stdout bytes and process return code match against GnuCOBOL.",
        "languages": {}, "cases": []}
    per_language: dict[str, list[dict[str, Any]]] = {x: [] for x in ("python", "c", "rust")}
    with tempfile.TemporaryDirectory(prefix="cobol2py-multilang-") as temp:
        root = Path(temp)
        for index, case in enumerate(cases, 1):
            source = (ROOT / case["path"]).resolve()
            row: dict[str, Any] = {"id": case["id"], "path": case["path"], "features": case.get("features", [])}
            case_dir = root / f"case-{index:04d}"
            case_dir.mkdir()
            ref_exe = case_dir / "reference"
            ref_compile = run(["cobc", "-x", "-I", str(source.parent), "-o", str(ref_exe), str(source)], case_dir, args.compile_timeout)
            if not ref_compile["launched"] or ref_compile["timeout"] or ref_compile["returncode"] != 0:
                row["reference_error"] = (ref_compile["stderr"] or b"reference compile failed").decode("utf-8", "replace")[-400:]
                for lang in per_language:
                    per_language[lang].append({"id": case["id"], "matched": False, "reason": "reference compile failed"})
                report["cases"].append(row)
                continue
            reference = run([str(ref_exe)], case_dir, args.run_timeout)
            if not reference["launched"] or reference["timeout"]:
                row["reference_error"] = "reference execution timed out or could not launch"
                for lang in per_language:
                    per_language[lang].append({"id": case["id"], "matched": False, "reason": "reference execution failed"})
                report["cases"].append(row)
                continue
            row["reference_returncode"] = reference["returncode"]
            commands = {
                "python": ["python3", "-I", str(ROOT / "cobol2py.py"), str(source), "--format", "auto"],
                "c": ["python3", "-I", str(ROOT / "cobol2native.py"), str(source), "--lang", "c", "--source-format", "auto"],
                "rust": ["python3", "-I", str(ROOT / "cobol2native.py"), str(source), "--lang", "rust", "--source-format", "auto"]}
            for lang, command in commands.items():
                work = case_dir / lang
                work.mkdir()
                translated = run(command, work, args.compile_timeout)
                result: dict[str, Any] = {"id": case["id"], "matched": False}
                if not translated["launched"] or translated["timeout"] or translated["returncode"] != 0:
                    result["reason"] = "translation timeout" if translated["timeout"] else (translated["stderr"].decode("utf-8", "replace")[-400:] or "translator failed")
                else:
                    suffix = {"python": ".py", "c": ".c", "rust": ".rs"}[lang]
                    generated = work / ("translated" + suffix)
                    generated.write_bytes(translated["stdout"])
                    if lang == "python":
                        compilation = {"returncode": 0, "stderr": b"", "timeout": False}
                        execution = ["python3", "-I", str(generated)]
                    elif lang == "c":
                        binary = work / "translated-c"
                        compilation = run(["cc", "-std=c11", "-Wall", "-Wextra", str(generated), "-o", str(binary)], work, args.compile_timeout)
                        execution = [str(binary)]
                    else:
                        binary = work / "translated-rust"
                        compilation = run(["rustc", str(generated), "-o", str(binary)], work, args.compile_timeout)
                        execution = [str(binary)]
                    if compilation.get("returncode") != 0 or compilation.get("timeout"):
                        result["reason"] = "generated code compilation failed: " + compilation.get("stderr", b"").decode("utf-8", "replace")[-350:]
                    else:
                        actual = run(execution, work, args.run_timeout)
                        match = actual["launched"] and not actual["timeout"] and actual["returncode"] == reference["returncode"] and actual["stdout"] == reference["stdout"]
                        result.update({"matched": match, "candidate_returncode": actual["returncode"],
                            "stdout_match": actual["stdout"] == reference["stdout"],
                            "returncode_match": actual["returncode"] == reference["returncode"]})
                        if not match:
                            result["reason"] = "runtime timeout" if actual["timeout"] else ("runtime launch failed" if not actual["launched"] else "stdout/return code mismatch")
                per_language[lang].append(result)
                row[lang] = result
            report["cases"].append(row)
            if index % 10 == 0:
                print(f"Progress: {index}/{len(cases)} cases", flush=True)
    for lang, results in per_language.items():
        passed = sum(bool(x["matched"]) for x in results)
        summary: dict[str, Any] = {"passed": passed, "total": len(results), "percent": round(100 * passed / len(results), 2) if results else 0.0, "failures_by_reason": {}}
        for item in results:
            if not item["matched"]:
                reason = item.get("reason", "unknown failure").splitlines()[-1][:180]
                summary["failures_by_reason"][reason] = summary["failures_by_reason"].get(reason, 0) + 1
        report["languages"][lang] = summary
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = args.output_dir / "multilang-benchmark.json", args.output_dir / "multilang-benchmark.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Three-language COBOL differential benchmark", "",
        "All backends use the same manifest and compiled GnuCOBOL reference.",
        "A pass requires byte-identical stdout and identical process return code. Unsupported syntax, translation errors, compiler errors and runtime failures count as failures.",
        "", f"- Corpus: {len(cases)} versioned programs (benchmarks/cases.json)",
        "- Reference: GnuCOBOL", "- Languages: Python, C, Rust", "",
        "| Backend | Exact matches | Pass rate |", "|---|---:|---:|"]
    for lang in ("python", "c", "rust"):
        s = report["languages"][lang]
        lines.append(f"| {lang} | {s['passed']}/{s['total']} | {s['percent']:.2f}% |")
    lines.extend(["", "## Failure families", ""])
    for lang in ("python", "c", "rust"):
        lines.extend([f"### {lang}"])
        failures = report["languages"][lang]["failures_by_reason"]
        if failures:
            for reason, count in sorted(failures.items(), key=lambda x: (-x[1], x[0]))[:12]:
                lines.append(f"- **{count}** — {reason.replace('|', chr(92) + '|')}")
        else:
            lines.append("- No failures.")
        lines.append("")
    lines.extend(["## Per-case results", "", "| Case | Features | Python | C | Rust |", "|---|---|---:|---:|---:|"])
    for row in report["cases"]:
        marks = ["PASS" if row.get(lang, {}).get("matched") else "FAIL" for lang in ("python", "c", "rust")]
        lines.append(f"| {row['id']} | {', '.join(row.get('features', []))} | {marks[0]} | {marks[1]} | {marks[2]} |")
    lines.extend(["", "## Interpretation", "",
        "- Scores are comparable because the same fixtures and GnuCOBOL outputs are used for all three backends.",
        "- A backend score is coverage of this versioned corpus, not the percentage of all COBOL programs it supports.",
        "- C and Rust currently implement only an experimental subset; unsupported constructs intentionally count as failures.",
        "- Cases where C or Rust succeeds and Python fails are candidates for new Python regression tests, after validating the relevant COBOL semantics.", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:18]))
    print(f"\nReports: {md_path} and {json_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
