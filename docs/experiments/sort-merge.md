# Experiment: SORT and MERGE

## Hypothesis
SORT/MERGE statements may be rejected or produce different record order because key comparison, duplicate handling, and input/output procedures need explicit semantics.

## Scope
- SORT table/file with ASCENDING/DESCENDING KEY
- INPUT PROCEDURE and OUTPUT PROCEDURE
- USING / GIVING file forms
- MERGE with multiple sorted inputs
- Duplicate keys and stable-order expectations where specified

## Regression fixtures
Create small records with numeric, alphanumeric, and composite keys. Compare the complete output sequence with GnuCOBOL, including duplicates, empty inputs, and descending keys.

## Acceptance criteria
- Key comparison follows COBOL data representation and collating rules supported by the translator.
- Procedure clauses run in the correct order.
- Unsupported variants are diagnosed explicitly.
- Unit and differential tests document every supported form.

## Risks
Do not implement SORT as Python's default string sort without validating numeric and collating semantics.