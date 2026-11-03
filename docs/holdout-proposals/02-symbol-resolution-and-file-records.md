# Proposal 02 — Canonical symbol resolution and file records

## Evidence from holdout run #542
https://github.com/orbitalronin94/cobol2py/actions/runs/41609868400
The four shards recorded 18 NameError and 10 KeyError exceptions. The historical failure ledger also records a qualified-field KeyError (NC208A) and missing record-name failures. These are diagnostic leads, not proof that every current exception has one root cause.

## Proposed solution
Build one canonical symbol table from the parsed data hierarchy and file declarations. Each symbol retains its COBOL name, normalized Python name, level, parent/group path, declaration kind and source location. Resolve references using the full OF/IN qualification chain before emission. Create FD/SD record bindings only from actual declarations and map file-name-to-record-name explicitly. Never hide unresolved references by injecting arbitrary globals or empty dictionaries.

## Scope
- Use the same canonical-name function for declarations and references.
- Resolve duplicate child names only when qualification disambiguates them.
- Validate file-control/FD associations and record availability.
- Emit deterministic unresolved/ambiguous-symbol diagnostics with source context.

## Regression plan
Duplicate names in sibling groups; two- and three-level OF/IN qualification; mixed case and hyphenated names; FD record names; file-name/record-name differences; genuinely unresolved identifiers; and runtime read/write of declared records.

## Acceptance
Valid qualified references resolve to declared storage; no fabricated symbols are introduced; unresolved names fail deterministically; existing tests and the unchanged 500-case holdout pass on the exact candidate SHA.