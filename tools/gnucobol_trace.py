#!/usr/bin/env python3
"""Compile a COBOL source with GnuCOBOL tracing and print variable snapshots.

This is a diagnostic helper, not a full COBOL debugger. It injects DISPLAY
statements immediately before standalone program-exit statements (or at the
end of the source when no explicit exit is found). Elementary non-table data
items are traced; groups and OCCURS items are reported as skipped.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import cobol2py


def detect_source_format(source: str) -> str:
    """Use the translator's conservative fixed-format heuristic."""
    for line in source.splitlines()[:30]:
        if len(line) > 7 and line[:6].strip() == "" and line[6] in " */-D":
            return "fixed"
        if len(line) > 7 and line[:6].strip().isdigit() and line[6] in " */-D":
            return "fixed"
    return "free"


def collect_trace_variables(
    source: str,
    source_format: str,
    max_table_items: int = 1000,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Return (label, COBOL reference) pairs for scalar fields, groups and tables."""
    program = cobol2py.parse_cobol(source, source_format=source_format)
    variables = program.variables
    name_counts: dict[str, int] = {}
    for variable in variables:
        name_counts[variable.name] = name_counts.get(variable.name, 0) + 1

    variables_by_name = {
        variable.name: variable
        for variable in variables
        if name_counts[variable.name] == 1
    }
    children_by_parent: dict[str, list[cobol2py.CobolVar]] = {}
    for variable in variables:
        if variable.parent_name:
            children_by_parent.setdefault(variable.parent_name, []).append(variable)

    skipped: list[str] = []
    for name, count in name_counts.items():
        if count > 1:
            skipped.append(f"{name}: duplicate data-name ({count} declarations; ambiguous qualification)")

    trace_entries: list[tuple[str, str]] = []
    visited: set[str] = set()

    def qualified_reference(
        variable: cobol2py.CobolVar,
        own_index: Optional[int],
        ancestor_indices: dict[str, int],
    ) -> str:
        reference = variable.name
        if own_index is not None:
            reference += f"({own_index})"
        parent_name = variable.parent_name
        while parent_name:
            parent = variables_by_name.get(parent_name)
            if parent is None:
                break
            parent_index = ancestor_indices.get(parent.name)
            qualifier = parent.name + (f"({parent_index})" if parent_index is not None else "")
            reference += f" OF {qualifier}"
            parent_name = parent.parent_name
        return reference

    def visit(variable: cobol2py.CobolVar, ancestor_indices: dict[str, int]) -> None:
        if variable.name == "FILLER":
            skipped.append("FILLER: unnamed field")
            return
        if name_counts.get(variable.name, 0) > 1:
            return
        if variable.name in visited and not variable.parent_name:
            return
        visited.add(variable.name)

        if variable.is_array:
            count = variable.occurs or 0
            if count <= 0:
                skipped.append(f"{variable.name}: OCCURS count could not be determined")
                return
            if count > max_table_items:
                skipped.append(
                    f"{variable.name}: {count} OCCURS elements exceeds --max-table-items {max_table_items}"
                )
                return
            for index in range(1, count + 1):
                ref = qualified_reference(variable, index, ancestor_indices)
                trace_entries.append((ref, ref))
                if variable.is_group:
                    nested_indices = dict(ancestor_indices)
                    nested_indices[variable.name] = index
                    for child in children_by_parent.get(variable.name, []):
                        visit(child, nested_indices)
            return

        ref = qualified_reference(variable, None, ancestor_indices)
        trace_entries.append((ref, ref))
        if variable.is_group:
            for child in children_by_parent.get(variable.name, []):
                visit(child, ancestor_indices)

    for variable in variables:
        if not variable.parent_name:
            visit(variable, {})
    if not trace_entries:
        skipped.append("No traceable data items were found.")
    return trace_entries, skipped

def instrument_source(
    source: str,
    source_format: str = "auto",
    copybook_paths: Optional[list[str | Path]] = None,
    source_path: Optional[str | Path] = None,
    max_table_items: int = 1000,
) -> tuple[str, list[str], list[str], list[str], str]:
    """Expand COPYs and inject one DISPLAY snapshot per scalar variable."""
    expanded, unresolved_copybooks = cobol2py.resolve_copybooks(
        source,
        copybook_paths=copybook_paths,
        source_path=source_path,
        max_table_items=max_table_items,
    )
    actual_format = detect_source_format(expanded) if source_format == "auto" else source_format
    trace_entries, skipped = collect_trace_variables(expanded, actual_format, max_table_items)
    variables = [label for label, _ in trace_entries]

    prefix = "       " if actual_format == "fixed" else "    "
    snapshot = [
        f'{prefix}DISPLAY "TRACE_VAR|{label}|" {reference}.'
        for label, reference in trace_entries
    ]
    terminal = re.compile(r"^\s*(?:(?:\d{6})\s+)?(?:STOP\s+RUN|GOBACK|EXIT\s+PROGRAM)\b", re.IGNORECASE)
    end_program = re.compile(r"^\s*(?:(?:\d{6})\s+)?END\s+PROGRAM\b", re.IGNORECASE)
    output: list[str] = []
    inserted = False
    for line in expanded.splitlines():
        code = line.split("*>", 1)[0]
        if not inserted and terminal.match(code):
            output.extend(snapshot)
            inserted = True
        elif not inserted and end_program.match(code):
            output.extend(snapshot)
            inserted = True
        output.append(line)
    if not inserted:
        output.extend(snapshot)
    return "\n".join(output) + "\n", variables, skipped, unresolved_copybooks, actual_format


def run_trace(
    source_path: Path,
    source_format: str,
    copybook_paths: list[Path],
    timeout: int,
    max_table_items: int,
) -> int:
    if shutil.which("cobc") is None:
        print("ERROR: GnuCOBOL compiler 'cobc' not found on PATH.", file=sys.stderr)
        return 127

    try:
        source = source_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"ERROR: cannot read {source_path}: {exc}", file=sys.stderr)
        return 2

    instrumented, variables, skipped, unresolved, actual_format = instrument_source(
        source,
        source_format=source_format,
        copybook_paths=copybook_paths,
        source_path=source_path,
    )
    if unresolved:
        print("WARNING: copybook resolution diagnostics:", file=sys.stderr)
        for item in unresolved:
            print(f"  - {item}", file=sys.stderr)

    with tempfile.TemporaryDirectory(prefix="cobol2py-trace-") as temp_dir:
        temp = Path(temp_dir)
        instrumented_path = temp / "trace_program.cbl"
        executable = temp / "trace_program"
        instrumented_path.write_text(instrumented, encoding="utf-8")
        command = ["cobc", "-x", "-ftraceall"]
        if actual_format == "free":
            command.append("-free")
        for path in [source_path.resolve().parent, *(p.resolve() for p in copybook_paths)]:
            command.extend(["-I", str(path)])
        command.extend(["-o", str(executable), str(instrumented_path)])
        compiled = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if compiled.stdout:
            print(compiled.stdout, end="", file=sys.stderr)
        if compiled.stderr:
            print(compiled.stderr, end="", file=sys.stderr)
        if compiled.returncode != 0:
            return compiled.returncode

        env = os.environ.copy()
        env["COB_SET_TRACE"] = "Y"
        try:
            executed = subprocess.run(
                [str(executable)],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print(f"ERROR: program exceeded timeout ({timeout}s).", file=sys.stderr)
            return 124

        # Program output, including TRACE_VAR lines, remains on stdout.
        print(executed.stdout, end="")
        if executed.stderr:
            print("=== GnuCOBOL runtime trace (stderr) ===", file=sys.stderr)
            print(executed.stderr, end="", file=sys.stderr)
        if skipped:
            print("=== Variables not traced ===", file=sys.stderr)
            for item in skipped:
                print(f"  - {item}", file=sys.stderr)
        print(
            f"Trace summary: {len(variables)} scalar variable(s); "
            f"{len(skipped)} skipped item(s).",
            file=sys.stderr,
        )
        return executed.returncode


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run COBOL with GnuCOBOL trace and variable snapshots.")
    parser.add_argument("source", type=Path, help="COBOL source file")
    parser.add_argument("--format", choices=("auto", "fixed", "free"), default="auto")
    parser.add_argument("--copybook-path", action="append", type=Path, default=[])
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-table-items", type=int, default=1000, help="Maximum OCCURS entries to snapshot per table")
    args = parser.parse_args(argv)
    if args.timeout < 1:
        parser.error("--timeout must be at least 1 second")
    if args.max_table_items < 1:
        parser.error("--max-table-items must be at least 1")
    return run_trace(args.source, args.format, args.copybook_path, args.timeout, args.max_table_items)


if __name__ == "__main__":
    raise SystemExit(main())
