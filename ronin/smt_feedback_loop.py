"""Bounded SMT-guided repair primitives for COBOL arithmetic translations.

This module is deliberately opt-in: it never edits a translator output unless a
caller supplies the exact COBOL/Python expression pair and accepts a verified
candidate. Z3 is optional; without it, only the narrow local repair rules run.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import ast
import re
from typing import Callable, Mapping, Optional

try:
    import z3  # type: ignore
except ImportError:  # optional dependency
    z3 = None


@dataclass
class SMTResult:
    status: str
    counterexample: dict[str, int | float] | None = None
    reason: str = ""


@dataclass
class RepairResult:
    expression: str
    repaired: bool
    iterations: int
    status: str
    diagnostics: list[dict]


_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)


def _validate_expr(source: str) -> ast.Expression:
    tree = ast.parse(source, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and not isinstance(node.op, _ALLOWED_BINOPS):
            raise ValueError("unsupported arithmetic operator")
        if isinstance(node, ast.UnaryOp) and not isinstance(node.op, _ALLOWED_UNARY):
            raise ValueError("unsupported unary operator")
        if not isinstance(node, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name,
                                 ast.Load, ast.Constant, *_ALLOWED_BINOPS, *_ALLOWED_UNARY)):
            raise ValueError(f"unsupported expression node: {type(node).__name__}")
    return tree


def _to_z3(node: ast.AST, symbols: dict[str, object]):
    if z3 is None:
        raise RuntimeError("z3-solver is not installed")
    if isinstance(node, ast.Expression):
        return _to_z3(node.body, symbols)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        # Rational arithmetic avoids floating point rounding in the checker.
        if isinstance(node.value, float):
            return z3.RealVal(str(node.value))
        return z3.IntVal(node.value)
    if isinstance(node, ast.Name):
        return symbols.setdefault(node.id, z3.Real(node.id))
    if isinstance(node, ast.UnaryOp):
        value = _to_z3(node.operand, symbols)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        left, right = _to_z3(node.left, symbols), _to_z3(node.right, symbols)
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        if isinstance(node.op, ast.Mult): return left * right
        if isinstance(node.op, ast.Div): return left / right
        if isinstance(node.op, ast.FloorDiv): return left / right
        if isinstance(node.op, ast.Mod): return left % right
        if isinstance(node.op, ast.Pow) and isinstance(node.right, ast.Constant) and isinstance(node.right.value, int):
            return left ** right.value
    raise ValueError("expression is outside the supported SMT arithmetic subset")


def check_equivalence(cobol_expr: str, python_expr: str, timeout_ms: int = 500) -> SMTResult:
    """Check arithmetic equivalence over real-valued inputs where supported."""
    if z3 is None:
        return SMTResult("unavailable", reason="optional dependency z3-solver is not installed")
    try:
        left_tree, right_tree = _validate_expr(cobol_expr), _validate_expr(python_expr)
        symbols: dict[str, object] = {}
        left, right = _to_z3(left_tree, symbols), _to_z3(right_tree, symbols)
        solver = z3.Solver()
        solver.set(timeout=timeout_ms)
        solver.add(left != right)
        result = solver.check()
        if result == z3.unsat:
            return SMTResult("equivalent")
        if result == z3.unknown:
            return SMTResult("unknown", reason=solver.reason_unknown())
        model = solver.model()
        values = {}
        for name, symbol in symbols.items():
            value = model.eval(symbol, model_completion=True)
            try:
                values[name] = float(value.as_fraction())
                if values[name].is_integer(): values[name] = int(values[name])
            except Exception:
                values[name] = str(value)
        return SMTResult("sat", values)
    except Exception as exc:
        return SMTResult("unsupported", reason=str(exc))


def propose_local_repair(cobol_expr: str, python_expr: str) -> str | None:
    """Repair only a clearly recognizable decimal-reciprocal substitution."""
    cobol = re.sub(r"\s+", "", cobol_expr).upper()
    py = re.sub(r"\s+", "", python_expr)
    # A / integer must not be approximated by multiplying a rounded reciprocal.
    match = re.fullmatch(r"([A-Za-z_]\w*)/([1-9]\d*)", cobol)
    if match:
        name, denominator = match.groups()
        if re.fullmatch(re.escape(name) + r"\*0?\.\d+", py, re.I):
            return f"{name} / {denominator}"
        if re.fullmatch(re.escape(name) + r"\*\(?0?\.\d+\)?", py, re.I):
            return f"{name} / {denominator}"
    return None


def repair_expression(
    cobol_expr: str,
    python_expr: str,
    *,
    expected_output: str | None = None,
    repairer: Callable[[str, str, Mapping[str, int | float], str | None], str | None] | None = None,
    max_iterations: int = 3,
    timeout_ms: int = 500,
) -> RepairResult:
    """Try bounded repairs and commit only when the checker proves equivalence."""
    current = python_expr
    diagnostics: list[dict] = []
    for iteration in range(1, max(0, min(max_iterations, 3)) + 1):
        check = check_equivalence(cobol_expr, current, timeout_ms)
        diagnostics.append({"iteration": iteration, "expression": current, **asdict(check)})
        if check.status == "equivalent":
            return RepairResult(current, current != python_expr, iteration - 1, "verified", diagnostics)
        if check.status not in ("sat", "unsupported") or iteration == max_iterations:
            break
        candidate = propose_local_repair(cobol_expr, current)
        if candidate is None and repairer is not None:
            candidate = repairer(cobol_expr, current, check.counterexample or {}, expected_output)
        if not candidate or candidate == current:
            break
        current = candidate
    final = check_equivalence(cobol_expr, current, timeout_ms)
    diagnostics.append({"iteration": len(diagnostics) + 1, "expression": current, **asdict(final)})
    if final.status == "equivalent":
        return RepairResult(current, current != python_expr, len(diagnostics) - 1, "verified", diagnostics)
    return RepairResult(python_expr, False, len(diagnostics), final.status, diagnostics)
