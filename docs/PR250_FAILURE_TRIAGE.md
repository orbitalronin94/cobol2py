# PR #250 — fast-screen failure triage and repair ledger

Baseline unchanged: 240/500 (48.0%). The fast-screen artifact at head 0ffff629662c53c0fa78a5e1703b381278e1051a had 27 candidate failures and 806 excluded cases whose GnuCOBOL reference failed or timed out. These are not 27 proven translator defects. Keep missing reference dependencies and missing input files separate from implementation bugs. Never change corpus membership, score criteria, or expected output to force a pass.

| # | Case | Observed failure class | Action / status |
|---:|---|---|---|
| 1 | asdf-create-group.cob | Reference rc 1; external module asdf-generate-uuid unavailable | Fixture/dependency; not a translator patch until the reference can run. |
| 2 | BIRDSPOT.cbl | Reference runs; stdout mismatch | Inspect exact output diff and file status/open path before patching. |
| 3 | c03ex02.cob | Reference runs; stdout mismatch | Reproduce input and trace ACCEPT/initialization/COMPUTE values. |
| 4 | caller_program.cob | Reference rc 1; called module unavailable | Fixture/dependency; do not invent a stub. |
| 5 | CBL0207v01DivideVerb.cbl | Reference runs; arithmetic stdout mismatch | Reproduce division result/PIC and implement only demonstrated COBOL truncation semantics. |
| 6 | CBL0208v01ComputeVerb.cbl | Reference runs; COMPUTE stdout mismatch | Diff expressions and receiving PIC; add focused arithmetic tests. |
| 7 | cisp.cbl | Reference rc 1; LOGGER dependency unavailable | Fixture/dependency; no fake logger implementation. |
| 8 | DB1014.2.cbl | Translator rc 0 but candidate rc absent | Recover runner logs and classify launch/timeout/exception first. |
| 9 | DB102A.CBL | Translator rc 0 but candidate rc absent | Recover runner logs and classify launch/timeout/exception first. |
| 10 | dectrans.cbl | Reference rc 16, candidate rc 1; dynamic year differs | Separate date/time semantics from UNSTRING; use controlled clock only if harness supports it. |
| 11 | IF126A.CBL | Generated call passes two args to one-arg _cobol_numval_c | Patched in this PR: optional currency argument is accepted and stripped; regression tests added. |
| 12 | MILLARD.cbl | Reference and candidate rc 0; stdout mismatch | Compare first differing byte/field before choosing a formatting fix. |
| 13 | NC105A.CBL | Candidate rc absent | Recover translator/runner logs before editing semantics. |
| 14 | NC106A.CBL | Candidate timeout, rc -9 | Trace generated loop/control flow; do not merely raise timeout. |
| 15 | NC109M.CBL | Runtime ValueError converting alphanumeric group data to int | Trace MOVE/group storage and PIC conversion; preserve alphanumeric bytes. |
| 16 | NC208A.CBL | Runtime KeyError for qualified field | Trace qualification/name resolution and nested storage; add a minimized regression. |
| 17 | NC2154.2.cbl | Runtime str/int comparison error | Use PIC-aware COBOL comparison semantics; test alphanumeric and numeric cases separately. |
| 18 | NC235A.CBL | Runtime TypeError: string index used on list | Trace OCCURS/index lowering; preserve numeric subscript semantics. |
| 19 | NC251A.CBL | Candidate timeout, rc -9 | Trace loop progress and exit conditions. |
| 20 | sale-control-sample.cob | Reference rc 1; required RubrosFile data missing | Fixture/path issue; run from expected working directory with fixture present. |
| 21 | SQ208M.CBL | Candidate timeout, rc -9 | Trace control flow and loop progress. |
| 22 | SQ218A.CBL | Candidate rc 1 | Obtain full traceback and minimize before patching. |
| 23 | ST109A.CBL | Candidate rc 1 | Obtain full traceback and minimize before patching. |
| 24 | SUMOE.cbl | Candidate emits fewer output records than reference | Trace loop termination and input consumption with multi-record test. |
| 25 | table.cob | Candidate stdout empty; reference emits records | Trace paragraph dispatch, table initialization and lookup hit/miss. |
| 26 | tictactoe.cbl | Candidate rc 1 under DEVNULL stdin | Reproduce EOF behavior; do not invent input moves to fake equivalence. |
| 27 | ZUTZCPC.CBL | Reference says UTSTCFG/SRCPRG missing; translator timed out | Fixture/dependency first; distinguish translator timeout from invalid reference setup. |

## Validation and execution policy

- The exact evaluated SHA must be recorded with every scorecard.
- The full fixed evaluation uses the 500-case second half (skip=500, target=500), split into four 125-case shards; no corpus or score-rule changes.
- RUN_FULL_HOLDOUT: true opts this PR into that full evaluation. The 50-case screen is not the release result.
- The one code fix in this revision is the demonstrated NUMVAL-C arity defect (#11). Other implementation cases remain open until their diagnostics are reproduced; environment/dependency cases must not be counted as translator fixes.
- Do not merge unless tests pass and a complete, SHA-matched report supports the decision.