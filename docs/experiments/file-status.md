# Experiment: Sequential file I/O and FILE STATUS

## Hypothesis
Programs using OPEN modes, READ/WRITE, AT END, and FILE STATUS may fail because runtime state and COBOL file semantics are not fully represented.

## Scope
- OPEN INPUT, OUTPUT, EXTEND, and I-O
- READ with AT END / NOT AT END
- WRITE and REWRITE record behavior
- CLOSE and declared FILE STATUS
- LINE SEQUENTIAL records, empty files, and missing files

## Regression fixtures
Use temporary files with deterministic contents. Compare status codes, record contents, output, and return codes with GnuCOBOL. Include EOF, missing input, duplicate keys where relevant, and invalid mode transitions.

## Acceptance criteria
- File status is updated after each applicable operation.
- AT END branches execute exactly once per EOF condition.
- Record padding/truncation follows declared record layout.
- Runtime tests clean up files and never depend on host-specific absolute paths.

## Risks
Binary/sequential organizations and indexed files have distinct semantics; keep this experiment scoped to supported sequential organizations.