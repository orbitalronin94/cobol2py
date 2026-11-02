# Indexed-file key and status semantics

## Hypothesis
Represent indexed-file operations with deterministic key lookup, duplicate-key handling, and COBOL FILE STATUS behavior.

## Scope and regressions
- OPEN modes and missing-file behavior.
- READ by primary key, START positioning, sequential READ, and EOF.
- WRITE/REWRITE/DELETE with duplicate and missing keys.
- Validate FILE STATUS after success and each error path.

## Acceptance
Use isolated temporary files and compare observable behavior with GnuCOBOL. Run the complete external 500-program corpus on the exact candidate SHA. Merge only if the comparable result strictly exceeds 242/500 with unchanged corpus checksum and exact stdout/return-code comparison.