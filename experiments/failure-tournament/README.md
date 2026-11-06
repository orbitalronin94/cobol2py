# 30-seed failure-directed repair tournament

This tournament replaces broad speculative patches with 30 isolated, falsifiable repair hypotheses.

## Frozen baseline

- Main holdout: **258/500 (51.6%)**.
- Source run: [42266714599](https://github.com/orbitalronin94/cobol2py/actions/runs/42266714599).
- Corpus: X-COBOL v2, fixed 500-case holdout (skip=500, target=500).
- Exact oracle: GnuCOBOL stdout bytes plus process return code.

## Candidate protocol

The 30 entries in `manifest.json` are distinct failure hypotheses, not 30 random reruns. Each candidate must live on its own branch, include a minimal reproducer and regression tests, and change only the translator behavior needed for its hypothesis.

For every candidate:

1. Run the full unit/regression suite.
2. Run all 500 holdout cases using the pinned corpus and unchanged benchmark settings.
3. Compare the candidate result with the frozen main result by case ID.
4. Reject it if it has **any regression** (a baseline pass becomes a candidate failure), an incomplete shard, a checksum mismatch, or a failing test suite.
5. Rank the survivors by newly passing cases. Break ties by fewer changed files and lower runtime.

The winner must score at least 259/500 and have zero regressions. A score gain without casewise zero-regression evidence is not eligible.

## Seed catalogue

The manifest assigns one specific repair hypothesis to each seed. Seeds are independent: no candidate inherits another candidate's patch. Candidate IDs and branch names are stable so results can be audited and reproduced.

## Promotion

The tournament reports a winner and evidence only. It never merges a candidate, changes the benchmark record, changes the corpus, or relaxes the zero-regression gate. The winning patch is reviewed and promoted separately.
