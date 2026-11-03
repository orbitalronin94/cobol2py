# H3 — PIC-aware numeric conversion

Propuesta de implementación en draft. No se afirma que la hipótesis explique todos los fallos ni que exista mejora de score.

## Evidencia

18 ValueError and 15 TypeError observations plus part of the 169 output/return-code mismatches. Hypothesis: generic float/int coercions lose COBOL precision, sign, scale or receiving width.

## Alcance

Separate parsing, arithmetic and assignment to the receiving PIC; use exact decimal arithmetic only for declared numeric pictures where justified.

## Regresiones

MOVE vs COMPUTE, signed/unsigned implied decimals, overflow boundaries, ROUNDED and SIZE ERROR against GnuCOBOL. Related issues #109, #111 and #112.

## Gate

Suite completa y 500 casos fijos de X-COBOL v2 (skip=500) en el SHA exacto. Baseline 250/500; mínimo 251/500. Checksum, corpus, IDs y comparación exacta inmutables. Mantener sincronizados cobol2py.py y web/index.html cuando cambie el traductor. No fusionar automáticamente.
