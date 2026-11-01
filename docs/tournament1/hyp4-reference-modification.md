# fix: reference modification bounds

## Hipótesis falsable

La modificación de referencia puede tener límites/índices COBOL incorrectos. Probar índices base 1, longitud omitida y límites; corregir emit_reference_modification_move sin cambiar otras rutas.

## Plan experimental

- Base: `main` al crear esta rama.
- Primero añadir regresiones mínimas en `tests/test_reference_modification_bounds.py`.
- Ejecutar los tests focalizados y la suite existente.
- No ejecutar ni modificar `benchmarks/legacy_primary/` ni `benchmarks/edge_cases/`.
- La muestra rápida de 50 casos debe superar estrictamente el último mejor porcentaje registrado antes de solicitar el holdout completo.
- El benchmark completo solo decide ganador si supera el récord actual de 240/500 sin regresiones en tests.
- No afirmar mejora de velocidad sin medición reproducible.

## Estado

Propuesta de experimento. No contiene un resultado medido; implementar solo después de confirmar la discrepancia con un test mínimo.
