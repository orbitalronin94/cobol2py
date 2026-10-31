from __future__ import annotations

import json

from ronin.behavioral_spec_graph import BehavioralSpecGraph
from ronin.compiler_guided_repair import repair_python_source
from ronin.smt_feedback_loop import propose_local_repair
from ronin.symbolic_executor import delta_debug_input, generate_path_cases
from ronin.repair_pipeline import RepairPipeline


def test_behavioral_graph_captures_rules_and_io():
    graph = BehavioralSpecGraph.from_cobol(
        "IF AMOUNT > 50\n MOVE 10 TO DISCOUNT\nEND-IF\nDISPLAY DISCOUNT")
    kinds = {node.kind for node in graph.nodes}
    assert {"condition", "transform", "output"} <= kinds
    assert graph.source_map()[1] == "n1"
    assert json.loads(graph.to_json())["schema_version"] == 1


def test_compiler_guided_local_repair():
    result = repair_python_source("print(x = 1)\n")
    assert result.compiled
    assert result.source == "x = 1\nprint(x)\n"


def test_reciprocal_repair_is_narrow():
    assert propose_local_repair("A / 3", "A * 0.333") == "A / 3"
    assert propose_local_repair("A + 3", "A * 0.333") is None


def test_symbolic_cases_cover_both_branches():
    cases = generate_path_cases("IF AMOUNT > 50")
    assert {case.branch for case in cases} == {"true", "false"}
    assert all("AMOUNT" in case.inputs for case in cases)


def test_delta_debugging_reduces_failure():
    source = "keep\nremove\nkeep-too\n"
    result = delta_debug_input(source, lambda candidate: "keep" in candidate)
    assert "keep" in result.minimized
    assert len(result.minimized) < len(source)


def test_pipeline_reports_compiler_repair(tmp_path):
    report = tmp_path / "repair_report.json"
    pipeline = RepairPipeline(report_path=report)
    result = pipeline.repair_case("syntax-1", "print(x = 1)\n")
    assert result.repaired
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["cases"][0]["technique"] == "compiler"
