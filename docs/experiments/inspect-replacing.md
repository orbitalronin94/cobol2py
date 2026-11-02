# INSPECT semantics experiment

## Hypothesis
The translator may diverge from GnuCOBOL for INSPECT TALLYING, REPLACING, and combined TALLYING/REPLACING operations, especially with repeated substrings and multiple tally clauses.

## Required behavior
- Count every non-overlapping occurrence according to COBOL INSPECT rules.
- Apply REPLACING only to the selected characters/occurrences.
- Preserve the original item length and padding behavior.
- Keep tally and replacement results independent when both appear in one statement.

## Acceptance matrix
- TALLYING ALL and CHARACTERS.
- REPLACING ALL, FIRST, and LEADING.
- Multiple BEFORE/AFTER INITIAL boundaries.
- Multiple tally identifiers and multiple replacement pairs.
- Empty strings, repeated characters, and fixed-width PIC X operands.

## Measurement
Add executable regression cases against GnuCOBOL, then run the full 500-case external holdout. Do not claim a score from the 50-case fast screen.