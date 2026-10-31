"""Compiler-diagnostic guided, local-only Python repair.

No code is executed. The candidate is accepted only after py_compile succeeds.
The default repairs are deliberately narrow; projects can inject a repairer if
they have a trusted offline model or rule engine.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import py_compile
import re
import tempfile
from pathlib import Path
from typing import Callable


@dataclass
class CompileRepairResult:
    source: str
    compiled: bool
    iterations: int
    status: str
    diagnostics: list[dict]


def _compile(source: str) -> tuple[bool, dict]:
    with tempfile.TemporaryDirectory(prefix="cobol2py-compile-check-") as tmp:
        path = Path(tmp) / "candidate.py"
        path.write_text(source, encoding="utf-8")
        try:
            py_compile.compile(str(path), doraise=True, cfile=str(Path(tmp) / "candidate.pyc"))
            return True, {"message": "", "line": None, "source_line": None}
        except py_compile.PyCompileError as exc:
            line = getattr(exc.exc_value, "lineno", None)
            lines = source.splitlines()
            offending = lines[line - 1] if line and 0 < line <= len(lines) else None
            return False, {"message": str(exc), "line": line, "source_line": offending}


def _local_repair(source: str, diagnostic: dict) -> str | None:
    line = diagnostic.get("line")
    if not line:
        return None
    lines = source.splitlines()
    if not 0 < line <= len(lines):
        return None
    offending = lines[line - 1]
    # A common invalid generated form: print(x = value), where the intent is
    # assignment followed by output. Keep the rewrite restricted to this shape.
    match = re.fullmatch(r"(\s*)print\(\s*([A-Za-z_]\w*)\s*=\s*([^()]*)\s*\)\s*", offending)
    if match:
        indent, name, value = match.groups()
        lines[line - 1:line] = [f"{indent}{name} = {value}", f"{indent}print({name})"]
        return "\n".join(lines) + ("\n" if source.endswith("\n") else "")
    return None


def repair_python_source(
    source: str,
    *,
    repairer: Callable[[str, dict], str | None] | None = None,
    max_iterations: int = 2,
) -> CompileRepairResult:
    current = source
    diagnostics: list[dict] = []
    for iteration in range(max(0, min(max_iterations, 2)) + 1):
        ok, diagnostic = _compile(current)
        diagnostics.append({"iteration": iteration, **diagnostic, "compiled": ok})
        if ok:
            return CompileRepairResult(current, True, iteration, "compiled", diagnostics)
        if iteration >= max_iterations:
            break
        candidate = _local_repair(current, diagnostic)
        if candidate is None and repairer is not None:
            candidate = repairer(current, diagnostic)
        if not candidate or candidate == current:
            break
        current = candidate
    return CompileRepairResult(source, False, len(diagnostics) - 1,
                               "FAILED_COMPILATION", diagnostics)
