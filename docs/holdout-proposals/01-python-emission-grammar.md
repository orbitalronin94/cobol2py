# Proposal 01 — Safe Python emission from COBOL tokens

## Evidence from holdout run #542
https://github.com/orbitalronin94/cobol2py/actions/runs/41609868400
Across the four 125-case shards there were 39 generated-Python syntax errors. Concrete diagnostics include unexpected indentation, unterminated strings, invalid assignment targets such as 100 = ... and 864.36 = ..., malformed comparisons such as == >, and COBOL fragments emitted verbatim (numeric, FUNCTION EXP).

## Proposed solution
Add a validation boundary between COBOL parsing and Python emission. Normalize only recognized COBOL constructs; never pass unconsumed source fragments into Python expressions. Represent supported literals, identifiers, calls, comparisons and arithmetic as structured expression nodes, then emit Python from those nodes. Unsupported constructs should produce stable source-located diagnostics rather than malformed Python. Compile every generated module in regression tests.

## Scope
- Audit reserved-word, relational-operator, intrinsic-call and literal-escaping paths.
- Keep comments and quoted literals opaque to normalization.
- Prevent numeric literals from becoming assignment targets.
- Avoid broad regex rewrites over already-generated Python.

## Regression plan
Fixtures for IS NUMERIC, IS NOT NUMERIC, relational operators, NOT, nested expressions, FUNCTION EXP, apostrophes, multiline literals, decimal literals and fixed-format continuation. Assert valid Python for supported forms and precise diagnostics for unsupported forms.

## Acceptance
All supported fixtures compile; unsupported forms fail deterministically with source context; existing tests pass; rerun the unchanged 500-case holdout on the exact candidate SHA. No accuracy gain is claimed by this proposal.