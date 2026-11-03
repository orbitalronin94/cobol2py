# PR3 — Typed IR and Python AST emission

## Repository adaptation
The current translator uses `Program`, `CobolVar`, `Node`, `build_tree`, `parse_procedure` and direct Python string emission in `cobol2py.py`. Introduce an intermediate layer incrementally; do not assume the proposed `src/translator/codegen` layout exists.

## Deliverables
1. Define typed IR nodes for the currently supported statements and expressions.
2. Add a compatibility adapter from existing `Node`/data models to typed IR.
3. Emit Python with `ast` nodes and `ast.unparse` (stdlib), or a deterministic AST-to-source emitter if target Python compatibility requires it.
4. Preserve source line metadata for diagnostics.
5. Fix at least 20 reproducible generated-Python syntax failures from the diagnostic corpus, with regression fixtures that do not redistribute third-party corpus source.

## Acceptance
- Existing CLI output remains deterministic.
- Generated modules pass `ast.parse` and `compile`.
- Golden tests cover all migrated IR nodes.
- Unsupported nodes fail with stable diagnostics rather than malformed Python.
- Full unit suite and 500-case exact benchmark are reported.