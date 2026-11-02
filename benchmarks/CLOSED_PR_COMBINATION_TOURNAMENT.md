# Closed PR combination tournament

This workflow evaluates up to seven PR deltas against the current `main` in one manually started GitHub Actions run.

For each supplied PR it freezes the current base/head SHAs, then evaluates:
- current `main` baseline;
- every PR delta individually;
- every pair of PR deltas;
- the full supplied combination in the input order.

Every candidate is integrated by applying its frozen diff to the same `main` checkout. A conflict or an empty implementation diff fails that candidate rather than silently skipping it. Unit tests run before the exact external benchmark. The external benchmark uses the pinned X-COBOL v2 archive, verifies its MD5, and evaluates the fixed second half of 500 programs using the official byte-for-byte stdout and process return-code criterion.

The workflow never changes `benchmarks/holdout_best.json`, `benchmarks/holdout-record.json`, or merges a candidate. The authoritative comparison target is `benchmarks/holdout_best.json` (242/500). The legacy `holdout-record.json` value is not used as the promotion threshold.

With seven PRs this produces 1 baseline + 7 singles + 21 pairs + 1 full combination = 30 candidates. Candidates run two at a time. The resulting artifacts contain the exact PR SHAs and integrated tree SHA so the comparison is reproducible.

A successful workflow run means the candidate was measured; it does not mean the candidate beat the record. Only a complete checksum-verified 500/500 run with a score strictly greater than 242 may be proposed for promotion.
