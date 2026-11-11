# INSPECT TALLYING FOR ALL CHARACTERS

## Holdout evidence

- Fixed X-COBOL v2 case: `cbl0701v01statementinspect-31f6d501b1`
- Source SHA-256: `31f6d501b179b358f913d8b9adf4c5d87a182f2cc11706db0cadc66fe102e2b0`
- Main baseline: [run 42844666181](https://github.com/orbitalronin94/cobol2py/actions/runs/42844666181), 261/500.
- Observed generated failure: `ws_n = int(ws_n) + (str(ws_str).count(str(characters)) if str(characters) else 0)`
- Runtime exception: `NameError: characters`.

The reproducer is the public COBOL program [CBL0701v01StatementInspect.cbl](https://github.com/mainframe-projects/CICS-Cobol/blob/master/CBL0701v01StatementInspect.cbl). It declares `WS-STR PIC X(15) VALUE 'AEDCILIDVALDV'`, then runs `INSPECT WS-STR TALLYING WS-N FOR ALL CHARACTERS` and a second tally for all `'A'` occurrences.

## Isolated hypothesis

`CHARACTERS` is a special INSPECT tally operand, not an identifier to resolve. For a fixed-width alphanumeric source, it increments the receiver by the full item length, including trailing padding spaces. The implementation is deliberately limited to this operand; ordinary `FOR ALL literal` counting remains unchanged.

## Regression

The unit reproducer uses a 15-character storage value with two trailing spaces and a non-zero initial tally. It expects the tally to increase by 15, proving both fixed-width counting and additive tally semantics.

## Evaluation status

This branch is an isolated candidate against main. It is not promoted. The full unit suite, smoke checks, and complete 500-case external holdout must finish before any casewise decision. A gain is valid only when the GnuCOBOL reference output hash and return code for that case are stable between baseline and candidate runs; oracle drift is inconclusive, not a translator gain.
