# Experiment: COPY and REPLACING

## Hypothesis
Some corpus failures may come from source composition: COPY books, nested COPY statements, pseudo-text delimiters, and REPLACING substitutions can alter tokens before normal parsing.

## Scope
- COPY with and without a library extension
- REPLACING identifier BY identifier
- REPLACING pseudo-text ==...== BY ==...==
- Multiple replacements and nested copybooks
- Missing copybook diagnostics and deterministic search paths

## Regression fixtures
Create minimal programs with local copybooks and assert the expanded source, source locations, and final output against GnuCOBOL. Include literals containing replacement-like text to prevent accidental substitutions.

## Acceptance criteria
- Expansion is deterministic and does not modify quoted literals or comments.
- Unsupported/missing copybooks produce explicit diagnostics, not silently incorrect Python.
- Unit tests and selected external corpus cases pass.
- Report exact case IDs and full-holdout results separately; do not infer a 500-case improvement from local fixtures.

## Risks
COPY syntax and library lookup are compiler/environment dependent. Keep search paths explicit and avoid arbitrary filesystem traversal.