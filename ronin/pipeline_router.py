"""Deterministic stage router for optional translation workflows.

This module has no LLM or external dependencies. It only chooses stages whose
input artifacts are available and whose subscription signals are live. It does
not execute stages or alter the default translator path.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


DEFAULT_CATALOG: dict[str, Any] = {
    "stages": {
        "parse": {
            "data": {"required": [], "output": ["ast"]},
            "signals": {"subscribes": [], "publishes": ["ast_ready"]},
        },
        "translate": {
            "data": {"required": ["ast"], "output": ["python"]},
            "signals": {"subscribes": ["ast_ready"], "publishes": ["python_ready"]},
        },
        "validate_syntax": {
            "data": {"required": ["python"], "output": ["valid_python"]},
            "signals": {"subscribes": ["python_ready"], "publishes": ["syntax_ok"]},
        },
        "execute": {
            "data": {"required": ["valid_python"], "output": ["stdout"]},
            "signals": {"subscribes": ["syntax_ok"], "publishes": ["executed"]},
        },
        "compare": {
            "data": {"required": ["stdout"], "output": ["result"]},
            "signals": {"subscribes": ["executed"], "publishes": ["benchmark_done"]},
        },
    }
}


def _matches(subscription: str, live_signals: set[str]) -> bool:
    return any(signal == subscription or signal.startswith(subscription + ":")
               for signal in live_signals)


def compose_route(
    catalog: Mapping[str, Any],
    live_signals: set[str] | frozenset[str],
    already_run: set[str] | frozenset[str] = frozenset(),
    available_artifacts: set[str] | frozenset[str] = frozenset(),
) -> list[str]:
    """Return a deterministic topological route; raise on blocked dependencies.

    A stage is eligible only when its signal subscription matches and all
    required artifacts are available. Outputs of a selected stage become
    available to later stages in the same route. Catalog insertion order breaks
    ties, keeping runs reproducible.
    """
    stages = catalog.get("stages")
    if not isinstance(stages, Mapping):
        raise ValueError("catalog must contain a stages mapping")

    live = set(live_signals)
    completed = set(already_run)
    available = set(available_artifacts)
    candidates: dict[str, Mapping[str, Any]] = {}
    for name, stage in stages.items():
        if name in completed:
            continue
        signals = stage.get("signals", {})
        subscriptions = signals.get("subscribes", [])
        if not subscriptions or any(_matches(str(sub), live) for sub in subscriptions):
            candidates[str(name)] = stage

    route: list[str] = []
    remaining = dict(candidates)
    while remaining:
        progressed = False
        for name, stage in list(remaining.items()):
            data = stage.get("data", {})
            required = set(data.get("required", []))
            if required.issubset(available):
                route.append(name)
                available.update(data.get("output", []))
                live.update(stage.get("signals", {}).get("publishes", []))
                del remaining[name]
                progressed = True
        if not progressed:
            blocked = {name: sorted(set(stage.get("data", {}).get("required", [])) - available)
                       for name, stage in remaining.items()}
            raise ValueError(f"unmet stage dependencies: {blocked}")
    return route
