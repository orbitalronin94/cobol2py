# Protocolo de evaluación final de consolidación

**Estado:** bloqueado hasta G-10. Este documento no autoriza ejecutar la muestra durante los gates intermedios.

## Propósito y autoridad

La evaluación externa es una única medición final de un candidato congelado. La ejecuta una persona autorizada después de aprobar G-01…G-09. El agente que prepara cambios, revisa CI o clasifica defectos no descarga, ejecuta, consulta ni inspecciona el corpus ni sus informes de holdout.

El nombre histórico *holdout* no significa que sea una muestra estadística intacta: el repositorio documenta que la selección fija se ha observado en iteraciones previas. El resultado solo mide equivalencia en esa selección y no demuestra compatibilidad general ni aptitud para producción.

## Inmutables

- Dataset: X-COBOL v2; no copiar el ZIP ni los fuentes extraídos al repositorio.
- Archivo: `COBOL_Files.zip`; MD5 esperado: `cbd974caed72b0836777dc2305928ed3`.
- Selección oficial: `skip=500`, `target=500`.
- Shards deterministas: `skip=500,625,750,875`, cada uno con `target=125`.
- Denominador: exactamente 500 casos elegibles ejecutados; informar aparte los errores de referencia y exclusiones.
- Acierto: stdout idéntico byte a byte y código de retorno idéntico a GnuCOBOL. No normalizar espacios, saltos de línea, codificación ni return codes.
- Baseline documentada: 250/500 (50,0 %), registrada en `benchmarks/holdout-record.json` desde el run 41602383991. Umbral mínimo: 251/500 (50,2 %). Verificar el SHA de referencia registrado allí; no confundirlo con el SHA actual de `main`.

No modificar checksum, selección, orden, elegibilidad, denominador, timeouts, exclusiones, comparador ni contenido del corpus para mejorar el resultado.

## Secuencia obligatoria

1. Aprobar G-01: CI verde del SHA exacto de `main`.
2. Aprobar G-02 y G-03: consolidación de #303/#304 sobre `main`, suite completa y comparaciones pequeñas requeridas.
3. Aprobar G-04…G-08: cada familia tiene hipótesis de causa raíz, casos reproducibles, regresiones y ADR; sin regresiones.
4. Aprobar G-09: topología de fallos, intersecciones, documentación y revisión de cambios.
5. Congelar el SHA candidato de la PR única. Registrar SHA, versión Python, versión GnuCOBOL, checksum y URLs de los checks ordinarios. No hacer más commits después de congelar.
6. Una persona autorizada inicia una única ejecución oficial de los cuatro shards. No iniciar ejecuciones exploratorias, parciales, de repetición ni de depuración.
7. La persona autorizada comprueba que los cuatro shards terminaron y suman exactamente 500 casos, revisa el informe completo y registra el resultado en `docs/holdout_result.md`.
8. Si el resultado es inferior a 251/500, incompleto o no reproducible, no se declara ready ni se fusiona. Cualquier nueva iteración requiere una nueva autorización y un protocolo de evaluación revisado; no se ajusta el código mirando esta medición.
9. Solo después de aceptar el resultado y la revisión final se puede ejecutar el commit de cierre G-10 y cerrar las PRs sustituidas.

## Registro de resultado

La persona ejecutora debe registrar en `docs/holdout_result.md`:

- SHA exacto de la PR medida y SHA de base.
- Fecha/hora UTC de inicio y fin.
- Versión de Python y GnuCOBOL.
- MD5 verificado del ZIP.
- IDs de los cuatro shards, sus skips y recuentos.
- Total probado, aciertos, porcentaje y delta frente a 250/500.
- Errores de referencia y exclusiones por separado.
- URL de la ejecución y referencias a los informes JSON/Markdown.
- Identidad de quien ejecutó y verificó la medición.

No incluir fuentes COBOL de terceros, stdout completo ni contenido del ZIP en Git.

## Protección contra ejecuciones accidentales

La rama `feat/consolidacion-main-holdout` debe quedar excluida de workflows automáticos que muestreen `skip=500`, incluidos `external-python-benchmark.yml` y `external-cobol-smoke.yml`. Las pruebas unitarias, compilación y comparaciones pequeñas de GnuCOBOL pueden ejecutarse durante los gates normales. La exclusión de workflow no debe cambiar la selección ni el comparador oficial.
