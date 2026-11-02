# MOVE CORRESPONDING group semantics experiment

## Hypothesis
Group-level MOVE CORRESPONDING may mismatch elementary items by name, qualification, or group hierarchy.

## Required behavior
- Match eligible elementary items with the same data-name under source and destination groups.
- Ignore nonmatching items.
- Exclude group items and items prohibited by COBOL CORRESPONDING rules.
- Preserve destination values for unmatched items.
- Apply elementary MOVE conversion and padding to each matched pair.

## Acceptance matrix
- Same-name fields at different nesting depths.
- Duplicate names in separate subgroups.
- Numeric-to-alphanumeric and alphanumeric-to-numeric matches.
- REDEFINES and FILLER exclusions.
- Unmatched source and destination fields.

## Measurement
Add reference-backed fixtures before changing translation logic; validate the full holdout before reporting improvement.