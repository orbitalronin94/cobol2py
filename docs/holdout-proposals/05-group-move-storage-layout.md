# Proposal 05 — Group MOVE as a storage operation

## Evidence from holdout run #542
https://github.com/orbitalronin94/cobol2py/actions/runs/41609868400
The holdout contains runtime/output mismatches and malformed nested group/table access. Historical triage records alphanumeric group data being converted to an integer (NC109M), while the prior accuracy analysis isolates group MOVE storage semantics as a distinct failure family. This proposal addresses layout, not generic dictionary assignment.

## Proposed solution
Define a layout descriptor for each supported group: ordered children, PIC category, width, usage and total storage length. Implement group MOVE as a storage-area operation over the serialized representation for supported DISPLAY/alphanumeric/numeric-display fields. Decode the destination using its own layout, applying truncation/padding at the group boundary. Keep binary/packed encodings out of scope until their sizes and encodings are modeled.

## Scope
- Derive group length and child offsets from declarations.
- Preserve declaration order and FILLER bytes/spaces.
- Distinguish group-to-group MOVE from elementary conversion.
- Do not introduce aliasing except for explicitly supported REDEFINES.

## Regression plan
Equal/unequal group lengths; nested groups; FILLER; trailing spaces; numeric-display children; overlapping names; MOVE followed by DISPLAY of source and destination. Compare byte-visible output against GnuCOBOL.

## Acceptance
Group MOVE preserves storage order for the supported subset; alphanumeric groups are not coerced to numbers; unsupported usages produce diagnostics rather than guessed offsets; unit suite and unchanged 500-case holdout on exact SHA.