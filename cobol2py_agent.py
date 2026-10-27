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
COPY_RE = re.compile(r"\bCOPY\s+([A-Z0-9_$#@./\\-]+)", re.I)
CALL_LITERAL_RE = re.compile(r'''\bCALL\s+['"]([^'"]+)['"]''', re.I)
CALL_DYNAMIC_RE = re.compile(r'''\bCALL\s+([A-Z0-9_$#@-]+)\b''', re.I)
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


def _strip_inline_comment(line: str, marker: str) -> str:
    """Remove a language comment marker only when it occurs outside literals."""
    quote: str | None = None
    index = 0
    while index < len(line):
        char = line[index]
        if quote is not None:
            if char == quote:
                if index + 1 < len(line) and line[index + 1] == quote:
                    index += 2
                    continue
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif line.startswith(marker, index):
            return line[:index]
        index += 1
    return line


def _mask_literals(source: str) -> str:
    """Replace quoted literal contents with spaces while preserving offsets and newlines."""
    chars = list(source)
    quote: str | None = None
    index = 0
    while index < len(source):
        char = source[index]
        if quote is not None:
            if char != "\n":
                chars[index] = " "
            if char == quote:
                if index + 1 < len(source) and source[index + 1] == quote:
                    chars[index + 1] = " "
                    index += 2
                    continue
                quote = None
        elif char in ("'", '"'):
            quote = char
            chars[index] = " "
        index += 1
    return "".join(chars)


