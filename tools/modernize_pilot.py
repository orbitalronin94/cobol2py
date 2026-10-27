#!/usr/bin/env python3
"""Run a conservative inventory-to-translation pilot without executing generated code."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import cobol2py
import cobol2py_agent


def run_pilot(root: Path, output_dir: Path) -> dict[str, Any]:
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
            diagnostics = cobol2py.collect_diagnostics(program)
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
    }
    report = {
        "schema_version": 1,
        "root": str(root),
        "inventory_summary": inventory["summary"],
        "translation_summary": summary,
        "semantic_validation": "not-performed",
        "limitations": [
            "Generated programs are syntax-checked but not executed.",
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
        "**Behavioral equivalence was not tested by this command.**", "",
        "## Per-file results", "",
        "| Source | Status | Syntax valid | Diagnostics |",
        "|---|---|---:|---:|",
    ]
    for item in results:
        lines.append(
            f"| `{item['source']}` | {item['status']} | "
            f"{'yes' if item['syntax_valid'] else 'no'} | {len(item['diagnostics'])} |"
        )
    lines += ["", "## Validation boundary", ""]
    lines += [f"- {lim}" for lim in report["limitations"]]
    (output_dir / "translation-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventory COBOL sources, translate each program, and syntax-check the generated Python."
    )
    parser.add_argument("root", nargs="?", default="samples", help="source tree to inspect (default: samples)")
    parser.add_argument("--out-dir", type=Path, default=Path("/tmp/cobol2py-pilot"),
                        help="output directory outside the source root (default: /tmp/cobol2py-pilot)")
    args = parser.parse_args(argv)
    try:
        report = run_pilot(Path(args.root), args.out_dir)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    summary = report["translation_summary"]
    print(json.dumps(summary, indent=2))
    return 1 if summary["syntax_errors"] or summary["translation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
