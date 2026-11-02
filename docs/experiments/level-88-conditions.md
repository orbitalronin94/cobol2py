# Experiment: Level-88 condition names

## Hypothesis
Condition names with single values, ranges, and multiple VALUE clauses may be mis-expanded in IF, EVALUATE, SET, and qualified references.

## Scope
- Single VALUE and VALUE THRU/THROUGH
- Multiple VALUE clauses
- NOT condition-name
- Qualified condition names and duplicate names under different parents
- SET condition-name TO TRUE where supported

## Regression fixtures
Cover numeric and alphanumeric parents, overlapping ranges, boundary values, duplicate condition names, and parent qualification. Compare truth values and resulting parent storage with GnuCOBOL.

## Acceptance criteria
- Every condition name resolves to its declared parent item.
- Inclusive range boundaries match COBOL behavior.
- Qualification is preserved when data-names collide.
- Unsupported SET forms are diagnosed rather than silently ignored.

## Risks
Do not conflate a level-88 name with a Python boolean variable; it is a condition over parent storage.