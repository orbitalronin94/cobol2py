# PERFORM VARYING control-flow experiment

## Hypothesis
PERFORM VARYING may diverge for AFTER nesting, TEST BEFORE/AFTER, and compound VARYING clauses.

## Required behavior
- Evaluate TEST BEFORE before the first iteration and TEST AFTER after the body.
- Apply FROM, BY, and UNTIL in the specified order.
- Support nested AFTER counters with their own reset/increment behavior.
- Preserve side effects in UNTIL conditions.

## Acceptance matrix
- TEST BEFORE and TEST AFTER.
- Positive and negative BY values.
- Inclusive and exclusive termination boundaries.
- VARYING ... AFTER ... nested counters.
- Inline PERFORM and paragraph PERFORM forms.

## Measurement
Use small executable GnuCOBOL differential fixtures and then the complete 500-case holdout.