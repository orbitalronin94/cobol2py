#!/usr/bin/env python3
"""Compile COBOL edge cases with GnuCOBOL and compare reference output to cobol2py.

The original 500+500 external score is deliberately kept separate. This runner
writes a JSON scorecard for the additional 50 cases and returns non-zero only
when a reference program fails to compile or execute; translation mismatches are
reported as data so the corpus can be used to diagnose current behavior. The CI gate also requires at least 60% exact matches.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command: list[str], *, cwd: Path, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--translator", type=Path, default=Path("cobol2py.py"))
    parser.add_argument("--source-dir", type=Path, default=Path("benchmarks/edge_cases"))
    parser.add_argument("--output", type=Path, default=Path("edge_cases_report.json"))
    args = parser.parse_args()
    root = Path.cwd()
    translator = (root / args.translator).resolve()
    source_dir = (root / args.source_dir).resolve()
    sources = sorted(source_dir.glob("[0-9][0-9]_*.cbl"))
    if len(sources) != 50:
        print(f"Expected 50 edge-case .cbl files; found {len(sources)} in {source_dir}", file=sys.stderr)
        return 2
    rows = []
    compile_failures = 0
    with tempfile.TemporaryDirectory(prefix="cobol2py-edge-") as temp:
        tempdir = Path(temp)
        for source in sources:
            exe = tempdir / source.stem
            ref = run(["cobc", "-x", "-o", str(exe), str(source)], cwd=root)
            row = {"case": source.stem, "source": str(source.relative_to(root))}
            if ref.returncode:
                compile_failures += 1
                row.update(status="reference_compile_failed", compile_returncode=ref.returncode,
                           compile_stderr=ref.stderr[-4000:])
                rows.append(row)
                continue
            try:
                reference = run([str(exe)], cwd=root)
            except subprocess.TimeoutExpired:
                row.update(status="reference_timeout")
                rows.append(row)
                continue
            row.update(reference_returncode=reference.returncode, reference_stdout=reference.stdout)
            if reference.returncode:
                row.update(status="reference_runtime_failed", reference_stderr=reference.stderr[-4000:])
                rows.append(row)
                continue
            # These fixtures declare free format explicitly. The translator's
            # auto-detection does not interpret compiler directives, so remove the
            # directive from a temporary copy and pass --format free explicitly.
            # Keep the original source untouched for GnuCOBOL/reference provenance.
            normalized_source = tempdir / f"{source.stem}.translator.cbl"
            normalized_text = source.read_text(encoding="utf-8", errors="replace")
            normalized_text = re.sub(
                r"(?im)^\\s*>>SOURCE\\s+FORMAT\\s+FREE\\s*$\\n?",
                "",
                normalized_text,
            )
            normalized_source.write_text(normalized_text, encoding="utf-8")
            translated = run(
                [sys.executable, str(translator), "--format", "free", str(normalized_source)],
                cwd=root,
            )
            if translated.returncode:
                row.update(status="translation_failed", translator_stderr=translated.stderr[-4000:])
                rows.append(row)
                continue
            pyfile = tempdir / f"{source.stem}.py"
            generated = translated.stdout
            row["generated_python_bytes"] = len(generated.encode("utf-8"))
            if not generated.strip():
                row.update(status="empty_translation", translator_stderr=translated.stderr[-4000:])
                rows.append(row)
                continue
            pyfile.write_text(generated, encoding="utf-8")
            syntax = run([sys.executable, "-m", "py_compile", str(pyfile)], cwd=root)
            if syntax.returncode:
                row.update(status="generated_python_syntax_error", translator_stderr=syntax.stderr[-4000:])
                rows.append(row)
                continue
            try:
                actual = run([sys.executable, str(pyfile)], cwd=root)
            except subprocess.TimeoutExpired:
                row.update(status="translated_program_timeout")
                rows.append(row)
                continue
            equal = actual.returncode == reference.returncode and actual.stdout == reference.stdout
            row.update(status="pass" if equal else "output_or_return_mismatch",
                       translated_returncode=actual.returncode, translated_stdout=actual.stdout,
                       translated_stderr=actual.stderr[-4000:])
            rows.append(row)
    passed = sum(r.get("status") == "pass" for r in rows)
    report = {
        "schema_version": 1,
        "benchmark": "edge_cases",
        "cases": len(sources),
        "passed": passed,
        "percent": round(100 * passed / len(sources), 2),
        "reference_compile_failures": compile_failures,
        "status_counts": {status: sum(r.get("status") == status for r in rows)
                          for status in sorted({r.get("status", "unknown") for r in rows})},
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("cases", "passed", "percent", "reference_compile_failures", "status_counts")}, indent=2))
    if compile_failures:
        return 1
    minimum_percent = 60.0
    if report["percent"] < minimum_percent:
        print(f"Edge-case gate failed: {report['percent']:.2f}% exact matches; minimum required is {minimum_percent:.2f}%.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
