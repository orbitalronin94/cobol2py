# fix: PIC numeric width and scale boundaries

## Hipótesis falsable

Los límites de escala y anchura PIC pueden dar tamaño incorrecto. Añadir pruebas de frontera para S9(n)V9(m), decimales y expresiones numéricas, corrigiendo solo pic_digit_count/fit_numeric_expression si se confirma el fallo.

## Plan experimental

- Base: `main` al crear esta rama.
- Primero añadir regresiones mínimas en `tests/test_numeric_pic_boundaries.py`.
- Ejecutar los tests focalizados y la suite existente.
- No ejecutar ni modificar `benchmarks/legacy_primary/` ni `benchmarks/edge_cases/`.
- La muestra rápida de 50 casos debe superar estrictamente el último mejor porcentaje registrado antes de solicitar el holdout completo.
- El benchmark completo solo decide ganador si supera el récord actual de 240/500 sin regresiones en tests.
- No afirmar mejora de velocidad sin medición reproducible.

## Estado

Propuesta de experimento. No contiene un resultado medido; implementar solo después de confirmar la discrepancia con un test mínimo.
