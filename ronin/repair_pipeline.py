"""Budgeted repair orchestrator for the optional SOTA repair stages.

All powerful stages require explicit callbacks. This keeps the default translator
deterministic and dependency-light and prevents an experimental repair from being
silently integrated into the 500-case evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import time
from pathlib import Path
from typing import Callable, Mapping, Any

from .compiler_guided_repair import repair_python_source
from .smt_feedback_loop import repair_expression
from .symbolic_executor import delta_debug_input


@dataclass
class PipelineResult:
    source: str
    repaired: bool
    technique: str
    iterations: int
    status: str
    diagnostics: list[dict]


class RepairPipeline:
    def __init__(self, budget_seconds: float = 5.0, report_path: str | Path = "repair_report.json"):
        self.budget_seconds = max(0.05, float(budget_seconds))
        self.report_path = Path(report_path)
        self._report: list[dict[str, Any]] = []

    def repair_case(
        self,
        case_id: str,
        python_source: str,
        *,
        cobol_expression: str | None = None,
        python_expression: str | None = None,
        expected_output: str | None = None,
        compile_repairer: Callable[[str, dict], str | None] | None = None,
        smt_repairer: Callable[[str, str, Mapping[str, int | float], str | None], str | None] | None = None,
        failing_input: str | None = None,
        still_fails: Callable[[str], bool] | None = None,
    ) -> PipelineResult:
        started = time.monotonic()
        deadline = started + self.budget_seconds
        diagnostics: list[dict] = []
        current = python_source

        compile_result = repair_python_source(current, repairer=compile_repairer, max_iterations=2)
        diagnostics.append({"stage": "compiler", "status": compile_result.status,
                            "iterations": compile_result.iterations,
                            "diagnostics": compile_result.diagnostics})
        if compile_result.compiled and compile_result.source != python_source:
            result = PipelineResult(compile_result.source, True, "compiler",
                                    compile_result.iterations, "repaired", diagnostics)
            return self._finish(case_id, started, result)
        if not compile_result.compiled:
            # Do not feed syntactically invalid output to semantic checkers.
            return self._finish(case_id, started, PipelineResult(
                python_source, False, "none", compile_result.iterations,
                "FAILED_COMPILATION", diagnostics))

        if time.monotonic() < deadline and cobol_expression and python_expression:
            smt = repair_expression(cobol_expression, python_expression,
                                    expected_output=expected_output, repairer=smt_repairer,
                                    max_iterations=3, timeout_ms=max(25, int((deadline-time.monotonic())*1000)))
            diagnostics.append({"stage": "smt", "status": smt.status,
                                "iterations": smt.iterations, "diagnostics": smt.diagnostics})
            if smt.repaired and smt.status == "verified":
                # This API repairs an expression, so only substitute exact caller
                # supplied expression text; never guess at AST/source boundaries.
                current = current.replace(python_expression, smt.expression, 1)
                result = PipelineResult(current, True, "smt", smt.iterations, "repaired", diagnostics)
                return self._finish(case_id, started, result)

        if (time.monotonic() < deadline and failing_input is not None
                and still_fails is not None):
            minimized = delta_debug_input(failing_input, still_fails)
            diagnostics.append({"stage": "symbolic_delta", **asdict(minimized)})
            # Delta-debugging supplies a diagnostic only; it cannot safely rewrite
            # a translated program without an explicit semantics-preserving patch.
            if minimized.minimized != failing_input:
                result = PipelineResult(current, False, "symbolic_delta", minimized.reductions,
                                        "counterexample_minimized", diagnostics)
                return self._finish(case_id, started, result)

        return self._finish(case_id, started, PipelineResult(
            python_source, False, "none", 0, "unchanged", diagnostics))

    def _finish(self, case_id: str, started: float, result: PipelineResult) -> PipelineResult:
        record = {"case_id": case_id, **asdict(result),
                  "elapsed_seconds": round(time.monotonic() - started, 6)}
        self._report.append(record)
        self._write_report()
        return result

    def _write_report(self) -> None:
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.report_path.with_suffix(self.report_path.suffix + ".tmp")
        tmp.write_text(json.dumps({"schema_version": 1, "cases": self._report},
                                  indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(self.report_path)
