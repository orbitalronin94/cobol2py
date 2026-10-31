"""Small, bounded path-constraint and delta-debugging utilities.

This is an adapter layer, not a replacement COBOL parser. Callers provide parsed
conditions or a callback that executes a candidate input against both programs.
Unsupported COBOL expressions are reported rather than guessed.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Callable, Iterable, Mapping


@dataclass
class PathCase:
    condition: str
    branch: str
    inputs: dict[str, int | float]
    solver_status: str


@dataclass
class DeltaResult:
    minimized: str
    original_size: int
    minimized_size: int
    reductions: int


_CONDITION = re.compile(
    r"(?im)^\s*IF\s+([A-Z0-9_-]+)\s*(>=|<=|<>|!=|=|>|<)\s*(-?\d+(?:\.\d+)?)"
)


def generate_path_cases(source: str, timeout_ms: int = 500) -> list[PathCase]:
    """Generate concrete boundary cases for simple numeric IF conditions.

    When z3-solver is installed, both true and false path constraints are solved.
    A deterministic boundary heuristic is used otherwise.
    """
    conditions = [(m.group(1), m.group(2), m.group(3), m.group(0).strip())
                  for m in _CONDITION.finditer(source)]
    cases: list[PathCase] = []
    try:
        import z3  # type: ignore
    except ImportError:
        z3 = None
    for name, op, raw, original in conditions:
        value = float(raw) if "." in raw else int(raw)
        for branch, truth in (("true", True), ("false", False)):
            if z3 is not None:
                var = z3.Real(name)
                rhs = z3.RealVal(str(value))
                expr = {">": var > rhs, "<": var < rhs, ">=": var >= rhs,
                        "<=": var <= rhs, "=": var == rhs, "!=": var != rhs,
                        "<>": var != rhs}[op]
                solver = z3.Solver()
                solver.set(timeout=timeout_ms)
                solver.add(expr if truth else z3.Not(expr))
                status = solver.check()
                if status != z3.sat:
                    continue
                model_value = solver.model().eval(var, model_completion=True)
                try:
                    val = float(model_value.as_fraction())
                    if val.is_integer(): val = int(val)
                except Exception:
                    continue
                cases.append(PathCase(original, branch, {name: val}, str(status)))
            else:
                # Prefer values immediately around the boundary; this is not a
                # proof of path feasibility and is labelled heuristic.
                delta = 1 if isinstance(value, int) else 0.1
                true_val = value + delta if op in (">", ">=", "!=", "<>") else value - delta
                if op == "=": true_val = value
                false_val = value + delta if true_val == value else value
                cases.append(PathCase(original, branch,
                                      {name: true_val if truth else false_val}, "heuristic"))
    return cases


def delta_debug_input(text: str, still_fails: Callable[[str], bool]) -> DeltaResult:
    """Reduce newline-delimited input using bounded ddmin while preserving failure."""
    lines = text.splitlines(keepends=True)
    original_size = len(text)
    if not lines or not still_fails(text):
        return DeltaResult(text, original_size, original_size, 0)
    current = lines[:]
    granularity = 2
    reductions = 0
    while len(current) >= 2:
        chunk_size = max(1, (len(current) + granularity - 1) // granularity)
        reduced = False
        for start in range(0, len(current), chunk_size):
            candidate = current[:start] + current[start + chunk_size:]
            if candidate and still_fails("".join(candidate)):
                current = candidate
                granularity = max(2, granularity - 1)
                reductions += 1
                reduced = True
                break
        if not reduced:
            if granularity >= len(current):
                break
            granularity = min(len(current), granularity * 2)
    result = "".join(current)
    return DeltaResult(result, original_size, len(result), reductions)


def compare_generated_cases(cases: Iterable[PathCase],
                            execute_pair: Callable[[Mapping[str, int | float]], tuple[str, str]]) -> list[dict]:
    """Run supplied COBOL/Python adapters and return only discrepancies."""
    failures = []
    for case in cases:
        try:
            reference, translated = execute_pair(case.inputs)
        except Exception as exc:
            failures.append({"condition": case.condition, "branch": case.branch,
                             "inputs": case.inputs, "error": str(exc)})
            continue
        if reference != translated:
            failures.append({"condition": case.condition, "branch": case.branch,
                             "inputs": case.inputs, "reference": reference,
                             "translated": translated})
    return failures
