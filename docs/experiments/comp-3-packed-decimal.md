# Experiment: COMP-3 packed decimal

## Hypothesis
Packed-decimal declarations may be represented as ordinary Python numbers while losing scale, sign, precision, or rounding behavior required by COBOL.

## Scope
- PIC with implied decimal and COMP-3
- Positive and negative values, including signed zero
- MOVE between packed and display numeric items
- ADD/SUBTRACT/COMPUTE with scale alignment
- ROUNDED and SIZE ERROR interaction (coordinate with decimal-arithmetic experiment)

## Regression fixtures
Use values at precision boundaries, fractional carries, negative values, and overflow. Compare DISPLAY formatting and final numeric storage with GnuCOBOL.

## Acceptance criteria
- Decimal scale and declared precision are preserved.
- No binary floating-point drift in packed-decimal operations.
- Sign, rounding, and overflow behavior are tested independently.
- Unsupported picture/storage combinations produce explicit diagnostics.

## Risks
Do not assume Python float is a valid packed-decimal representation; use exact decimal/integer scaling where appropriate.