def _analysis_source(source: str, kind: str) -> str:
    """Strip comments before regex inventory so commented-out code is not a dependency."""
    lines = source.splitlines()
    if kind in {"cobol", "copybook"}:
        # Fixed-format comment/debug indicators occupy column 7 after six
        # sequence columns. Preserve line count while removing comment records.
        fixed_format = any(
            len(line) >= 7
            and re.fullmatch(r"[ 0-9]{6}", line[:6])
            and line[6] in (" ", "*", "/", "D", "d", "-")
            for line in lines[:20]
        )
        cleaned: list[str] = []
        for line in lines:
            if fixed_format and len(line) >= 7 and re.fullmatch(r"[ 0-9]{6}", line[:6]):
                indicator = line[6]
                if indicator in ("*", "/"):
                    cleaned.append("")
                    continue
                line = line[7:72]
            cleaned.append(_strip_inline_comment(line, "*>"))
        return "\n".join(cleaned)
    if kind == "jcl":
        return "\n".join("" if line.lstrip().startswith("//*") else line for line in lines)
    if kind == "sql":
        return "\n".join(_strip_inline_comment(line, "--") for line in lines)
    return source


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
        analysis_source = _analysis_source(source, kind)
        code_source = _mask_literals(analysis_source)
        program_match = PROGRAM_RE.search(code_source) if kind == "cobol" else None
        program_id = program_match.group(1).upper() if program_match else None
        stem = path.stem.upper()
        symbols[stem].append(rel)
        if program_id:
            symbols[program_id].append(rel)

        copies = sorted({m.group(1).upper().rstrip(".") for m in COPY_RE.finditer(code_source)}) if kind in {"cobol", "copybook"} else []
        calls = sorted({m.group(1).upper() for m in CALL_LITERAL_RE.finditer(analysis_source) if code_source[m.start():m.start() + 4].upper() == "CALL"}) if kind == "cobol" else []
        dynamic_calls = sorted({m.group(1).upper() for m in CALL_DYNAMIC_RE.finditer(code_source)}) if kind == "cobol" else []
        exec_programs = sorted({m.group(1).upper() for m in EXEC_PGM_RE.finditer(code_source)}) if kind == "jcl" else []
        jcl_datasets = sorted({m.group(1).strip("\\'\"").upper() for m in JCL_DSN_RE.finditer(analysis_source) if code_source[m.start():m.start() + 3].upper() == "DSN"}) if kind == "jcl" else []
        sql_includes = sorted({m.group(1).upper() for m in INCLUDE_RE.finditer(code_source)}) if kind in {"cobol", "sql"} else []
        features = []
        for pattern, label in (
            (r"\bEXEC\s+SQL\b", "embedded-sql"),
            (r"\bEXEC\s+CICS\b", "cics"),
            (r"\bREDEFINES\b", "redefines"),
            (r"\bOCCURS\b", "tables"),
            (r"\bFILE\s+CONTROL\b|\bSELECT\s+.+\s+ASSIGN\b", "file-io"),
            (r"\bSORT\b|\bMERGE\b", "sort-merge"),
            (r"\bCALL\b", "subprogram-calls"),
            (r"\bALTER\b", "alter-dynamic-control-flow"),
            (r"\bGO\s+TO\b", "goto-control-flow"),
            (r"\bGO\s+TO\b[^.]*\bDEPENDING\s+ON\b", "computed-goto"),
        ):
            if re.search(pattern, code_source, re.I | re.S):
                features.append(label)

        # Heuristic triage only: weights surface high-risk constructs; they are
        # not a correctness claim, measured effort, or proof of runtime reachability.
        complexity_signals = (
            (r"\bALTER\b", "ALTER", 5),
            (r"\bGO\s+TO\b[^.]*\bDEPENDING\s+ON\b", "GO TO DEPENDING ON", 5),
            (r"\bREDEFINES\b", "REDEFINES", 4),
            (r"\bGO\s+TO\b", "GO TO", 2),
            (r"\bPERFORM\b[^.]*\bUNTIL\b", "PERFORM UNTIL", 2),
            (r"\bEXEC\s+(?:SQL|CICS)\b", "embedded SQL/CICS", 3),
            (r"\bCALL\s+[A-Za-z0-9_$#@-]+\b", "dynamic CALL identifier", 3),
            (r"\bCOPY\b", "COPY dependency", 1),
        )
        complexity_reasons = [
            {"construct": label, "weight": weight}
            for pattern, label, weight in complexity_signals
            if re.search(pattern, code_source, re.I | re.S)
        ]
        complexity_score = sum(item["weight"] for item in complexity_reasons)
        complexity_level = (
            "HIGH" if complexity_score >= 5 else
            "MEDIUM" if complexity_score >= 2 else
            "LOW"
        )
        records[rel] = {
            "path": rel, "kind": kind, "program_id": program_id,
            "copybooks": copies, "calls": calls, "dynamic_calls": dynamic_calls, "jcl_programs": exec_programs,
            "jcl_datasets": jcl_datasets, "sql_includes": sql_includes, "features": features,
            "complexity_score": complexity_score, "complexity_level": complexity_level,
            "complexity_reasons": complexity_reasons,
            "lines": len(source.splitlines()),
        }

    def resolve(name: str) -> list[str]:
        return sorted(set(symbols.get(name.upper(), [])))

    paths_by_casefold = {path.casefold(): path for path in records}

    def resolve_copy(source_rel: str, target: str) -> list[str]:
        """Prefer a source-relative copybook before falling back to name lookup."""
        normalized = target.replace("\\", "/").rstrip(".")
        target_path = Path(normalized)
        source_parent = Path(source_rel).parent
        explicit_path = "/" in normalized
        if explicit_path:
            candidates = [source_parent / target_path]
            if not target_path.suffix:
                candidates.extend(
                    source_parent / (normalized + suffix)
                    for suffix in (".cpy", ".copy", ".CPY", ".COPY")
                )
            for candidate in candidates:
                try:
                    relative = (root / candidate).resolve().relative_to(root).as_posix()
                except ValueError:
                    continue
                matched = paths_by_casefold.get(relative.casefold())
                if matched and records[matched]["kind"] == "copybook" and matched != source_rel:
                    return [matched]
            return []

        key = target_path.stem.upper()
        all_matches = [
            path for path in sorted(set(symbols.get(key, [])))
            if path != source_rel and records[path]["kind"] == "copybook"
        ]
        local = [
            path for path in all_matches
            if Path(path).parent.as_posix().casefold() == source_parent.as_posix().casefold()
        ]
        return local or all_matches

    edges: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []
    ambiguous: list[dict[str, Any]] = []
    for rel, item in records.items():
        references: list[tuple[str, str]] = []
        references += [("copy", name) for name in item["copybooks"]]
        references += [("call", name) for name in item["calls"]]
        references += [("jcl-exec", name) for name in item["jcl_programs"]]
        references += [("sql-include", name) for name in item["sql_includes"]]
        for relation, target in references:
            if relation == "copy":
                candidates = resolve_copy(rel, target)
            else:
                candidates = [p for p in resolve(target) if p != rel]
            if candidates:
                edges.extend({"source": rel, "target": candidate, "relation": relation, "symbol": target}
                             for candidate in candidates)
                if len(candidates) > 1:
                    ambiguous.append({
                        "source": rel, "relation": relation, "symbol": target,
                        "candidates": candidates,
                    })
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
            "ambiguous_references": len(ambiguous),
            "dynamic_call_targets": sum(len(item["dynamic_calls"]) for item in records.values()),
            "high_complexity_files": sum(item.get("complexity_level") == "HIGH" for item in records.values()),
        },
        "files": list(records.values()),
        "dependencies": edges,
        "unresolved_references": unresolved,
        "ambiguous_references": ambiguous,
        "recommended_sequence": [
            {"stage": 1, "name": "Baseline and inventory", "exit_criteria": "Inventory reviewed; source format, compiler and runtime assumptions recorded."},
            {"stage": 2, "name": "Dependency closure", "exit_criteria": "COPY/CALL/JCL/SQL references resolved or explicitly classified as external."},
            {"stage": 3, "name": "Low-risk pilot", "exit_criteria": "A small program and its copybooks translate; generated code compiles and differential tests pass."},
            {"stage": 4, "name": "Program families", "exit_criteria": "Programs grouped by shared copybooks, calls and batch flow; representative tests cover each family."},
            {"stage": 5, "name": "Verified migration waves", "exit_criteria": "Each wave has reviewed diffs, test evidence, rollback path and an exception report."},
        ],
        "review_first": [
            {"path": item["path"], "features": item["features"], "complexity_score": item["complexity_score"],
             "complexity_level": item["complexity_level"], "complexity_reasons": item["complexity_reasons"],
             "reason": "Contains constructs or integrations that need explicit semantic and runtime validation."}
            for item in sorted(risky, key=lambda item: (-item["complexity_score"], -len(item["features"]), item["path"].casefold()))
        ],
        "limitations": [
            "Complexity scores are deterministic heuristics for triage, not measured effort, runtime reachability, or semantic support.",
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
        f"- Unresolved references: **{summary['unresolved_references']}**",
        f"- Ambiguous references: **{summary.get('ambiguous_references', 0)}**",
        f"- High-complexity files (heuristic): **{summary.get('high_complexity_files', 0)}**", "",
        f"- Dynamic CALL targets (not statically resolved): **{summary.get('dynamic_call_targets', 0)}**", "",
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
    lines += ["", "## Dynamic CALL targets", ""]
    dynamic_rows = [(item["path"], target) for item in plan["files"] for target in item.get("dynamic_calls", [])]
    if dynamic_rows:
        lines += ["| Source | Target identifier |", "|---|---|"]
        lines += ["| " + path + " | " + target + " |" for path, target in dynamic_rows]
        lines.append("")
        lines.append("These targets are identifiers, not literal program names. Their runtime values cannot be resolved by this static name-based analysis.")
    else:
        lines.append("No unquoted CALL identifiers were detected.")
    lines += ["", "## Ambiguous references", ""]
    if plan.get("ambiguous_references"):
        lines += ["| Source | Relation | Symbol | Candidate paths |", "|---|---|---|---|"]
        lines += [
            f"| `{item['source']}` | {item['relation']} | `{item['symbol']}` | "
            + ", ".join(f"`{candidate}`" for candidate in item["candidates"])
            + " |"
            for item in plan["ambiguous_references"]
        ]
    else:
        lines.append("No ambiguous references were detected by name-based static analysis.")
    lines += ["", "## JCL datasets detected", ""]
    dataset_rows = [(item["path"], dataset) for item in plan["files"] for dataset in item.get("jcl_datasets", [])]
    if dataset_rows:
        lines += ["| JCL file | DSN |", "|---|---|"]
        lines += [f"| `{path}` | `{dataset}` |" for path, dataset in dataset_rows]
    else:
        lines.append("No DSN= references were detected in JCL files.")
    lines += ["", "## Review first", ""]
    if plan["review_first"]:
        for item in plan["review_first"]:
            lines.append(f"- `{item['path']}` — **{item.get('complexity_level', 'UNKNOWN')}** "
                         f"(score {item.get('complexity_score', 0)}): {', '.join(item['features'])}")
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
