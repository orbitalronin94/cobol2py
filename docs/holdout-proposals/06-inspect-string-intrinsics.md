# Proposal 06 — Clause-aware INSPECT and STRING parsing

## Evidence from holdout run #542
https://github.com/orbitalronin94/cobol2py/actions/runs/41609868400
The holdout repeatedly emits malformed Python for COBOL string/INSPECT-like expressions. One generated line appears twice in a shard: str(...).count(str("a" before ... replacing ...)); other diagnostics show COBOL phrases leaking into Python. The run has 169 runtime/output mismatches overall, but this proposal does not assume all are string-related.

## Proposed solution
Give INSPECT and STRING clause-aware parsers and intermediate representations. Model TALLYING, REPLACING, CONVERTING, BEFORE INITIAL, AFTER INITIAL, DELIMITED BY, WITH POINTER and overflow branches only where explicitly supported. Preserve operand order, delimiter semantics and receiver sizing. Emit narrow runtime-helper calls instead of translating COBOL clause text into chained Python string methods.

## Scope
- Parse multiple INSPECT clauses in source order.
- Implement BEFORE/AFTER INITIAL as bounded slices with COBOL positioning semantics.
- Keep STRING pointer updates and overflow handling separate from UNSTRING.
- Reject unsupported combinations; do not approximate with str.count/replace.

## Regression plan
TALLYING, REPLACING, CONVERTING, BEFORE/AFTER INITIAL, repeated delimiters, pointer start positions, receiver capacity, ON OVERFLOW/NOT ON OVERFLOW, no-match and empty-operand boundaries. Compare output/state with GnuCOBOL.

## Acceptance
COBOL clause tokens never appear in generated Python expressions; supported operations match reference; unsupported forms produce deterministic diagnostics; unit suite and unchanged 500-case holdout on exact SHA.