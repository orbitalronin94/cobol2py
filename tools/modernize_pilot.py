#!/usr/bin/env python3
"""Run a conservative inventory-to-translation pilot without executing generated code."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Executing this file directly sets sys.path[0] to tools/, not the repository root.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import cobol2py
import cobol2py_agent


DIAGNOSTIC_CLASSIFICATIONS = {
    "COPYBOOK_RESOLUTION": "dependency-resolution",
    "MALFORMED_CONTROL_FLOW": "possible-defect",
    "UNSUPPORTED_STATEMENT": "possible-defect",
    "PYTHON_IDENTIFIER_COLLISION": "possible-defect",
    "EVALUATE_WITHOUT_WHEN": "possible-defect",
    "ARITHMETIC_SIZE_ERROR_UNSUPPORTED": "known-limitation",
    "PARTIAL_NUMERIC_PIC_SEMANTICS": "known-limitation",
    "UNSUPPORTED_STORAGE_OVERLAY": "known-limitation",
    "UNSUPPORTED_RENAMES": "known-limitation",
    "UNSUPPORTED_CONDITION_NAME_88": "known-limitation",
    "OCCURS_GROUP_UNSUPPORTED": "known-limitation",
    "OCCURS_DEPENDING_ON_UNSUPPORTED": "known-limitation",
    "UNSUPPORTED_EVALUATE_ALSO": "known-limitation",
    "ALPHANUMERIC_ORDER_COMPARISON_UNSUPPORTED": "known-limitation",
    "ALPHANUMERIC_FIELD_COMPARISON_UNSUPPORTED": "known-limitation",
    "ALPHANUMERIC_LITERAL_LEFT_COMPARISON_UNSUPPORTED": "known-limitation",
    "EVALUATE_ALPHANUMERIC_PADDING_UNSUPPORTED": "known-limitation",
}


def classify_diagnostic(diagnostic: dict[str, Any]) -> dict[str, Any]:
    """Add a review category without changing the translator's diagnostic meaning."""
    result = dict(diagnostic)
    result["classification"] = DIAGNOSTIC_CLASSIFICATIONS.get(str(diagnostic.get("code", "")), "review-required")
    result["review_required"] = True
    return result


def _translator_version() -> str:
    """Read the human-maintained version from the translator module docstring."""
    import re
    match = re.search(r"\bv(\d+\.\d+\.\d+)\b", cobol2py.__doc__ or "")
    return match.group(1) if match else "unknown"


def _differential_fixtures(source_path: Path) -> list[dict[str, Any]]:
    """Return exact manifest path matches; never infer semantic validation from a match."""
    manifest = REPOSITORY_ROOT / "benchmarks" / "cases.json"
    try:
        cases = json.loads(manifest.read_text(encoding="utf-8")).get("cases", [])
    except (OSError, json.JSONDecodeError):
        return []
    return [
        {"id": case.get("id"), "path": case.get("path"), "features": case.get("features", [])}
        for case in cases
        if (REPOSITORY_ROOT / case.get("path", "")).resolve() == source_path.resolve()
    ]


def _run_differential(results: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    """Run only manifest fixtures exactly associated with inventoried source paths."""
    selected_ids = {
        fixture["id"]
        for item in results
        for fixture in item.get("differential_fixtures", [])
    }
    if not selected_ids:
        return {"status": "not-applicable", "case_count": 0, "cases": []}

    manifest = json.loads((REPOSITORY_ROOT / "benchmarks" / "cases.json").read_text(encoding="utf-8"))
    selected = [case for case in manifest.get("cases", []) if case.get("id") in selected_ids]
    manifest_path = output_dir / "differential-cases.json"
    manifest_path.write_text(json.dumps({"version": manifest.get("version", 1), "cases": selected}, indent=2) + "\n", encoding="utf-8")
    report_path = output_dir / "differential-report.json"
    markdown_path = output_dir / "differential-report.md"
    command = [
        sys.executable, str(REPOSITORY_ROOT / "benchmarks" / "run_benchmark.py"),
        "--manifest", str(manifest_path), "--translator", str(REPOSITORY_ROOT / "cobol2py.py"),
        "--json", str(report_path), "--markdown", str(markdown_path), "--report-only",
    ]
    try:
        completed = subprocess.run(
            command, cwd=REPOSITORY_ROOT, text=True, capture_output=True,
            timeout=max(120, len(selected) * 15), check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"status": "reference-error", "case_count": len(selected), "cases": [], "error": str(error)}
    if not report_path.is_file():
        return {
            "status": "reference-error", "case_count": len(selected), "cases": [],
            "error": completed.stderr.strip()[-2000:] or f"benchmark exited {completed.returncode} without a report",
        }
    try:
        benchmark = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"status": "reference-error", "case_count": len(selected), "cases": [], "error": str(error)}

    cases = []
    for case in benchmark.get("cases", []):
        if not case.get("compile_ok", False) or not case.get("reference_ok", True):
            status = "reference-error"
        elif (case.get("candidate") or {}).get("matched", False):
            status = "matched"
        else:
            status = "discrepancy"
        cases.append({"id": case.get("id"), "path": case.get("path"), "status": status,
                      "reason": (case.get("candidate") or {}).get("reason") or case.get("compile_error") or case.get("reference_error")})
    overall = "matched" if cases and all(case["status"] == "matched" for case in cases) else (
        "discrepancy" if any(case["status"] == "discrepancy" for case in cases) else "reference-error"
    )
    status_by_id = {case["id"]: case["status"] for case in cases}
    for item in results:
        matched = [status_by_id[fixture["id"]] for fixture in item.get("differential_fixtures", []) if fixture["id"] in status_by_id]
        if matched:
            item["semantic_status"] = "matched" if all(status == "matched" for status in matched) else (
                "discrepancy" if "discrepancy" in matched else "reference-error"
            )
    return {"status": overall, "case_count": len(cases), "cases": cases,
            "report": report_path.name, "markdown": markdown_path.name,
            "runner_returncode": completed.returncode}


