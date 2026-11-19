# Torneo de siete hipótesis para COBOL → Python

**Fecha:** 2026-11-03  
**Estado:** protocolo aprobado para candidatas aisladas; ninguna hipótesis se considera ganadora hasta completar el benchmark.

## Evidencia de partida

La referencia de main es **250/500 (50,0 %)** en la muestra fija de evaluación X-COBOL v2, obtenida en el run [#538](https://github.com/orbitalronin94/cobol2py/actions/runs/41602383991). El informe de fallos del candidato reciente analizado cubrió 500 casos:

| Estado final | Casos |
|---|---:|
| Coincidencia exacta | 250 |
| stdout o return code diferente | 169 |
| Error de sintaxis Python generado | 39 |
| Timeout del programa traducido | 38 |
| Salida de traducción supera el límite de captura | 3 |
| Timeout del traductor | 2 |

Las excepciones observadas en los fallos incluyen `ValueError` (18), `NameError` (18), `TypeError` (15), `KeyError` (10), `UnboundLocalError` (4), `ZeroDivisionError` (3), `AttributeError` (2) e `IndexError` (2). Estos recuentos son diagnósticos y pueden solaparse con la categoría de mismatch.

**Límite de atribución:** los 169 mismatches no vienen clasificados por verbo COBOL. Las hipótesis siguientes son líneas de investigación, no causas demostradas. Cada PR debe identificar y minimizar los casos que realmente respaldan su cambio antes de ampliar el comportamiento.

## Hipótesis y alcance de cada PR

### H1 — Emisión de Python sintácticamente segura

- **Señal:** 39 errores de sintaxis Python generados.
- **Hipótesis:** algunos tokens COBOL residuales, literales, expresiones o cierres de bloque alcanzan el emisor sin una representación válida en Python.
- **Trabajo:** endurecer la frontera entre parser y emisor; validar identificadores, literales, expresiones y bloques; emitir diagnóstico explícito para fragmentos no soportados en vez de producir código roto.
- **Regresión:** una fuente mínima por forma sintáctica identificada; comprobar `compile()` y comparación GnuCOBOL cuando el programa sea ejecutable.
- **No hacer:** reparaciones textuales generales sobre Python generado que puedan cambiar semántica.

### H2 — Resolución de símbolos, ámbitos y registros de archivo

- **Señal:** 18 `NameError`, 10 `KeyError`, 2 `AttributeError` y referencias a estructuras ausentes.
- **Hipótesis:** declaraciones, campos cualificados, nombres de párrafo o registros de `FILE SECTION` no siempre se conectan con las referencias emitidas.
- **Trabajo:** construir/consultar una tabla de símbolos consistente desde las declaraciones; resolver calificadores y campos subordinados; asociar FD/SD con su registro; evitar crear variables ficticias para silenciar errores.
- **Regresión:** fuente mínima con el símbolo ausente reproducido, declaración, acceso cualificado y ejecución exacta.

### H3 — Conversión numérica guiada por PIC/USAGE

- **Señal:** 18 `ValueError`, 15 `TypeError` y una parte aún no clasificada de los mismatches.
- **Hipótesis:** coerciones Python genéricas no respetan precisión, escala, signo, anchura ni reglas del receptor COBOL.
- **Trabajo:** separar parsing, operación aritmética y asignación al campo destino; usar decimal exacto donde corresponda; aplicar truncamiento/redondeo y límites solo cuando la cláusula PIC/USAGE lo permita.
- **Regresión:** positivos/negativos, decimales, overflow, MOVE frente a COMPUTE, ROUNDED y SIZE ERROR en fixtures pequeñas contra GnuCOBOL.

### H4 — OCCURS, subíndices y referencias anidadas

- **Señal:** 2 `IndexError`, accesos que pueden provocar `KeyError`/`TypeError` y mismatches por resolución de índices.
- **Hipótesis:** la conversión base 1 → base 0, el acceso a listas/diccionarios y las rutas calificadas no son uniformes en tablas anidadas.
- **Trabajo:** centralizar la traducción de subíndices y rutas; conservar la diferencia entre índice y nombre de campo; verificar límites y OCCURS anidados.
- **Regresión:** primer/último elemento, índice variable, tablas anidadas, índice inválido y referencia calificada.

### H5 — MOVE de grupos según layout de almacenamiento

- **Señal:** mismatches de salida y errores de acceso a campos que pueden aparecer cuando un grupo se representa como diccionario Python.
- **Hipótesis:** mover un grupo como objeto estructurado no reproduce la copia de la representación contigua COBOL, incluidos relleno, espacios y overlays.
- **Trabajo:** modelar layout y serialización de grupos de forma explícita, sin confundir un MOVE de grupo con asignaciones campo a campo. Mantener los límites de REDEFINES documentados si no se implementan.
- **Regresión:** grupos anidados, campos alfanuméricos con padding, longitud de grupo y comparación byte-exacta.

### H6 — Parsing y semántica de INSPECT / STRING / UNSTRING

- **Señal:** el informe agregado no etiqueta estas sentencias; existen issues específicos y su semántica de punteros/delimitadores es propensa a diferencias.
- **Hipótesis:** el tratamiento textual o parcial de operandos no conserva delimitadores, tamaños, punteros, tallying y ramas overflow.
- **Trabajo:** parsear operandos y cláusulas de forma estructural; implementar una sentencia por cambio aislado o mantener diagnóstico de no soporte.
- **Regresión:** DELIMITED BY SIZE/literal, delimitadores consecutivos, punteros, TALLYING, CONVERTING y ON OVERFLOW según la sentencia concreta.

### H7 — PERFORM, rangos de párrafos y terminación

- **Señal:** 38 timeouts de programas traducidos y 4 `UnboundLocalError`; no se ha demostrado aún qué fracción deriva de control de flujo.
- **Hipótesis:** bucles, rangos THRU, retornos y salidas de párrafo pueden producir ciclos o ejecución posterior incorrecta.
- **Trabajo:** modelar explícitamente la secuencia de párrafos, límites de PERFORM, retorno y terminación del programa; no convertir salidas no soportadas en no-op.
- **Regresión:** PERFORM TIMES/UNTIL/VARYING, THRU, llamadas anidadas, EXIT PARAGRAPH/SECTION y STOP RUN; verificar timeout y stdout contra GnuCOBOL.

## Reglas comunes de implementación

1. Una hipótesis por rama y PR, siempre con base `main`; las candidatas no se apilan unas sobre otras.
2. Antes de codificar, identificar IDs de casos del informe y obtener fuente temporal, Python generado, salida/código de retorno de referencia, salida/código de retorno candidato y traceback.
3. Reducir al menos un caso representativo a una fixture pequeña que reproduzca el fallo.
4. Mantener `cobol2py.py` y `web/index.html` sincronizados cuando cambie el traductor embebido.
5. Añadir tests enfocados y ejecutar la suite completa.
6. No cambiar el corpus, checksum, IDs, orden, selección, timeouts, exclusiones, captura ni comparación exacta.
7. No mezclar mejoras de velocidad con exactitud; el perfil de rendimiento se mide por separado.
8. No cerrar issues como resueltos hasta que el cambio correspondiente esté implementado y verificado.

## Gate de promoción

- Baseline main: **250/500**.
- Mínimo para superar: **251/500**.
- Deben completarse los cuatro shards de 125, total 500/500, checksum verificado y SHA coincidente con la cabeza de la PR.
- La suite completa debe pasar.
- Se revisan tanto nuevas coincidencias como regresiones por ID.
- El resultado negativo se conserva. No hay merge automático.

La muestra se observa repetidamente durante el desarrollo y por ello es una muestra fija de evaluación, no un holdout estadístico intacto. Una mejora en ella no demuestra compatibilidad general ni aptitud para producción.


## Revalidación del 16 de noviembre de 2026

### Estado de main

- Main actual: `41db26bacf45abcfc9bc26d0535e30a13f74842b`.
- Último holdout externo completo del código de main: **263/500 (52,6 %)**, [run 43592015588](https://github.com/orbitalronin94/cobol2py/actions/runs/43592015588), medido en `8ecabaaa7b50d01e9649814a989bbbac7491adef`.
- El commit actual `41db26b` solo modifica `README.md`; el blob de `cobol2py.py` sigue siendo `4a7562627d161580470f1b0522cda0b094f635b0`, idéntico al de la medición completa. Por tanto, 263/500 es equivalente para el código actual, pero **no** debe describirse como una ejecución lanzada sobre el SHA exacto `41db26b`.
- La referencia histórica 257/500 de [run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592) permanece separada. El 258/500 de [run 42266714599](https://github.com/orbitalronin94/cobol2py/actions/runs/42266714599) fue una rama experimental.

### PR #383 — EVALUATE NOT / ANY

El torneo emparejado [run 43743736691](https://github.com/orbitalronin94/cobol2py/actions/runs/43743736691) completó baseline y candidata con 500/500 casos y comparación por fingerprints congelados del oráculo GnuCOBOL:

| Métrica | Resultado |
|---|---:|
| Main congelado (`9e7b1279`) | 263/500 |
| PR #383 | 263/500 |
| Nuevos aprobados | 0 |
| Regresiones | 0 |
| Derivas del oráculo durante la candidata | 8 |

Los ocho IDs con deriva fueron: `cob-simpleinventory-6af451140a`, `collatz-6e335e6eda`, `date1-f31ce2734d`, `intrdate-0517c3d81c`, `pullydis-9e45af6c84`, `randombingo-e50339cc12`, `randomnumbers-d8fc7ee85b` y `rolldice-08e3de1a0e`. La puntuación se calculó contra el oráculo congelado de main; las derivas son diagnósticas. PR #383 no cumple el gate de promoción y no se fusiona.

### Cohorte de 30 semillas

La búsqueda actual encontró las 30 ramas declaradas en el manifiesto (más una rama antigua adicional de la semilla 10). La última comparación completa de divergencia y aislamiento disponible fue contra `bba24a11`: las 30 ramas estaban divergidas, ninguna era ahead-only; las semillas 11–15 no tenían cambios de traductor/tests y las 16–30 contenían ruido de workflows/benchmarks. No se ha hecho todavía una nueva comparación SHA por SHA contra `41db26b`, por lo que la readiness sigue bloqueada. El workflow de 30 semillas sigue siendo manual y no se ha despachado.

El run [43834365886](https://github.com/orbitalronin94/cobol2py/actions/runs/43834365886) es la competición de fixtures de 105 casos; no sustituye el holdout externo de 500.

### Decisión

Sin ganador, sin promoción y sin merge de código de traductor. La siguiente hipótesis prioritaria sigue siendo EVALUATE NOT/ANY, pero requiere reducirla a los dos reproduceres motivadores y demostrar al menos una ganancia exacta en el holdout congelado; la ejecución actual no ha demostrado esa ganancia.


## Revalidación del 18 de noviembre de 2026

### Baseline exacto de main

- SHA main: `a21d0131529aa7e608f762c13f8604d2e7dc54a4`.
- Resultado: **263/500 (52,6 %)**, [run 44164146830](https://github.com/orbitalronin94/cobol2py/actions/runs/44164146830).
- X-COBOL v2: MD5 `cbd974caed72b0836777dc2305928ed3`, verificado; `skip=500`, `target=500`.
- 500 IDs únicos y 500 fingerprints GnuCOBOL completos (SHA-256 stdout, longitud en bytes y código de retorno).
- El job de baseline terminó correctamente y publicó el artefacto. Falló únicamente el agregador porque `download-artifact` aplanó el único artefacto y el script buscó una subcarpeta. No se invalida la medición. La corrección de descubrimiento recursivo está en [PR #392](https://github.com/orbitalronin94/cobol2py/pull/392).

La referencia histórica de main **257/500** en [run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592) permanece separada. El **258/500** de [run 42266714599](https://github.com/orbitalronin94/cobol2py/actions/runs/42266714599) sigue siendo experimental y no es main.

### EVALUATE WHEN NOT: evidencia de la candidata anterior y reconstrucción

El informe completo de la candidata #389, [run 44076995672](https://github.com/orbitalronin94/cobol2py/actions/runs/44076995672), se recompuso desde sus cuatro shards de 125 casos y se comparó por los mismos 500 IDs contra el oráculo congelado de main del run 44164146830:

| Métrica | Resultado |
|---|---:|
| Main congelado | 263/500 |
| Candidata #389 contra el oráculo congelado | 264/500 |
| Ganancia aparente | 1 |
| Regresiones | 0 |
| IDs con deriva del oráculo durante la candidata | 8 |

El único ID adicional fue `exec84-2-03eae98697`: main no lanzó el candidato después de un timeout cercano al límite de 20 s; la candidata sí terminó y coincidió con el oráculo. No se atribuye al parche EVALUATE. Los dos reproduceres que motivaron #389 siguieron fallando al generar Python inválido:

- `nc225a-a777e5ee71`: `if _cobol_evaluate_619 not (33 + (99 - 43)):`
- `nc2254-2-73142ca32f`: `if _cobol_evaluate_614 not (33 + (99 - 43)):`

Por ello #389 se cerró sin merge y se sustituyó por [PR #391](https://github.com/orbitalronin94/cobol2py/pull/391), reconstruida directamente sobre el SHA actual. #391 amplía `WHEN NOT` a expresiones aritméticas parentizadas, usa `translate_expr` y añade tests de runtime para operandos iguales y distintos. Su suite completa pasó en [run 44292849009](https://github.com/orbitalronin94/cobol2py/actions/runs/44292849009); la comparación externa de 500 casos quedó en curso en los cuatro shards de [run 44292849042](https://github.com/orbitalronin94/cobol2py/actions/runs/44292849042). No se le atribuye ninguna ganancia hasta finalizar ese run.

### Auditoría fresca del torneo de 30 semillas

Comparación individual de las 30 ramas del manifiesto contra `a21d0131529aa7e608f762c13f8604d2e7dc54a4`:

- 30/30 refs existentes y 30/30 heads distintos.
- 30/30 ramas divergidas; 0 ahead-only.
- Semillas 11–15: sin implementación del traductor ni tests/reproducer.
- Semillas 16–30: tienen cambios de traductor/tests, pero también ruido ajeno en workflows, benchmarks, metadatos de candidatos o documentación.
- Semillas 1–10: cambios de traductor y tests aislados, pero siguen divergidas y necesitan reconstrucción sobre main.
- El workflow sigue siendo manual y readiness continúa bloqueada; no se ha despachado.

### Decisión

Sin ganador, sin promoción y sin merge de código de traductor. La siguiente hipótesis activa es corregir `WHEN NOT (aritmética)` en los dos NIST reproduceres. El siguiente gate es el holdout completo de #391, con mismos 500 IDs, source hashes, checksum y oráculo congelado, al menos una nueva coincidencia exacta atribuible al cambio y cero regresiones.


## Verificación actual — 2026-11-19

- **Main exacto:** `7b55ce1d5aadc4465549c65e04d2f15bf45b25b9`.
- **Baseline actual:** **263/500 (52,6 %)** en [run 44308154079](https://github.com/orbitalronin94/cobol2py/actions/runs/44308154079), ejecutado sobre ese SHA exacto. X-COBOL v2, `skip=500`, `target=500`, MD5 `cbd974caed72b0836777dc2305928ed3`, 500 IDs y 500 fingerprints GnuCOBOL completos.
- **Histórico separado:** 257/500 sigue siendo la referencia histórica de main en [run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592). El 258/500 de [run 42266714599](https://github.com/orbitalronin94/cobol2py/actions/runs/42266714599) sigue siendo experimental, no main.
- **PR #395:** [run candidato 44307154327](https://github.com/orbitalronin94/cobol2py/actions/runs/44307154327), cuatro shards completos de 125 casos, 500 IDs y source SHA idénticos. Contra el baseline actual obtuvo 264/500 frente a 263/500, cero regresiones y una diferencia: `exec84-2-03eae98697`. Main excedió el timeout de traducción (20,004175 s); la candidata terminó en 11,884421 s y coincidió con el oráculo en stdout vacío y return code 1. Se registra como mejora de timeout no atribuible semánticamente a EVALUATE, no como ganancia aceptada. Los dos NIST reproduceres `nc225a-a777e5ee71` y `nc2254-2-73142ca32f` seguían fallando con `NameError: it_is_81`. PR #395 se cerró como supersedida.
- **PR #398:** [PR](https://github.com/orbitalronin94/cobol2py/pull/398), head `12ac3014966d07148567f69836353097564230b9`, base exacta en main, un commit y tres archivos permitidos. Añade lowering de condition-names de nivel 88 en sujetos `EVALUATE ALSO` y un test de integración. Suite Python 3.10–3.13, GnuCOBOL reference/trace, Java y browser smoke completados con éxito en [run 44519122825](https://github.com/orbitalronin94/cobol2py/actions/runs/44519122825). El holdout de cuatro shards [run 44519122937](https://github.com/orbitalronin94/cobol2py/actions/runs/44519122937), el smoke [run 44519122846](https://github.com/orbitalronin94/cobol2py/actions/runs/44519122846) y el torneo emparejado [run 44519122785](https://github.com/orbitalronin94/cobol2py/actions/runs/44519122785) están en curso; no hay todavía ganancias ni regresiones confirmadas.
- **Auditoría de 30 semillas contra main 7b55ce1:** las 30 ramas del manifiesto existen, sus 30 heads son distintos, las 30 están divergidas y ninguna está ahead-only. Semillas 1–10: traductor y tests aislados, pero 16–212 commits detrás. Semillas 11–15: no contienen traductor ni tests. Semillas 16–30: contienen traductor/tests pero también ruido de workflow, benchmark o documentación. Hay una rama adicional antigua `10-syntax-evaluate-also` fuera del manifiesto, por lo que el prefijo devuelve 31 refs pero el manifiesto sigue conteniendo 30.
- **PR #349:** fusionó únicamente el arnés. El workflow es manual (`workflow_dispatch`), congela el baseline y rechaza ramas divergidas, duplicadas, sin tests o con cambios ajenos; la promoción no es automática. La readiness sigue correctamente en `blocked`; no se ha iniciado un torneo de 30 semillas.

**Decisión actual:** ningún candidato de traductor se ha fusionado. #398 solo podrá promocionarse si su holdout completo acredita al menos una ganancia exacta atribuible a la hipótesis y cero regresiones contra el mismo baseline congelado.


## Revalidación del 19 de noviembre — resultado emparejado de EVALUATE ALSO y nueva candidata FILE I/O

### PR #398 — no elegible

- Baseline exacto: **263/500 (52,6 %)**, main SHA `7b55ce1d5aadc4465549c65e04d2f15bf45b25b9`, [run 44308154079](https://github.com/orbitalronin94/cobol2py/actions/runs/44308154079). X-COBOL v2, MD5 `cbd974caed72b0836777dc2305928ed3`, `skip=500`, `target=500`, 500 IDs y fingerprints completos.
- El torneo oficial [run 44519122785](https://github.com/orbitalronin94/cobol2py/actions/runs/44519122785) terminó correctamente: main **263/500**, PR #398 **263/500**, 500 casos comparables, **0 nuevas aprobaciones**, **0 regresiones**, 8 derivas del oráculo. El ranking se hizo contra los fingerprints congelados de main.
- IDs con deriva: `cob-simpleinventory-6af451140a`, `collatz-6e335e6eda`, `date1-f31ce2734d`, `intrdate-0517c3d81c`, `pullydis-9e45af6c84`, `randombingo-e50339cc12`, `randomnumbers-d8fc7ee85b`, `rolldice-08e3de1a0e`.
- El holdout independiente [run 44519122937](https://github.com/orbitalronin94/cobol2py/actions/runs/44519122937) completó 500/500, pero su ganancia ocasional de `exec84-2-03eae98697` no se reprodujo en el emparejado; es un caso sensible al límite temporal y no una mejora atribuible a EVALUATE.
- Los dos reproduceres motivadores, `nc225a-a777e5ee71` y `nc2254-2-73142ca32f`, siguen terminando en timeout del programa traducido. Suite [44519122825](https://github.com/orbitalronin94/cobol2py/actions/runs/44519122825) y smoke [44519122846](https://github.com/orbitalronin94/cobol2py/actions/runs/44519122846) verdes, pero sin ganancia exacta. PR #398 se cerró sin merge.

### PR #371 — reconstruida sobre main para FILE I/O SEQUENTIAL

- PR: [#371](https://github.com/orbitalronin94/cobol2py/pull/371).
- Base: `7b55ce1d5aadc4465549c65e04d2f15bf45b25b9`; head reconstruido: `6e5ec12077ac5c4d9d2ea0ca24a44147bc42ebd9`.
- Hipótesis: `ORGANIZATION SEQUENTIAL` debe leer registros de ancho fijo según el ancho declarado, no usar `readline()` cuando el archivo no contiene separadores de línea. `LINE SEQUENTIAL` conserva lectura por línea.
- Caso motivador del holdout: `openfilesequential-962ba09d3d`. Main produce 83 bytes frente a 46 bytes de GnuCOBOL; el candidato cambia la lectura al ancho del FD. Se añade fixture ejecutable con dos registros de cuatro bytes sin newline y comprobación del estado EOF.
- Cambios aislados en `cobol2py.py`, `web/index.html` y `tests/test_cobol2py.py`; no se modificó corpus, métrica ni workflow.
- Suite [44523489717](https://github.com/orbitalronin94/cobol2py/actions/runs/44523489717), smoke [44523489851](https://github.com/orbitalronin94/cobol2py/actions/runs/44523489851), holdout [44523489575](https://github.com/orbitalronin94/cobol2py/actions/runs/44523489575) y torneo emparejado [44523489648](https://github.com/orbitalronin94/cobol2py/actions/runs/44523489648) están en curso. No hay puntuación, ganancias ni regresiones elegibles todavía.

### Readiness de las 30 semillas

El manifiesto sigue en `blocked`: 30 ramas existentes y distintas, todas divergidas; semillas 11–15 sin traductor/tests y 16–30 con ruido ajeno de workflows/benchmark/documentación. El workflow de 30 semillas sigue siendo manual (`workflow_dispatch`) y no se ha iniciado. El torneo antiguo de 16 candidatos sigue manual-only y sin cohorte válida; no se ha duplicado.

**Decisión:** ningún parche de traductor promovido ni fusionado. El siguiente gate es el holdout emparejado completo de #371 con los mismos 500 IDs y fingerprints congelados de main, al menos una nueva coincidencia atribuible a FILE I/O SEQUENTIAL y cero regresiones.
