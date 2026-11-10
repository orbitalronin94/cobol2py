# 30-seed failure-directed repair tournament

The 30-seed tournament is defined, but **not currently ready to run**. The branch names exist; their contents are stale and several do not implement the hypotheses assigned in the manifest.

## Main baseline record

- Historical main reference: **257/500 (51.4%)**, [run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592), SHA `393b6f5d98eb0a0f2f1af41eb5d937e6bb274d28`.
- Latest main remeasurement: **258/500 (51.6%)**, [30-seed attempt 42272058313](https://github.com/orbitalronin94/cobol2py/actions/runs/42272058313), frozen baseline SHA `3485bbd36daee6c3c2319d204bf33fddac6a32a4`.
- Both reports use X-COBOL v2, `skip=500`, `target=500`, archive MD5 `cbd974caed72b0836777dc2305928ed3`, and the same 500 case IDs.
- The one-case difference is timing-sensitive: `exec84-2-03eae98697` hit the 20-second translator timeout at 20.003376s in the earlier holdout and completed in 19.109681s in the later run. This is not evidence of a translator improvement. Keep the historical 257 reference and the latest 258 remeasurement separate.
- [Run 42266714599](https://github.com/orbitalronin94/cobol2py/actions/runs/42266714599) is an experimental branch result, not the main baseline.

## Audit of the 30-seed attempt

[Run 42272058313](https://github.com/orbitalronin94/cobol2py/actions/runs/42272058313) was cancelled. Its baseline completed 500/500 at 258/500, but only 9 candidate holdout reports were available. No candidate met the zero-regression gate; no winner was produced and nothing was promoted.

The available reports show why stale branches must not be accepted: seeds 1–8 scored 234–236/500 with 27–28 regressions each; seed 16 scored 155/500 with 113 regressions. These are not valid comparisons against current main because the candidate branches do not contain the frozen main history.

The branch histories are also mislabelled in the manifest. For example, seed 1 contains an EVALUATE-padding candidate, seed 2 EXIT PARAGRAPH, seed 3 EXIT SECTION, seed 4 INSPECT CONVERTING, seed 5 INSPECT REPLACING ALL, seed 6 IS NUMERIC, seed 9 multiple UNSTRING delimiters, and seed 10 UNSTRING POINTER—not the hypotheses currently assigned to those seeds.

## Readiness gate

Before dispatching, each of the 30 candidates must:

1. Be rebuilt from the current main SHA (the frozen main commit must be an ancestor of the candidate).
2. Change the translator implementation for its declared hypothesis.
3. Include a minimal reproducer and regression test.
4. Pass the complete unit/regression suite.
5. Run the same 500 X-COBOL v2 cases with `skip=500`, `target=500`, the pinned archive checksum and the frozen benchmark harness.
6. Compare all 500 exact case IDs; any regression rejects the candidate, and at least one new pass is required.

The workflow now checks branch ancestry and translator/test changes before running any holdout, uses the benchmark runner and Dockerfile from the frozen main SHA, and validates the corpus/options contract before ranking. It is manual-dispatch only while the candidate set is blocked.

## Promotion

No candidate qualifies. No merge, no benchmark-record update, and no automatic promotion. Once all 30 branches have been rebuilt and audited, the tournament can be dispatched. A winner still requires a separate manual review and a fresh comparison if main has moved.
