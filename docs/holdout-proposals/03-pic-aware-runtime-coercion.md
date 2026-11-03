# Proposal 03 — PIC-aware runtime conversion and comparison

## Evidence from holdout run #542
https://github.com/orbitalronin94/cobol2py/actions/runs/41609868400
The four shards recorded 18 ValueError and 15 TypeError exceptions. The historical triage includes a concrete ValueError converting alphanumeric group data to int (NC109M) and a str/int comparison failure (NC2154.2). These point to Python coercions being used without consulting COBOL storage categories.

## Proposed solution
Centralize conversions and comparisons in a compatibility layer driven by parsed PIC metadata. Distinguish alphanumeric, numeric display, signed numeric, implied-decimal, edited numeric and group storage. Use exact decimal/fixed-point operations for supported numeric PICs. Preserve character/byte storage and apply COBOL field sizing for alphanumeric and group items. Comparisons must use operand categories and documented padding rules.

## Scope
- Replace ad hoc int(str(...)) and float(...) on PIC-aware paths with explicit helpers.
- Keep group MOVE separate from elementary numeric MOVE.
- Define invalid numeric content and overflow; never silently coerce invalid text to zero.
- Do not change unrelated Python-native values or unsupported PIC forms.

## Regression plan
Numeric/alphanumeric fields containing digits, spaces, signs, edited symbols and invalid text; group/element MOVE; signed and implied decimals; truncation, rounding and size boundaries; mixed-category comparisons; divide-by-zero. Compare output and return status with GnuCOBOL.

## Acceptance
No ValueError/TypeError for newly supported cases; no binary-float rounding on exact-decimal paths; invalid data follows documented semantics or a stable diagnostic; unit suite and unchanged 500-case holdout run on exact SHA.