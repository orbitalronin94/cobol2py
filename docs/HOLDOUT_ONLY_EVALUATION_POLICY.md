# Política de evaluación externa de candidatas Python

**Fecha de actualización:** 2026-11-03  
**Estado:** vigente para el torneo de hipótesis COBOL → Python.

## Decisión

La evaluación iterativa usa exclusivamente la segunda mitad fija de X-COBOL v2: `skip=500`, `target=500`. La muestra primaria (`skip=0`, 500 casos) queda fuera de los workflows de candidatas y no se utiliza para ranking, promoción ni cálculo combinado.

La muestra se divide en cuatro shards deterministas de 125 casos (`skip=500, 625, 750, 875`). Los cuatro deben terminar correctamente y sumar exactamente 500 casos.

## Baseline y criterio de promoción

- **Baseline de main:** 250/500 (50,0 %).
- **Umbral mínimo de mejora:** 251/500 (50,2 %).
- **Fuente:** benchmark externo completo run [#538](https://github.com/orbitalronin94/cobol2py/actions/runs/41602383991), PR #284, con SHA integrado registrado en [`benchmarks/holdout-record.json`](../benchmarks/holdout-record.json).
- **Condiciones obligatorias:** checksum de X-COBOL v2 verificado, muestra completa 500/500, suite completa de tests verde y resultado asociado al SHA exacto de la PR.
- No se acepta como victoria un shard aislado, una muestra incompleta, un score de otro SHA o una suma de ejecuciones distintas.

## Métrica

Un caso pasa únicamente cuando el flujo de bytes de stdout coincide exactamente con GnuCOBOL y el código de retorno también es idéntico. No se normalizan espacios, saltos de línea, codificación ni códigos de salida. No se cambia el orden determinista, el criterio de elegibilidad, el denominador, los timeouts ni las exclusiones para elevar el porcentaje.

Los fallos de compilación de referencia y los timeouts del programa de referencia se informan por separado; no se convierten silenciosamente en aciertos o fallos del traductor.

## Terminología y límites

Aunque el repositorio conserve el nombre histórico *holdout*, esta muestra se observa repetidamente durante el desarrollo. Por tanto, es una **muestra fija de evaluación**, no un holdout estadístico intacto. No permite estimar sin sesgo la generalización a fuentes COBOL no observadas ni demuestra equivalencia de producción.

La muestra primaria de 500 no se ejecuta en el ciclo rutinario. No se publicará una puntuación combinada 1.000/1.000 como criterio vigente. El benchmark diferencial curado de 105 fixtures se conserva únicamente como herramienta manual histórica; no bloquea PRs ni participa en el ranking.

## Workflows canónicos

- `seven-candidate-tournament.yml`: descubre PRs candidatas no draft contra `main`, congela sus SHA, ejecuta suite completa y evalúa el corpus fijo.
- `external-python-benchmark.yml`: evaluación externa Python holdout-only en cuatro shards; no ejecuta primaria para ramas `experiment-v4/`.
- `differential-benchmark.yml`: manual-only para análisis histórico de las fixtures versionadas.
- `tests.yml`: mantiene unittest, compilación y smoke/differential checks de fixtures pequeñas; no ejecuta el barrido de 105 fixtures.

## Evidencia que debe adjuntar cada PR

1. SHA exacto evaluado y URL del workflow.
2. Los cuatro shards completados, con 500/500 casos medidos.
3. JSON/Markdown del informe y checksum del archivo externo verificado.
4. Aciertos/500 y delta frente a 250/500.
5. Resultado de la suite completa y regresiones enfocadas.
6. Diagnósticos de fallos sin redistribuir el dataset de terceros.

No hay merge automático. Un resultado de 251/500 es una condición necesaria, no suficiente: también se revisan regresiones, calidad de la implementación y reproducibilidad.