def run_pilot(root: Path, output_dir: Path, *, differential: bool = False) -> dict[str, Any]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    if not root.is_dir():
        raise ValueError(f"source root is not a directory: {root}")
    if output_dir == root or output_dir.is_relative_to(root):
        raise ValueError("output directory must be outside the source root to keep inventory reproducible")

    inventory = cobol2py_agent.analyze_repository(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "inventory.md").write_text(
        cobol2py_agent.render_markdown(inventory) + "\n", encoding="utf-8"
    )
    (output_dir / "inventory.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    copybook_dirs = sorted({
        (root / item["path"]).resolve().parent
        for item in inventory["files"]
        if item["kind"] == "copybook"
    })
    translated_root = output_dir / "translated"
    results: list[dict[str, Any]] = []

    for item in inventory["files"]:
        if item["kind"] != "cobol":
            continue
        relative = Path(item["path"])
        source_path = root / relative
        destination = (translated_root / relative).with_suffix(".py")
        result: dict[str, Any] = {
            "source": relative.as_posix(),
            "output": destination.relative_to(output_dir).as_posix(),
            "syntax_valid": False,
            "diagnostics": [],
            "status": "translation-error",
            "semantic_status": "not-evaluated",
            "differential_fixtures": _differential_fixtures(source_path),
        }
        try:
            source = source_path.read_text(encoding="utf-8", errors="replace")
            program = cobol2py.parse_cobol(
                source,
                source_format="auto",
                copybook_paths=copybook_dirs,
                source_path=source_path,
            )
            generated = cobol2py.emit_python(program)
            diagnostics = [classify_diagnostic(item) for item in cobol2py.collect_diagnostics(program)]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(generated + "\n", encoding="utf-8")
            try:
                compile(generated, str(destination), "exec")
                result["syntax_valid"] = True
            except SyntaxError as error:
                result["syntax_error"] = {
                    "line": error.lineno,
                    "message": error.msg,
                }
            result["diagnostics"] = diagnostics
            result["status"] = (
                "syntax-error" if not result["syntax_valid"]
                else "translated-with-diagnostics" if diagnostics
                else "translated"
            )
        except Exception as error:  # keep a per-file report instead of aborting the estate scan
            result["error"] = f"{type(error).__name__}: {error}"
        results.append(result)

    summary = {
        "source_files": len(results),
        "translated": sum(item["status"] in ("translated", "translated-with-diagnostics") for item in results),
        "syntax_errors": sum(item["status"] == "syntax-error" for item in results),
        "translation_errors": sum(item["status"] == "translation-error" for item in results),
        "files_with_diagnostics": sum(bool(item["diagnostics"]) for item in results),
        "diagnostic_count": sum(len(item["diagnostics"]) for item in results),
        "diagnostic_classifications": {},
        "diagnostic_codes": {},
    }
    for item in results:
        for diagnostic in item["diagnostics"]:
            classification = diagnostic["classification"]
            code = diagnostic.get("code", "UNKNOWN")
            summary["diagnostic_classifications"][classification] = summary["diagnostic_classifications"].get(classification, 0) + 1
            summary["diagnostic_codes"][code] = summary["diagnostic_codes"].get(code, 0) + 1

    differential_report = {"status": "not-evaluated", "case_count": 0, "cases": []}
    if differential:
        differential_report = _run_differential(results, output_dir)
        for item in results:
            if not item.get("differential_fixtures"):
                item["semantic_status"] = "not-applicable"
    semantic_validation = differential_report["status"] if differential else "not-performed"
    summary["semantic_status_counts"] = {}
    for item in results:
        status = item["semantic_status"]
        summary["semantic_status_counts"][status] = summary["semantic_status_counts"].get(status, 0) + 1
    summary["differential_case_count"] = differential_report["case_count"]


    report = {
        "schema_version": 2,
        "tool_versions": {"translator": _translator_version(), "pilot_schema": 2},
        "root": str(root),
        "inventory_summary": inventory["summary"],
        "translation_summary": summary,
        "semantic_validation": semantic_validation,
        "differential_validation": differential_report,
        "validation": {
            "syntax": "checked-per-file",
            "semantics": differential_report["status"] if differential else "not-evaluated",
            "comparison_dimensions": ["stdout", "return-code"],
            "differential_fixture_links_are_candidates_only": True,
        },
        "limitations": [
            "By default, generated programs are syntax-checked but not executed; --differential explicitly executes only exact manifest fixtures.",
            "Syntax validity and static diagnostics do not prove behavioral equivalence.",
            "Use the differential benchmark with GnuCOBOL for supported, executable cases.",
        ],
        "results": results,
    }
    (output_dir / "translation-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Translation pilot report", "",
        f"> Source root: `{root}`", "",
        "## Summary", "",
        f"- COBOL source files: **{summary['source_files']}**",
        f"- Syntax-checked translations: **{summary['translated']}**",
        f"- Syntax errors: **{summary['syntax_errors']}**",
        f"- Translation errors: **{summary['translation_errors']}**",
        f"- Files with diagnostics: **{summary['files_with_diagnostics']}**", "",
        ("**Differential status: " + report["semantic_validation"] + ".**" if differential else "**Behavioral equivalence was not tested by this command.**"), "",
        "## Per-file results", "",
        "| Source | Status | Syntax valid | Diagnostics |",
        "|---|---|---:|---:|",
    ]
    for item in results:
        lines.append(
            f"| `{item['source']}` | {item['status']} | "
            f"{'yes' if item['syntax_valid'] else 'no'} | {len(item['diagnostics'])} |"
        )
    lines += ["", "## Diagnostic classification", "", "| Classification | Count |", "|---|---:|"]
    for classification, count in sorted(summary["diagnostic_classifications"].items()):
        lines.append("| \x60" + classification + "\x60 | " + str(count) + " |")
    lines += ["", "## Diagnostic details by source", "", "| Source | Line | Code | Classification | Message |", "|---|---:|---|---|---|"]
    for item in results:
        for diagnostic in item["diagnostics"]:
            line = diagnostic.get("line") if diagnostic.get("line") is not None else "—"
            message = str(diagnostic.get("message", "")).replace("|", "\\|").replace("\\n", " ")
            lines.append("| `" + item["source"] + "` | " + str(line) + " | `" + str(diagnostic.get("code", "UNKNOWN")) + "` | `" + diagnostic["classification"] + "` | " + message + " |")
    lines += ["", "## Diagnostic codes", "", "| Code | Count | Classification |", "|---|---:|---|"]
    for code, count in sorted(summary["diagnostic_codes"].items()):
        classification = DIAGNOSTIC_CLASSIFICATIONS.get(code, "review-required")
        lines.append("| \x60" + code + "\x60 | " + str(count) + " | \x60" + classification + "\x60 |")
    lines += ["", "## Candidate differential fixtures", "",
        "Fixture links identify exact source-path matches in the versioned manifest; they do not mean this pilot ran those cases or proved semantic equivalence.", "",
        "| Source | Candidate fixture IDs | Semantic status |", "|---|---|---|"]
    for item in results:
        fixture_ids = ", ".join("\x60" + str(fixture["id"]) + "\x60" for fixture in item.get("differential_fixtures", [])) or "—"
        lines.append("| \x60" + item["source"] + "\x60 | " + fixture_ids + " | \x60" + item["semantic_status"] + "\x60 |")
    lines += ["", "## Differential validation", "",
        "- Overall status: \x60" + report["semantic_validation"] + "\x60",
        "- Cases evaluated: " + str(differential_report["case_count"]), ""]
    if differential_report.get("cases"):
        lines += ["| Fixture | Status | Detail |", "|---|---|---|"]
        for case in differential_report["cases"]:
            reason = str(case.get("reason") or "—").replace("|", "\\|").replace("\\n", " ")
            lines.append("| \x60" + str(case.get("id")) + "\x60 | \x60" + case["status"] + "\x60 | " + reason + " |")
    elif not differential:
        lines.append("Differential execution was not requested. Use --differential to run only exact manifest matches.")
    else:
        lines.append("No exact differential fixtures were associated with the selected source files.")
    lines += ["", "## Validation boundary", ""]
    lines += [f"- {lim}" for lim in report["limitations"]]
    (output_dir / "translation-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventory COBOL sources, translate each program, syntax-check output, and optionally run exact differential fixtures."
    )
    parser.add_argument("root", nargs="?", default="samples", help="source tree to inspect (default: samples)")
    parser.add_argument("--out-dir", type=Path, default=Path("/tmp/cobol2py-pilot"),
                        help="output directory outside the source root (default: /tmp/cobol2py-pilot)")
    parser.add_argument("--differential", action="store_true", help="explicitly compare exact manifest fixtures against GnuCOBOL; executes only those fixture cases")
    args = parser.parse_args(argv)
    try:
        report = run_pilot(Path(args.root), args.out_dir, differential=args.differential)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    summary = report["translation_summary"]
    print(json.dumps(summary, indent=2))
    return 1 if (summary["syntax_errors"] or summary["translation_errors"] or report["semantic_validation"] in ("discrepancy", "reference-error")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
