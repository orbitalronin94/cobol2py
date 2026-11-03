# H5 — Group MOVE storage layout

Propuesta de implementación en draft. No se afirma que la hipótesis explique todos los fallos ni que exista mejora de score.

## Evidencia

Output mismatches and group/field access exceptions can arise when dictionaries stand in for contiguous COBOL storage. Hypothesis: group MOVE needs byte layout, padding and overlay semantics.

## Alcance

Validate the current layout model against nested groups, REDEFINES, FILLER and receiving widths; change only a reproduced storage rule.

## Regresiones

Group-to-group move, nested group, padding, overlay and byte-exact DISPLAY. Related issue #106.

## Gate

Suite completa y 500 casos fijos de X-COBOL v2 (skip=500) en el SHA exacto. Baseline 250/500; mínimo 251/500. Checksum, corpus, IDs y comparación exacta inmutables. Mantener sincronizados cobol2py.py y web/index.html cuando cambie el traductor. No fusionar automáticamente.
