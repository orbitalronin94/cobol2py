# Experiment: Reference modification

## Hypothesis
Substring reads and writes can differ because COBOL positions are one-based, lengths may be omitted, and assignment must preserve the unaffected parts of the receiver.

## Scope
- identifier(start:length) reads
- identifier(start:) and identifier(:length) if valid in supported dialect
- MOVE into a reference-modified receiver
- Reference modification on group/alphanumeric items
- Boundary and zero-length behavior

## Regression fixtures
Exercise first/last positions, full-width and short replacements, omitted length, numeric-looking strings, and nested expressions. Compare exact bytes/characters and DISPLAY output with GnuCOBOL.

## Acceptance criteria
- One-based COBOL positions map correctly to Python slicing.
- Writes preserve prefix/suffix and honor receiver length.
- Invalid ranges produce compiler-compatible behavior or explicit diagnostics.
- Tests include multibyte/dialect assumptions only where defined.

## Risks
Keep numeric data-item slicing separate from arithmetic subscripting and validate padding/truncation semantics.