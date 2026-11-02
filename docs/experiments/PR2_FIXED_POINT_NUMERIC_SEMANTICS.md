# PR2 — Fixed-point numeric semantics

## Repository adaptation
Numeric parsing, PIC interpretation and Python emission currently live in `cobol2py.py` (not a separate `codegen/` tree). Preserve the public single-file CLI and keep new runtime helpers in a small stdlib-only module only if the import path remains valid in the isolated benchmark container.

## Deliverables
1. Define decimal scale, precision, sign, truncation/rounding and overflow behavior for supported PIC clauses.
2. Implement a fixed-point representation or Decimal-backed helper with explicit COBOL-compatible operations.
3. Migrate only numeric PIC/arithmetic paths covered by tests; do not silently convert unrelated numeric expressions.
4. Add differential fixtures against GnuCOBOL for MOVE, ADD, SUBTRACT, MULTIPLY, DIVIDE, COMPUTE and edited numeric output.

## Acceptance
- Tests cover positive/negative values, implied decimal, scale alignment, truncation, rounding and size boundaries.
- Generated Python compiles and preserves existing supported outputs.
- No float conversion on a path declared exact-decimal.
- Official 500-case score must be rerun; no change to record unless it strictly exceeds 242/500 with a complete checksum-valid sample.