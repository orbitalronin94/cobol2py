# OCCURS DEPENDING ON active table bounds

## Hypothesis
Distinguish declared maximum storage from the runtime active occurrence count controlled by DEPENDING ON.

## Scope
Cover minimum/maximum occurrence counts, changing the controller at runtime, nested variable tables, and bounds-sensitive references. Keep ordinary fixed OCCURS behavior unchanged.

## Regression matrix
- Initialize and iterate tables at minimum, intermediate, and maximum counts.
- Change the depending item after initialization and before iteration.
- Test subscripts at active-count and declared-capacity boundaries.
- Cover nested OCCURS DEPENDING ON layouts.

## Acceptance
Add GnuCOBOL-backed fixtures and unit tests. Run the complete external 500-program corpus on the exact candidate SHA. Improvement is accepted only when the comparable score strictly exceeds 242/500 with the same checksum and exact stdout/return-code comparison.