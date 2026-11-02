# NATIONAL data and character encoding

## Hypothesis
Preserve COBOL NATIONAL/NATIONAL-EDITED data semantics and explicit character encoding rather than silently treating every field as ordinary single-byte text.

## Scope and regressions
- NATIONAL elementary and group items.
- MOVE, comparison, concatenation, and length behavior.
- Non-ASCII characters and code-point/byte-width distinctions.
- Numeric-edited and alphanumeric conversion boundaries.

## Acceptance
Add GnuCOBOL-backed fixtures with fixed locale/encoding and unit tests. Run the complete external 500-program corpus on the exact candidate SHA. Merge only if the comparable result strictly exceeds 242/500 with unchanged corpus checksum and exact stdout/return-code comparison.