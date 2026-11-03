# PR5 — Control-flow execution model

## Repository adaptation
The current parser builds paragraph/node structures in `cobol2py.py`; it does not contain the proposed standalone VM package. Start by modeling paragraph/section transfers, PERFORM ranges, THRU, TIMES, UNTIL, VARYING, GO TO and fall-through explicitly. Add a VM only if the existing generated control flow cannot express the required semantics safely.

## Deliverables
1. A documented control-flow graph / program-counter model for supported constructs.
2. Correct PERFORM entry, return and nested-call behavior.
3. A configurable execution budget or bounded loop strategy that prevents runaway translated programs without changing valid program output.
4. Regression cases for the 38 historically observed translated-program timeouts, where source provenance permits.

## Acceptance
- Tests cover nested PERFORM, paragraph fall-through, PERFORM THRU, loop exit and termination.
- Timeout/budget failures are explicit and distinguishable from COBOL program exit.
- No arbitrary global timeout increase used to hide hangs.
- Full holdout run and failure-category delta are attached.