# Segundo torneo: siete hipótesis independientes de exactitud

**Base:** `main` en el commit `1624dacb57a2b70412c4438468aee98cf5ebeaff` (actualizar la base si cambia antes de ejecutar).
**Récord de referencia:** 240/500 = 48,00 %, leído de `benchmarks/holdout_best.json`.
**Procedimiento obligatorio:** primero 50 casos; solo candidatos que superen estrictamente la tasa récord pasan a la evaluación completa de 500. El gate completo decide el récord. No tocar ni ejecutar `benchmarks/legacy_primary/` ni `benchmarks/edge_cases/`.

Estas hipótesis son distintas de las siete del primer torneo (PIC, STRING, decimal, nombres/nivel 88, OCCURS, REDEFINES y longitud/cadenas). Son hipótesis de control de flujo y semántica de ejecución. No se consideran resultados hasta tener PR de código, SHA y scorecard del workflow.

## T2-H1 — Alcance de terminadores de sentencia

**Predicción:** `END-IF`, `END-EVALUATE`, `END-PERFORM` y sus formas anidadas se traducen con alcance incorrecto en ciertos casos.
**Experimento:** añadir fixtures mínimos anidados y corregir solo el reconocimiento de terminadores explícitos.
**Medida:** coincidencias exactas nuevas en esos fixtures y score de 50; falsada si no mejora o rompe sentencias ya correctas.

## T2-H2 — Semántica de `EVALUATE`

**Predicción:** selección de rama, `WHEN OTHER`, rangos y `ALSO` difieren del comportamiento COBOL.
**Experimento:** aislar el lowering de `EVALUATE` y añadir tests de límites y ramas múltiples.
**Medida:** casos diferenciales de `EVALUATE`; no modificar el parser general en la misma PR.

## T2-H3 — `PERFORM VARYING` y límites de bucle

**Predicción:** límite inclusivo, paso, variable de control o terminación generan una iteración de más/menos.
**Experimento:** corregir solo el modelo de iteración, incluyendo pasos positivos/negativos si están soportados.
**Medida:** iteraciones y salida exactas en los fixtures; rechazar cambios que alteren bucles no relacionados.

## T2-H4 — Inicialización y valores iniciales

**Predicción:** campos numéricos/alfa, grupos y valores iniciales se inicializan con tipos o espacios incorrectos.
**Experimento:** mapear únicamente cláusulas de inicialización explícitas y valores por defecto documentados.
**Medida:** estado inicial observable y salida exacta; no inferir valores no declarados.

## T2-H5 — `FILE STATUS` y ramas de E/S

**Predicción:** estado de apertura/lectura/EOF se simula con códigos incorrectos o la rama de fin de archivo no se ejecuta en el momento correcto.
**Experimento:** corregir únicamente la traducción de estado de archivo para las operaciones ya soportadas; no simular éxito en operaciones no soportadas.
**Medida:** tests de OPEN/READ/EOF/CLOSE y salida diferencial.

## T2-H6 — `MOVE CORRESPONDING`

**Predicción:** asignaciones entre grupos emparejan campos incorrectos o incluyen campos que no corresponden.
**Experimento:** construir el conjunto de campos por nombre y cualificación, respetando exclusiones semánticas conocidas.
**Medida:** valores por campo y salida exacta; falsada si no hay mejoras aisladas.

## T2-H7 — Condiciones compuestas y precedencia lógica

**Predicción:** combinaciones de `AND`, `OR`, `NOT` y paréntesis cambian precedencia o evaluación.
**Experimento:** aislar normalización/precedencia de condiciones, sin mezclar cambios aritméticos.
**Medida:** tabla de verdad para cada fixture y comparación diferencial.

## Ejecución y selección

1. Crear una rama y PR de implementación independiente por hipótesis.
2. El workflow ejecuta primero la muestra fija de 50 y calcula `floor(best_rate × 50) + 1`; si no alcanza el umbral, no se lanza el lote de 500.
3. Si supera la muestra, ejecutar el benchmark completo, checksum-verificado, con cuatro lotes de 125. Solo una mejora estricta sobre el récord actual gana.
4. Registrar para cada candidato: ID, SHA, 50-case score, si calificó, score de 500, duración, tests y fallos diferenciales.
5. Reparar fallos de PR y reejecutar los checks; no fusionar por porcentaje aislado si fallan tests de corrección.
6. Exactitud y tiempo de ejecución son métricas separadas. No atribuir aceleración sin medición comparable.
7. Nunca ejecutar ni modificar `benchmarks/legacy_primary/` o `benchmarks/edge_cases/`.

**Nota de honestidad experimental:** este documento define hipótesis, no demuestra que estén implementadas ni que hayan ganado. La muestra de 50 es un filtro rápido sobre el corpus fijo observado repetidamente, no un holdout estadístico intacto.
