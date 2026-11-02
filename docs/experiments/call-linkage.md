# Experiment: CALL USING and LINKAGE SECTION

## Hypothesis
Subprogram calls can diverge when argument passing, BY REFERENCE/BY CONTENT/BY VALUE, linkage items, or RETURNING values are translated incompletely.

## Scope
- Static CALL to a local subprogram
- USING argument order and parameter count
- BY REFERENCE, BY CONTENT, and supported BY VALUE cases
- LINKAGE SECTION parameter declarations
- RETURNING and GOBACK/EXIT PROGRAM behavior

## Regression fixtures
Build paired main/subprogram examples that mutate a passed field, receive literals, return a value, and exercise nested calls. Compare observable output and final storage with GnuCOBOL.

## Acceptance criteria
- BY REFERENCE mutations are visible to the caller.
- BY CONTENT values do not mutate caller storage.
- Parameter mapping and return behavior are deterministic.
- Dynamic/external calls remain explicitly unsupported until separately specified.

## Risks
Python object aliasing must not accidentally make BY CONTENT behave like BY REFERENCE.