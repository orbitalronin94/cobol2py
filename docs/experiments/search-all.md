# SEARCH / SEARCH ALL experiment

## Hypothesis
Table search may diverge for VARYING indexes, AT END, WHEN ordering, and binary-search assumptions.

## Required behavior
- SEARCH advances the index in table order and selects the first matching WHEN.
- AT END runs only when no WHEN matches.
- SEARCH ALL respects declared ASCENDING/DESCENDING KEY ordering and binary-search constraints.
- Index values and subscripts remain COBOL-compatible.

## Acceptance matrix
- SEARCH with one and multiple WHEN clauses.
- VARYING explicit index and implicit table index.
- AT END and NOT AT END paths.
- SEARCH ALL ascending and descending keys.
- Duplicate keys, missing keys, and boundary elements.

## Measurement
Do not treat a translated linear scan as equivalent to SEARCH ALL unless the observable behavior matches the reference. Run the full holdout after implementation.