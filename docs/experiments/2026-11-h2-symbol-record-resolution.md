# H2 — Symbol and file-record resolution

Propuesta de implementación en draft. No se afirma que la hipótesis explique todos los fallos ni que exista mejora de score.

## Evidencia

18 NameError, 10 KeyError and 2 AttributeError observations. Hypothesis: declarations, FD/SD records, qualified names and emitted references can diverge in the simplified symbol table.

## Alcance

Trace missing identifiers from data declarations and FILE SECTION through resolution. Fix shared declaration/reference handling; never add placeholder variables to silence exceptions.

## Regresiones

Minimized FILE SECTION/FD fixture, qualified nested field access and end-to-end execution. Related issue mapping remains unconfirmed.

## Gate

Suite completa y 500 casos fijos de X-COBOL v2 (skip=500) en el SHA exacto. Baseline 250/500; mínimo 251/500. Checksum, corpus, IDs y comparación exacta inmutables. Mantener sincronizados cobol2py.py y web/index.html cuando cambie el traductor. No fusionar automáticamente.
