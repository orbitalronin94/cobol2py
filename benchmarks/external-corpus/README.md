# External COBOL candidate ledger

`candidates.json` is a machine-readable companion to the preliminary source audit in
`docs/external-corpus-audit.md`. It currently contains six externally hosted
candidate units. It is **not** the final 100-program corpus.

Each entry records the upstream repository, immutable source commit, source path,
blob SHA, line count, declared license and audit status. Sources are not copied
into this repository. Entries are explicitly marked `NOT_RUN` until compilation
and runtime comparisons have actually happened.

Validate the metadata from the repository root:

```bash
python tools/validate_external_corpus_manifest.py
python -m unittest tests.test_external_corpus_manifest -v
```

The validator checks required provenance fields, pinned 40-character commit and
blob hashes, source URL pinning, positive line counts, duplicate identities and
recognized status labels. Passing validation only means the ledger is structurally
consistent; it does not verify upstream reachability, licensing beyond the recorded
review, GnuCOBOL compilation or behavioral equivalence.

Next steps remain: inspect dependencies/copybooks, build a pinned compiler
environment, create deterministic inputs where possible, and report compilation,
runtime, differential and blocked statuses separately. Do not treat a blocked
platform dependency as a translator failure.
