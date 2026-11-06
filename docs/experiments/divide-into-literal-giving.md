# DIVIDE INTO GIVING with a numeric-literal dividend

## Evidence

The paired X-COBOL v2 main-baseline report from workflow run #316 contains repeated generated-Python syntax failures in NIST COBOL-85 programs:

- Primary: `nc117a-915f228a0e`, `nc117a-981f3e0212`, `nc1724-2-1e5e6dc890`, `nc203a-d0c691e671`.
- Holdout: `nc203a-dc7f80e633`, `nc172a-3a5109e496`, `nc1174-2-1ca986faf4`.

The source statements include `DIVIDE DIV2 INTO 864.36 GIVING DIV8` (NC117A/NC172A) and `DIVIDE 25COUNT INTO 100 GIVING 25ANS REMAINDER 25REM` (NC203A).

## Root cause

The `DIVIDE ... INTO ... GIVING` recognizer required the INTO operand (the dividend) to match `DATA_REF_PATTERN`. A numeric literal such as `864.36` or `100` therefore failed the GIVING recognizer and fell through to the multiple-receiver path. That path treated the literal as an assignment target, emitting invalid Python such as `864.36 = ...` or `100 = ...`.

## Change

Allow a signed integer/decimal numeric literal as the dividend operand while keeping the GIVING and optional REMAINDER receivers constrained to COBOL data references. The existing `translate_literal` and assignment emitters remain responsible for conversion and PIC sizing.

## Regression coverage

- Decimal literal dividend with INTO/GIVING.
- Integer literal dividend with INTO/GIVING/REMAINDER.
- Existing variable-dividend, multiple-receiver, and remainder tests remain unchanged.

## Scope

This change does not add new rounding, SIZE ERROR, or arithmetic-expression grammar. It only accepts numeric literal operands already supported by `translate_literal`. Corpus, sample selection, exact stdout/return-code metric, and benchmark settings are unchanged.
