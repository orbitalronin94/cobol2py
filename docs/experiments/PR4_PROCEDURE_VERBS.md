# PR4 — Additional procedure verbs

## Repository adaptation
Extend the statement parser and emitter in `cobol2py.py`; there is no separate `codegen/` directory. Reuse the existing `Node` tree until the typed-IR migration provides a safe replacement.

## Scope
Implement or complete EVALUATE, INSPECT, STRING, UNSTRING, SEARCH and DISPLAY UPON. For each verb, define accepted syntax, operands, scope terminators, side effects, error cases and explicit unsupported forms.

## Deliverables
- Parser tests for valid and invalid forms.
- GnuCOBOL differential fixtures for each implemented semantic branch.
- Deterministic translation output and line-aware errors.
- No broad regex substitution that changes literals or comments.

## Acceptance
- Each supported form has at least one positive and one negative test.
- Nested scope terminators and continuation lines are covered.
- Unit suite passes; exact 500-case benchmark is complete and checksum verified.
- Do not claim the whole verb is supported if only a syntax subset is implemented.