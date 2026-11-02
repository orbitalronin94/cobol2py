# INITIALIZE semantics experiment

## Hypothesis
INITIALIZE may diverge for category-specific defaults, REPLACING clauses, and nested groups.

## Required behavior
- Set alphanumeric/alphabetic items to spaces and numeric items to zero as required.
- Respect category exclusions such as FILLER and selected REPLACING targets.
- Traverse nested groups and OCCURS items consistently.
- Apply REPLACING by category without touching excluded items.

## Acceptance matrix
- Basic group and elementary initialization.
- WITH FILLER and nested OCCURS.
- REPLACING ALPHANUMERIC, ALPHABETIC, NUMERIC, and category-specific values.
- Items with VALUE clauses and REDEFINES.
- Signed and edited numeric PIC declarations.

## Measurement
Use GnuCOBOL output as the oracle and require a valid complete 500-case holdout for any score claim.