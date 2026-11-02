# REDEFINES storage overlays

## Hypothesis
Model COBOL REDEFINES as overlapping views of the same storage bytes, not independent Python fields.

## Scope
Isolate elementary/group overlays, alternate PIC interpretations, writes through either view, and nested group layouts. Do not combine with OCCURS DEPENDING ON or numeric conversion changes.

## Regression matrix
- Read the same bytes through the original and redefining item.
- Write through each view and verify the other view observes the changed bytes.
- Cover alphanumeric/numeric overlays and group-level overlays.
- Verify offsets and lengths for nested structures.

## Acceptance
Add GnuCOBOL-backed fixtures and unit tests. Run the complete external 500-program corpus on the exact candidate SHA. Improvement is accepted only when the comparable score strictly exceeds the current official record of 242/500; preserve corpus checksum and exact stdout/return-code comparison.