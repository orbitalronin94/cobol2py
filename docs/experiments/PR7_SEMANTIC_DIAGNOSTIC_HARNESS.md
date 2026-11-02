# PR7 — Supplementary semantic diagnostic harness

## Repository adaptation
The official comparator is in `benchmarks/run_external_corpus.py` and counts exact stdout bytes plus process return code. Keep that comparator authoritative and add semantic diagnostics as a separate report/field; never replace or inflate the official pass count.

## Deliverables
Classify each case as:
- BYTE_MATCH — exact stdout byte stream and return code match.
- SEMANTIC_MATCH — a separately defined, conservative normalization says observable output is equivalent, while raw bytes differ.
- BEHAVIORAL_MISMATCH — behavior differs or equivalence cannot be established.

Define normalization rules explicitly (e.g. line endings only if justified); never normalize numeric values, whitespace, ordering or exit codes by default. Include raw byte hashes, return codes and normalized comparison details.

## Acceptance
- Official `passed/500` remains byte-for-byte identical to the existing implementation.
- Semantic counts are supplementary and stored in separate fields/report section.
- Tests prove semantic classification cannot mutate the official pass/fail result.
- Complete checksum-verified holdout report includes both views.