#!/usr/bin/env python3
"""Repository-level inventory and migration planning for legacy COBOL estates.

This tool is intentionally deterministic and dependency-free. It does not claim
semantic equivalence or autonomously rewrite production code; it creates an
auditable inventory and a migration plan that can guide later verified steps.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

COBOL_EXTENSIONS = {".cbl", ".cob", ".cobol", ".cobx"}
COPY_EXTENSIONS = {".cpy", ".copy"}
JCL_EXTENSIONS = {".jcl", ".job"}
SQL_EXTENSIONS = {".sql"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}
COPY_RE = re.compile(r"\bCOPY\s+([A-Z0-9_$#@-]+)", re.I)
CALL_RE = re.compile(r"""\bCALL\s+(?:['"]([^'"]+)['"]|([A-Z0-9_$#@-]+))""", re.I)
PROGRAM_RE = re.compile(r"\bPROGRAM-ID\s*\.\s*([A-Z0-9_$#@-]+)", re.I)
EXEC_PGM_RE = re.compile(r"\bEXEC\s+PGM\s*=\s*([A-Z0-9_$#@-]+)", re.I)
JCL_DSN_RE = re.compile(r"\bDSN\s*=\s*([^,\s]+)", re.I)
INCLUDE_RE = re.compile(r"\b(?:INCLUDE|EXEC\s+SQL\s+INCLUDE)\s+([A-Z0-9_$#@-]+)", re.I)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return ""


def discover_files(root: Path) -> list[Path]:
    """Find likely estate artifacts without descending into generated/vendor dirs."""
    files: list[Path] = []
    for current, dirs, names in __import__("os").walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        base = Path(current)
        for name in sorted(names):
            path = base / name
            if path.suffix.lower() in COBOL_EXTENSIONS | COPY_EXTENSIONS | JCL_EXTENSIONS | SQL_EXTENSIONS:
                files.append(path)
                continue
            # Include extensionless COBOL programs only when the content is strongly indicative.
            if not path.suffix and path.is_file():
                sample = _read_text(path)[:8192]
                if re.search(r"\bIDENTIFICATION\s+DIVISION\b", sample, re.I):
                    files.append(path)
    return sorted(files, key=lambda p: p.as_posix().casefold())


def analyze_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    discovered = discover_files(root)
    records: dict[str, dict[str, Any]] = {}
    symbols: dict[str, list[str]] = defaultdict(list)

    for path in discovered:
        rel = path.relative_to(root).as_posix()
        ext = path.suffix.lower()
        kind = (
            "copybook" if ext in COPY_EXTENSIONS else
            "jcl" if ext in JCL_EXTENSIONS else
            "sql" if ext in SQL_EXTENSIONS else
            "cobol"
        )
        source = _read_text(path)
        program_match = PROGRAM_RE.search(source) if kind == "cobol" else None
        program_id = program_match.group(1).upper() if program_match else None
        stem = path.stem.upper()
        symbols[stem].append(rel)
        if program_id:
            symbols[program_id].append(rel)

        copies = sorted({m.group(1).upper() for m in COPY_RE.finditer(source)}) if kind in {"cobol", "copybook"} else []
        calls = sorted({(m.group(1) or m.group(2)).upper() for m in CALL_RE.finditer(source)}) if kind == "cobol" else []
        exec_programs = sorted({m.group(1).upper() for m in EXEC_PGM_RE.finditer(source)}) if kind == "jcl" else []
        sql_includes = sorted({m.group(1).upper() for m in INCLUDE_RE.finditer(source)}) if kind in {"cobol", "sql"} else []
        features = []
        for pattern, label in (
            (r"\bEXEC\s+SQL\b", "embedded-sql"),
            (r"\bEXEC\s+CICS\b", "cics"),
            (r"\bREDEFINES\b", "redefines"),
            (r"\bOCCURS\b", "tables"),
            (r"\bFILE\s+CONTROL\b|\bSELECT\s+.+\s+ASSIGN\b", "file-io"),
            (r"\bSORT\b|\bMERGE\b", "sort-merge"),
            (r"\bCALL\b", "subprogram-calls"),
        ):
            if re.search(pattern, source, re.I | re.S):
                features.append(label)
        records[rel] = {
            "path": rel, "kind": kind, "program_id": program_id,
            "copybooks": copies, "calls": calls, "jcl_programs": exec_programs,
            "sql_includes": sql_includes, "features": features,
            "lines": len(source.splitlines()),
        }

    def resolve(name: str) -> list[str]:
        return sorted(set(symbols.get(name.upper(), [])))

    edges: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []
    for rel, item in records.items():
        references: list[tuple[str, str]] = []
        references += [("copy", name) for name in item["copybooks"]]
        references += [("call", name) for name in item["calls"]]
        references += [("jcl-exec", name) for name in item["jcl_programs"]]
        references += [("sql-include", name) for name in item["sql_includes"]]
        for relation, target in references:
            candidates = [p for p in resolve(target) if p != rel]
            # A COPY should resolve to a copybook if possible, not to an identically named program.
            if relation == "copy":
                copy_candidates = [p for p in candidates if records[p]["kind"] == "copybook"]
                if copy_candidates:
                    candidates = copy_candidates
            if candidates:
                edges.extend({"source": rel, "target": candidate, "relation": relation, "symbol": target}
                             for candidate in candidates)
            else:
                unresolved.append({"source": rel, "relation": relation, "symbol": target})

    cobol_count = sum(x["kind"] == "cobol" for x in records.values())
    copy_count = sum(x["kind"] == "copybook" for x in records.values())
    jcl_count = sum(x["kind"] == "jcl" for x in records.values())
    sql_count = sum(x["kind"] == "sql" for x in records.values())
    risky = sorted(
        (item for item in records.values() if item["features"]),
        key=lambda item: (-len(item["features"]), item["path"].casefold()),
    )
    plan = {
        "schema_version": 1,
        "root": str(root),
        "summary": {
            "files": len(records), "cobol_programs": cobol_count,
            "copybooks": copy_count, "jcl_files": jcl_count, "sql_files": sql_count,
            "dependency_edges": len(edges), "unresolved_references": len(unresolved),
        },
        "files": list(records.values()),
        "dependencies": edges,
        "unresolved_references": unresolved,
        "recommended_sequence": [
            {"stage": 1, "name": "Baseline and inventory", "exit_criteria": "Inventory reviewed; source format, compiler and runtime assumptions recorded."},
            {"stage": 2, "name": "Dependency closure", "exit_criteria": "COPY/CALL/JCL/SQL references resolved or explicitly classified as external."},
            {"stage": 3, "name": "Low-risk pilot", "exit_criteria": "A small program and its copybooks translate; generated code compiles and differential tests pass."},
            {"stage": 4, "name": "Program families", "exit_criteria": "Programs grouped by shared copybooks, calls and batch flow; representative tests cover each family."},
            {"stage": 5, "name": "Verified migration waves", "exit_criteria": "Each wave has reviewed diffs, test evidence, rollback path and an exception report."},
        ],
        "review_first": [
            {"path": item["path"], "features": item["features"], "reason": "Contains constructs or integrations that need explicit semantic and runtime validation."}
            for item in risky
        ],
        "limitations": [
            "Static text analysis only; this is not a complete COBOL parser or linker.",
            "Name-based dependency resolution can be ambiguous and cannot prove runtime reachability.",
            "Dynamic CALL targets, generated source, vendor-specific syntax and external systems may be missed.",
            "A migration plan is not evidence of semantic equivalence; compile and run differential tests for each change.",
        ],
    }
    return plan


def render_markdown(plan: dict[str, Any]) -> str:
    summary = plan["summary"]
    lines = [
        "# Legacy modernization plan", "",
        f"> Root: `{plan['root']}`", "",
        "## Inventory", "",
        f"- Files discovered: **{summary['files']}**",
        f"- COBOL programs: **{summary['cobol_programs']}**",
        f"- Copybooks: **{summary['copybooks']}**",
        f"- JCL files: **{summary['jcl_files']}**",
        f"- SQL files: **{summary['sql_files']}**",
        f"- Resolved dependency edges: **{summary['dependency_edges']}**",
        f"- Unresolved references: **{summary['unresolved_references']}**", "",
        "## Recommended migration sequence", "",
    ]
    for stage in plan["recommended_sequence"]:
        lines += [f"### {stage['stage']}. {stage['name']}", "", stage["exit_criteria"], ""]
    lines += ["## Dependency edges", ""]
    if plan["dependencies"]:
        lines += ["| Source | Relation | Symbol | Target |", "|---|---|---|---|"]
        lines += [f"| `{e['source']}` | {e['relation']} | `{e['symbol']}` | `{e['target']}` |" for e in plan["dependencies"]]
    else:
        lines.append("No dependencies were resolved by name-based static analysis.")
    lines += ["", "## Unresolved references", ""]
    if plan["unresolved_references"]:
        lines += ["| Source | Relation | Symbol |", "|---|---|---|"]
        lines += [f"| `{e['source']}` | {e['relation']} | `{e['symbol']}` |" for e in plan["unresolved_references"]]
    else:
        lines.append("No unresolved references were detected by the current heuristics.")
    lines += ["", "## Review first", ""]
    if plan["review_first"]:
        for item in plan["review_first"]:
            lines.append(f"- `{item['path']}`: {', '.join(item['features'])}")
    else:
        lines.append("No flagged constructs were detected. This does not mean the code is low risk.")
    lines += ["", "## Limitations", ""]
    lines += [f"- {item}" for item in plan["limitations"]]
    lines += ["", "## Next actions", "",
              "1. Review and correct the inventory, especially ambiguous or external references.",
              "2. Record compiler/dialect, build instructions, runtime inputs, files and external interfaces.",
              "3. Select a small, representative pilot with a stable baseline.",
              "4. Translate with the existing deterministic translator, then run syntax, unit and differential tests.",
              "5. Do not accept a migration based on generated-code compilation alone.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory a legacy COBOL estate and produce an auditable migration plan.")
    parser.add_argument("root", nargs="?", default=".", help="repository or application root to scan")
    parser.add_argument("--out", default="migration-plan.md", help="Markdown report path (default: migration-plan.md)")
    parser.add_argument("--json-out", default="migration-plan.json", help="JSON report path (default: migration-plan.json)")
    parser.add_argument("--stdout-json", action="store_true", help="write JSON to stdout instead of the Markdown report")
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2
    plan = analyze_repository(root)
    if args.stdout_json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(plan) + "\n", encoding="utf-8")
        print(f"Markdown report: {out}")
    json_path = Path(args.json_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"JSON report: {json_path}")
    print("Note: static inventory only; review dependencies and verify every migration differentially.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
