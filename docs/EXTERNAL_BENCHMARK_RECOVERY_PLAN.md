# External benchmark recovery plan

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
