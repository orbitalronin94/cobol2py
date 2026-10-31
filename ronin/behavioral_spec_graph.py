"""Inspectable behavioural specification extracted from COBOL source text.

The graph is intentionally source-oriented because cobol2py currently exposes no
stable public COBOL AST. Nodes retain line numbers and exact source statements;
unsupported constructs remain visible as 'statement' nodes instead of vanishing.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import re
from typing import Any


@dataclass
class SpecNode:
    id: str
    kind: str
    line: int
    source: str
    attributes: dict[str, Any]


@dataclass
class SpecEdge:
    source: str
    target: str
    relation: str


class BehavioralSpecGraph:
    """Source-traceable graph of business conditions, mutations and I/O."""
    def __init__(self) -> None:
        self.nodes: list[SpecNode] = []
        self.edges: list[SpecEdge] = []

    @classmethod
    def from_cobol(cls, source: str) -> "BehavioralSpecGraph":
        graph = cls()
        patterns = [
            ("condition", re.compile(r"^\s*(IF|ELSE|EVALUATE|WHEN|END-IF|END-EVALUATE)\b", re.I)),
            ("transform", re.compile(r"^\s*(MOVE|COMPUTE|ADD|SUBTRACT|MULTIPLY|DIVIDE|INITIALIZE|SET)\b", re.I)),
            ("control", re.compile(r"^\s*(PERFORM|GO\s+TO|GOTO|EXIT\s+PERFORM|STOP\s+RUN|GOBACK)\b", re.I)),
            ("input", re.compile(r"^\s*ACCEPT\b", re.I)),
            ("output", re.compile(r"^\s*DISPLAY\b", re.I)),
            ("io", re.compile(r"^\s*(OPEN|READ|WRITE|REWRITE|DELETE|CLOSE|START)\b", re.I)),
            ("declaration", re.compile(r"^\s*(\d{1,2}\s+\S+|COPY\b|REPLACE\b)", re.I)),
        ]
        for line_no, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("*>", "*>")):
                continue
            for kind, pattern in patterns:
                match = pattern.search(line)
                if match:
                    verb = re.sub(r"\s+", " ", match.group(0).strip().upper())
                    graph.nodes.append(SpecNode(
                        id=f"n{len(graph.nodes) + 1}", kind=kind, line=line_no,
                        source=stripped, attributes={"verb": verb}))
                    break
            else:
                # Preserve unclassified non-structural statements for audit.
                if re.match(r"^\s*(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\b", line, re.I):
                    continue
                graph.nodes.append(SpecNode(
                    id=f"n{len(graph.nodes) + 1}", kind="statement", line=line_no,
                    source=stripped, attributes={}))
        # Sequential source order is a conservative control-flow approximation.
        for left, right in zip(graph.nodes, graph.nodes[1:]):
            graph.edges.append(SpecEdge(left.id, right.id, "next"))
        return graph

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": 1,
                "nodes": [asdict(node) for node in self.nodes],
                "edges": [asdict(edge) for edge in self.edges]}

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_markdown(self) -> str:
        lines = ["# COBOL Behavioural Specification", "",
                 "| ID | Line | Kind | Source |", "|---|---:|---|---|"]
        for node in self.nodes:
            source = node.source.replace("|", "\\|")
            lines.append(f"| {node.id} | {node.line} | {node.kind} | `{source}` |")
        lines += ["", "## Sequential trace", ""]
        lines.extend(f"- {edge.source} --{edge.relation}--> {edge.target}" for edge in self.edges)
        return "\n".join(lines) + "\n"

    def source_map(self) -> dict[int, str]:
        """Map source line numbers to stable graph node IDs for code comments."""
        return {node.line: node.id for node in self.nodes}
