# fix: STRING overflow pointer and destination safety

## Hipótesis falsable

STRING con POINTER y ON OVERFLOW puede alterar destino o puntero en el borde. Añadir pruebas de overflow exacto y un carácter por encima; corregir solo split_concat_statements/translate_statement.

## Plan experimental

- Base: `main` al crear esta rama.
- Primero añadir regresiones mínimas en `tests/test_string_overflow_boundaries.py`.
- Ejecutar los tests focalizados y la suite existente.
- No ejecutar ni modificar `benchmarks/legacy_primary/` ni `benchmarks/edge_cases/`.
- La muestra rápida de 50 casos debe superar estrictamente el último mejor porcentaje registrado antes de solicitar el holdout completo.
- El benchmark completo solo decide ganador si supera el récord actual de 240/500 sin regresiones en tests.
- No afirmar mejora de velocidad sin medición reproducible.

## Estado

Propuesta de experimento. No contiene un resultado medido; implementar solo después de confirmar la discrepancia con un test mínimo.
