# fix: preserve literal-safe COBOL condition semantics

## Hipótesis falsable

Condiciones COBOL con literales que contienen AND/OR/NOT pueden sufrir reescrituras incorrectas. Añadir una función de tokenización segura que solo normalice operadores fuera de literales, con regresiones para comillas y operadores textuales.

## Plan experimental

- Base: `main` al crear esta rama.
- Primero añadir regresiones mínimas en `tests/test_literal_safe_conditions.py`.
- Ejecutar los tests focalizados y la suite existente.
- No ejecutar ni modificar `benchmarks/legacy_primary/` ni `benchmarks/edge_cases/`.
- La muestra rápida de 50 casos debe superar estrictamente el último mejor porcentaje registrado antes de solicitar el holdout completo.
- El benchmark completo solo decide ganador si supera el récord actual de 240/500 sin regresiones en tests.
- No afirmar mejora de velocidad sin medición reproducible.

## Estado

Propuesta de experimento. No contiene un resultado medido; implementar solo después de confirmar la discrepancia con un test mínimo.
