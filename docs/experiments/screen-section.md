# SCREEN SECTION and ACCEPT/DISPLAY fields

## Hypothesis
Translate basic SCREEN SECTION declarations and screen-oriented ACCEPT/DISPLAY operations while preserving field attributes and input/output behavior.

## Scope and regressions
- Screen coordinates, line/column positioning, and field sizes.
- Required/default input, prompt text, and cursor positioning.
- Numeric/alphanumeric input conversion and validation.
- Deterministic non-interactive fallback for automated tests.

## Acceptance
Add GnuCOBOL-backed fixtures where terminal behavior can be captured deterministically. Run the complete external 500-program corpus on the exact candidate SHA. Merge only if the comparable result strictly exceeds 242/500 with unchanged corpus checksum and exact stdout/return-code comparison.