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
