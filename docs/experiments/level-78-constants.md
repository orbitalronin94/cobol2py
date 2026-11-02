# Level-78 named constants

## Hypothesis
Resolve level-78 constant names consistently in expressions and conditions without treating them as mutable data items.

## Scope and regressions
- Integer, decimal, and alphanumeric constant values.
- Use in arithmetic, MOVE, conditions, and subscripts where legal.
- Qualified/name-collision behavior and source-order rules.
- Ensure generated Python never emits assignments to constants.

## Acceptance
Add GnuCOBOL-backed fixtures and unit tests. Run the complete external 500-program corpus on the exact candidate SHA. Merge only if the comparable result strictly exceeds 242/500 with unchanged corpus checksum and exact stdout/return-code comparison.