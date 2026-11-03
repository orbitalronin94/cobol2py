# H7 — PERFORM and paragraph termination

Proposal-only. Evidence: 38 translated-program timeouts and 4 UnboundLocalError observations; control flow is not yet proven as the cause.

Scope: reproduce timeouts, distinguish loops from missing input/output, and model PERFORM ranges and EXIT scope explicitly.

Regressions: PERFORM UNTIL, VARYING, THRU, nested calls, EXIT PARAGRAPH/SECTION and STOP RUN. Related issues #118, #119 and #120.

No score improvement is claimed. Gate: full tests and 500 fixed X-COBOL cases (skip=500), baseline 250/500, minimum 251/500, exact SHA and unchanged comparator.