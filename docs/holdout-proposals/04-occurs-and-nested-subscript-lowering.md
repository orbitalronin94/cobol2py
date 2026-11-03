# Proposal 04 — Structured OCCURS and nested subscript lowering

## Evidence from holdout run #542
https://github.com/orbitalronin94/cobol2py/actions/runs/41609868400
Generated diagnostics include malformed paths such as (inxex1 inxex2 inxex3) - 1, s32 s33 - 1 and 1 index3 - 1. Runtime KeyError/TypeError failures also occur. Historical triage records a list/string indexing TypeError (NC235A); the existing accuracy analysis identifies 1-based COBOL subscripts and nested OCCURS tables as a risk.

## Proposed solution
Parse a table reference as a structured path: base item, nested group/table components and each subscript expression. Lower every subscript independently and convert its 1-based value to the host index exactly once at the access boundary. Preserve declared OCCURS dimensions and validate supplied subscript count. Keep element representation consistent; do not emit a list for one declaration path and a scalar/string for another.

## Scope
- Parse arithmetic subscript expressions rather than concatenating source tokens.
- Resolve each nested OCCURS level from declaration metadata.
- Preserve index-vs-subscript distinction where supported.
- Define out-of-range behavior; do not silently clamp.

## Regression plan
One-dimensional and nested tables; first/last valid entries; arithmetic and multiple independent subscripts; repeated access; group elements; index variables; out-of-range references. Assert generated Python compiles and read/write results match GnuCOBOL.

## Acceptance
No malformed Python from adjacent subscript tokens; no list/string shape mismatch for supported declarations; each COBOL subscript is converted once; unit suite and unchanged 500-case holdout on exact SHA.