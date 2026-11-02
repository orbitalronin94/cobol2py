# PR6 — Runtime errors and initialization

## Repository adaptation
Storage defaults and data declarations are currently modeled by `CobolVar` in `cobol2py.py`; runtime behavior is emitted into generated Python. Keep semantics explicit in the translator/runtime helper layer and preserve the dependency-free benchmark image.

## Deliverables
- Define initial values for alphanumeric, numeric, group and OCCURS storage.
- Implement supported COBOL MOVE conversion, size error, arithmetic error, divide-by-zero and invalid reference behavior.
- Preserve process exit status and stderr/stdout behavior where observable by the official harness.
- Distinguish a COBOL runtime error from a translator failure and a harness timeout.

## Acceptance
- Differential tests compare stdout, return code and expected error behavior against GnuCOBOL.
- Initialization tests include VALUE, spaces, low/high values, signed numeric and group items.
- No change to official matching rule or record.
- Full 500-case checksum-verified run is required before promotion.