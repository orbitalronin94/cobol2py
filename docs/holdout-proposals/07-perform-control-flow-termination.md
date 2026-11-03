# Proposal 07 — Explicit PERFORM control flow and termination

## Evidence from holdout run #542
https://github.com/orbitalronin94/cobol2py/actions/runs/41609868400
The four shards report 43 other translator errors/timeouts and 169 runtime/output mismatches. Historical triage records translated-program timeouts (NC106A, NC251A, SQ208M) and lost output records (SUMOE). Existing control-flow analysis identifies PERFORM ranges, loop exits and paragraph fall-through as risks. These are leads for reproduction, not proof that all timeouts share one cause.

## Proposed solution
Represent procedure execution explicitly before emitting Python: paragraph/section identity, statement order, PERFORM entry/return, THRU ranges, nested PERFORM frames and fall-through. For supported loops, define TIMES, UNTIL, TEST BEFORE/AFTER and VARYING boundary semantics. Add a bounded execution guard only as a diagnostic safety net; report source paragraph and loop context and never change valid termination behavior.

## Scope
- Make paragraph dispatch and fall-through deterministic.
- Preserve nested PERFORM call/return state.
- Handle EXIT PERFORM and STOP RUN at the correct nesting level.
- Do not raise global timeouts or add arbitrary iteration caps that truncate valid programs.

## Regression plan
PERFORM paragraph/THRU; nested PERFORM; fall-through; TIMES zero/one/many; UNTIL true initially; TEST AFTER; VARYING positive/negative steps; EXIT PERFORM; multiple input records; a non-terminating fixture for the bounded diagnostic.

## Acceptance
Valid loops match GnuCOBOL output and return code; non-terminating translations are diagnosed with context, not silently truncated; existing tests pass and unchanged 500-case holdout runs on exact SHA.