# PR1 — Supported COBOL fragment contract

## Repository adaptation
The translator is the single-file `cobol2py.py` implementation. There is no `src/translator`, tree-sitter dependency, or standalone codegen package. The contract must describe the existing preprocessor, data parser, procedure parser, `Program`/`Node` model and Python emitter as they exist today.

## Deliverables
1. A compact grammar for the supported source subset, including fixed/free source format, data declarations, paragraphs, statements and expressions.
2. A semantic table for initialization, PIC storage, MOVE/arithmetic, control flow, DISPLAY and program termination.
3. A corpus classifier that reports supported / partially supported / unsupported by construct, without changing the official score.
4. A deterministic JSON report with input SHA-256, translator SHA, counts and stable reason codes.

## Files to inspect/change
- `cobol2py.py` — actual parser, model and emitter.
- `benchmarks/run_external_corpus.py` — archive selection and deterministic 500-case runner.
- `benchmarks/external-corpus/candidates.json` — corpus provenance/selection metadata.
- `tests/test_cobol2py.py`, `tests/test_external_benchmark_runner.py` — regression contracts.

## Acceptance
- Unit tests validate grammar examples and classifier reason codes.
- Two runs over the same inputs produce byte-identical JSON apart from explicitly excluded timing fields.
- Classification is supplemental; official byte-match score and 242/500 record remain unchanged.
- No tree-sitter or third-party dependency is introduced unless separately justified.