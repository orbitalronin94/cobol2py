# External benchmark recovery plan

## Verified status — 2026-11-18

- Current main SHA: `293fc04c4dc4d825b4063e8b2b121b919de2c018`. The merge of PR #396 changed only the paired-tournament workflow and its contract test; `cobol2py.py` remains blob `4a7562627d161580470f1b0522cda0b094f635b0`.
- Latest complete X-COBOL v2 baseline artifact: [run 44297062982](https://github.com/orbitalronin94/cobol2py/actions/runs/44297062982), baseline job successful, 500/500 IDs, `skip=500`, `target=500`, MD5 `cbd974caed72b0836777dc2305928ed3`, 263/500 (52.6%), complete GnuCOBOL fingerprints. The overall run ended `failure` because discovery found no eligible candidates; its final artifact explicitly records `candidates=[]`. It is a valid baseline artifact, not a completed candidate tournament.
- The current main is code-equivalent to that baseline because the translator blob is unchanged, but a fresh baseline run on the exact current main SHA is still required before calling 263/500 an exact-SHA measurement.
- PR [#395](https://github.com/orbitalronin94/cobol2py/pull/395), pre-fix head `d42a46c827a08097c642a0a43032d48e3c50973c`, was manually compared from its four complete 125-case artifacts against the frozen baseline artifact: 500 identical IDs and source SHA values, 263/500, zero new passes, zero regressions, and eight candidate-run oracle drifts. It was not eligible for promotion. Candidate run: [44301540420](https://github.com/orbitalronin94/cobol2py/actions/runs/44301540420).
- NIST reproducers `nc225a-a777e5ee71` and `nc2254-2-73142ca32f` now compile after the earlier `WHEN NOT` syntax repair, but still failed at runtime because single-subject `EVALUATE ... NUMERIC WHEN ANY` emitted an unbound `cobol_any`. PR #395 now includes an explicit unconditional `WHEN ANY` branch plus a focused regression test at head `6553ee20b785a29794bec66526bda756ef42e2c0`. Its complete paired holdout has not yet run.
- Fresh 30-seed audit against main `293fc04`: all 30 refs exist and are distinct; all 30 are diverged; none is ahead-only. Seeds 11–15 have no translator change or regression reproducer. Seeds 16–30 contain unrelated workflow/benchmark/documentation noise and require isolated rebuilds. The 30-seed workflow remains manual-only and blocked.
- The paired PR tournament used one global concurrency group. A long baseline-only run for PR #396 held that group and the candidate run for PR #395 was cancelled before discovery. PR [#397](https://github.com/orbitalronin94/cobol2py/pull/397) is intended to scope concurrency by PR/run so independent candidate comparisons cannot cancel each other while waiting for runners.

The historical main reference remains 257/500 (51.4%) in [run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592). The 258/500 result in [run 42266714599](https://github.com/orbitalronin94/cobol2py/actions/runs/42266714599) remains experimental and is not main.

---

This PR is an incremental, test-first attempt to recover failures in the 500-program X-COBOL primary sample. It must be judged by the external differential report, not by the smaller curated regression suite.

## Baseline and acceptance criteria

- Previously recorded external baseline: 363/1,000 exact matches (36.3%) across primary and holdout.
- Goal: improve exact stdout **and** process exit-status agreement against GnuCOBOL.
- The current external workflow samples 500 primary and 500 holdout programs separately. Report both samples and their screened/excluded counts; never combine the curated 105-program suite into the external headline.
- Every behavior change must have a focused regression test before it is credited as a fix.
- A benchmark workflow success means the sample was measured successfully, not that every translated program passed.

## Failure families and experiment order

- [x] Qualified data references with a subscript attached to a non-OCCURS qualifier: add a regression and redirect the subscript to the nearest preceding OCCURS item when the qualifier itself is not an array.
- [ ] Run unit/regression suite and confirm generated Python compiles for the new qualified-reference regression.
- [ ] Reproduce multidimensional OCCURS and repeated-group failures; fix storage-path construction with focused tests.
- [ ] Reproduce generated syntax failures (reference modification, malformed subscripts, UNSTRING indexed items, concatenated identifiers); fix by syntax family, not by blanket post-processing.
- [ ] Reproduce control-flow/timeouts with bounded test execution; avoid silently translating unsupported file I/O into a non-progressing loop.
- [ ] Implement and test the supported subset of OPEN/READ/WRITE/CLOSE and EOF/status behavior, or emit an explicit unsupported diagnostic where faithful translation is not possible.
- [ ] Investigate missing file-record/overlay symbols from actual generated cases before changing storage layout.
- [ ] Expand semantic regression coverage for NUMVAL-C, level-88 conditions, REDEFINES, RENAMES, numeric PIC/sign/scale, and alphanumeric comparisons.
- [ ] Run the external 500-primary benchmark after the targeted fixes; inspect per-case outcomes and regression deltas before claiming improvement.
- [ ] Run the 500-program holdout as a separate guard against overfitting.

## Safety against false positives

- Do not convert a timeout or runtime exception into a claimed pass unless stdout and exit status both match GnuCOBOL.
- Do not add corpus source files to the repository or publish source text in reports.
- Keep `cobol2py.py` and the embedded translator in `web/index.html` synchronized.
