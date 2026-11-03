# H4 — OCCURS and nested subscript resolution

Propuesta de implementación en draft. No se afirma que la hipótesis explique todos los fallos ni que exista mejora de score.

## Evidencia

2 IndexError plus table-path KeyError/TypeError observations. Hypothesis: base-1 conversion and nested table paths diverge for qualified references and arithmetic subscripts.

## Alcance

Centralize subscript parsing and path resolution; preserve field-name/index distinction and verify bounds without changing unsupported behavior silently.

## Regresiones

First/last occurrence, multidimensional arrays, nested groups, arithmetic and invalid indices. No direct issue attribution without a reproduction.

## Gate

Suite completa y 500 casos fijos de X-COBOL v2 (skip=500) en el SHA exacto. Baseline 250/500; mínimo 251/500. Checksum, corpus, IDs y comparación exacta inmutables. Mantener sincronizados cobol2py.py y web/index.html cuando cambie el traductor. No fusionar automáticamente.
