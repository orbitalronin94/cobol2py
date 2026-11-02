# Decimal arithmetic and size-error experiment

## Hypothesis
Arithmetic may diverge for intermediate decimal precision, ROUNDED, ON SIZE ERROR, and receiver truncation.

## Required behavior
- Preserve COBOL decimal scaling through intermediate calculations.
- Apply ROUNDED at the receiving item boundary.
- Select ON SIZE ERROR / NOT ON SIZE ERROR correctly.
- Keep the receiver unchanged on size error where COBOL requires it.
- Respect signed, implied-decimal, and edited PIC formats.

## Acceptance matrix
- ADD, SUBTRACT, MULTIPLY, DIVIDE, and COMPUTE.
- ROUNDED with positive and negative halfway values.
- ON SIZE ERROR and NOT ON SIZE ERROR.
- Truncation into smaller integer/decimal receivers.
- Intermediate precision versus final receiver precision.

## Measurement
Add exact-output and return-code comparisons against GnuCOBOL. Only a valid complete 500-case holdout can establish a new record.