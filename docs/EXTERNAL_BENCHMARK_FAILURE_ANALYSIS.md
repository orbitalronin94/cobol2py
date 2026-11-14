# Informe de fallos del benchmark externo y plan de mejora concentrada

**Fecha:** 2026-10-29  
**Proyecto:** `cobol2py`  
**Propósito:** priorizar cambios con mayor potencial de recuperar casos en el corpus externo, sin alterar el corpus ni la métrica.

> **Nota de vigencia (2026-10-29):** las tablas de los apartados 1–3 describen la ejecución histórica #511 (SHA `2307c7b`) y no deben interpretarse como el estado actual. El apartado **7. Estado actual y trabajo en curso** contiene la medición posterior y prevalece para decisiones nuevas.

## 1. Resumen ejecutivo

La última evaluación completa analizada del candidato de trabajo obtuvo:

| Muestra | Aciertos | Exactitud |
|---|---:|---:|
| Primaria | 178/500 | 35,6 % |
| Holdout | 197/500 | 39,4 % |
| Total combinado | 375/1000 | 37,5 % |

- Ejecución de referencia: [external-cobol-corpus #511](https://github.com/orbitalronin94/cobol2py/actions/runs/40839194532).
- SHA evaluado: `2307c7beed973cefd7ffe8d17b2a9f6af7154083`.
- Una segunda ejecución en el mismo SHA dio 198/500 en holdout (39,6 %) y 376/1000 combinado por un único caso variable (`rock-paper-scissors`). Por ello, **39,4 % en holdout y 37,5 % combinado son las cifras conservadoras de referencia** hasta eliminar la fuente de no determinismo.
- Estas cifras describen el SHA evaluado en la rama de trabajo, no deben atribuirse automáticamente al estado de `main`.

La oportunidad de mejora más grande no está en un único error sintáctico: está en los desacuerdos de ejecución entre el programa COBOL de referencia y el Python generado. El orden recomendado es: (1) referencias/datos y símbolos; (2) semántica de ejecución y tipos COBOL; (3) sintaxis generada; (4) control de flujo y tiempos de espera. Cada cambio debe tener una regresión pequeña y medirse en ambas muestras.

## 2. Distribución de fallos observada

Sobre los 1.000 casos de los informes de primaria y holdout:

| Resultado del candidato | Casos | % del corpus |
|---|---:|---:|
| Diferencia de stdout o código de salida | 490 | 49,0 % |
| Error de sintaxis Python generado | 74 | 7,4 % |
| Tiempo de espera del programa traducido | 56 | 5,6 % |
| Tiempo de espera del traductor | 3 | 0,3 % |
| Excepción de regex en el traductor | 2 | 0,2 % |
| **Fallos totales** | **625** | **62,5 %** |
| **Aciertos exactos** | **375** | **37,5 %** |

Las categorías anteriores describen el estado final del caso y suman 1.000. Las excepciones Python observadas durante los fallos se solapan con esas categorías; no deben sumarse de nuevo al total.

### Excepciones recurrentes observadas

| Excepción | Ocurrencias |
|---|---:|
| `NameError` | 116 |
| `TypeError` | 47 |
| `ValueError` | 37 |
| `KeyError` | 20 |
| `UnboundLocalError` | 5 |
| `IndexError` | 3 |
| `AttributeError` | 3 |
| `RecursionError` | 1 |
| `ZeroDivisionError` | 1 |

Los recuentos son diagnósticos de los casos fallidos y pueden solaparse con las diferencias de salida/código de retorno.

### Nombres ausentes más repetidos

| Nombre | Ocurrencias |
|---|---:|
| `file_cobol_record_information_rec` | 39 |
| `cobol_is` | 12 |
| `rdf3_5_16` | 3 |
| `debug_contents` | 3 |
| `cobol_new_string` | 3 |
| `idx_5` | 3 |
| `tbl_elemen_` | 3 |
| `ws_file_status` | 2 |
| `loop_count` | 2 |
| `tbl_2_r` | 2 |

Los nombres ausentes son una pista para rastrear el origen: declaración no analizada, referencia cualificada que no se normalizó, registro de archivo no creado, campo o subíndice mal traducido, o token COBOL residual. No se recomienda añadir variables globales ficticias para silenciar los `NameError`: hay que reparar el análisis y la generación del dato correspondiente.

## 3. Diagnóstico por prioridad

### P0 — Referencias, declaraciones y estructuras de datos

**Por qué va primero:** `NameError` es la excepción más repetida; un único fallo en la declaración o resolución de nombres puede afectar a múltiples sentencias de un programa.

Pistas concretas:
- `file_cobol_record_information_rec` aparece 39 veces y apunta a declaraciones de registros/archivos, especialmente el recorrido de `FILE SECTION`, `FD`/`SD` y la asociación entre nombre de archivo y registro.
- `cobol_is` aparece 12 veces y sugiere que `IS` sobrevivió a la traducción como si fuera un identificador Python, probablemente en una condición o cláusula COBOL que no se normalizó.
- `KeyError` (20) y `IndexError` (3) invitan a revisar inicialización y acceso a tablas/registros, no solo la existencia de nombres.
- También se observan referencias con cualificación profunda y subíndices de tabla.

**Trabajo propuesto:**
1. Para cada caso representativo, guardar fuente COBOL, Python generado, stdout/código de retorno de referencia, resultado candidato y traceback.
2. Seguir el símbolo desde el análisis de declaraciones hasta la resolución de referencias y el código emitido.
3. Corregir la regla compartida que origina la familia, no el ejemplo concreto.
4. Añadir pruebas de traducción y de ejecución; si el traductor web incluye una copia embebida, mantenerla sincronizada.
5. Volver a ejecutar los casos afectados antes del benchmark completo.

**Criterio de aceptación:** desaparece el error sin introducir regresiones en los casos ya correctos, y las referencias a archivos/registros/tablas conservan su estructura y semántica.

### P1 — Semántica COBOL/Python y diferencias de salida

**Por qué:** 490 casos (49,0 % del corpus) terminan en diferencias de salida o código de retorno; es la mayor categoría. La solución no es normalizar la salida para que parezca correcta, sino reproducir la semántica COBOL.

Áreas a inspeccionar:
- `PIC X`, campos numéricos y numéricos editados, espacios de relleno y truncamiento.
- `MOVE` entre campos elementales y grupos, incluyendo representación de bytes.
- Conversión entre cadenas y números, signos, decimales, redondeo y división.
- `STRING`/`UNSTRING`, delimitadores, operandos múltiples y campos receptores.
- Valores iniciales, cláusulas `VALUE`, nivel 88 y registros de archivo.
- Código de retorno y condiciones de fin de archivo.

**Método:** agrupar diffs por patrón semántico (salida vacía inesperada, padding, formato numérico, valor calculado, retorno incorrecto), elegir el patrón con más casos y escribir una prueba diferencial mínima antes de cambiar el traductor.

### P2 — Sintaxis Python generada

**Por qué:** 74 casos (7,4 %) fallan porque el Python emitido no se puede ejecutar. Estos casos suelen ser recuperables si la corrección es general.

Pistas del reporte:
- Se repiten condiciones con llamadas a `.ljust(20)` y expresiones de tabla.
- Aparecen diccionarios generados con nombres COBOL residuales como `cobol_is`.
- Se observan problemas de paréntesis, tokenización, expresiones anidadas y referencias a tablas.

**Trabajo propuesto:**
1. Compilar con `compile(generated_python, filename, "exec")` inmediatamente después de traducir, en las pruebas y en el diagnóstico del benchmark.
2. Guardar la primera línea inválida y su fuente COBOL.
3. Clasificar por regla del traductor: condiciones, literales, llamadas intrínsecas, subíndices, indentación o sentencias multilínea.
4. Evitar arreglos de texto globales que puedan reescribir código Python ya generado; proteger límites entre tokens COBOL y Python.

**Criterio de aceptación:** cada caso sintáctico corregido tiene fixture y la suite completa continúa pasando.

### P3 — Bucles, control de flujo y timeouts

**Por qué:** 56 programas traducidos se agotan por tiempo (5,6 %) y otros 3 casos agotan el tiempo del traductor (0,3 %).

Revisar:
- `PERFORM` (incluidos `TEST AFTER`, rangos `THRU` y transferencias `GO TO`).
- Contadores, límites de iteración, `EXIT PERFORM`, índices de tablas y condiciones abreviadas.
- Condiciones de terminación alteradas por coerciones o valores iniciales.
- Recursión o expansión de regex no acotada en el propio traductor.

**Criterio de aceptación:** reproducir el caso con un timeout acotado, localizar el bucle/recorrido que no progresa y añadir una prueba que valide tanto la terminación como la salida final.

## 4. Orden de trabajo para la siguiente iteración

1. **Congelar una referencia:** SHA exacto, puntuación primaria/holdout/combinada y lista de casos correctos/fallidos. Repetir una vez los casos sospechosos de no determinismo.
2. **Atacar la familia de símbolos/datos:** comenzar por `file_cobol_record_information_rec` y `cobol_is`; comprobar si las 51 apariciones corresponden a pocas reglas compartidas o a causas distintas.
3. **Atacar diferencias semánticas agrupadas:** empezar por la familia que más casos comparte el mismo patrón de diff, no por casos aislados.
4. **Eliminar errores sintácticos de forma sistemática:** compilar todo el código generado y convertir cada fallo reproducible en fixture.
5. **Resolver los timeouts con casos mínimos:** distinguir timeout del traductor frente a timeout del programa traducido.
6. **Validación completa:** pruebas unitarias, regresiones, primaria (500), holdout (500) y comparación caso por caso.
7. **Registrar resultados:** anotar SHA, aciertos de cada muestra, total combinado, casos recuperados, regresiones y tiempo de ejecución.

## 5. Reglas para mantener el benchmark honesto

- No cambiar el corpus, los criterios de comparación ni el tratamiento de stdout/código de retorno para aumentar la puntuación.
- No optimizar solo la muestra primaria: el holdout es una salvaguarda contra el sobreajuste.
- No atribuir a una revisión un resultado medido en otro SHA.
- No presentar una mejora como estable si cambia al repetir la misma revisión; investigar primero la fuente de no determinismo.
- Mantener fixtures para todo fallo corregido y comprobar que no se pierden casos ya aprobados.
- Separar las métricas de exactitud de los diagnósticos de excepciones, ya que estos últimos pueden solaparse.

## 6. Objetivo de iteración

Objetivo de planificación: buscar una mejora de **+5 puntos porcentuales combinados** en una iteración concentrada; +10 puntos sería un objetivo aspiracional, no una promesa. Solo se declarará alcanzado cuando primaria y holdout terminen en el mismo SHA, se revise el delta de regresiones y la ejecución sea reproducible.

La prioridad inmediata es corregir una causa compartida que recupere varios casos y que pueda validarse con una prueba pequeña. La métrica final debe mejorar por equivalencia real, no por tolerar diferencias.


## 7. Estado actual y trabajo en curso (2026-10-29)

### Medición externa comparable más reciente

La referencia conservadora continúa siendo [#511](https://github.com/orbitalronin94/cobol2py/actions/runs/40839194532), SHA `2307c7b`: 178/500 en primaria, 197/500 en holdout y **375/1000 = 37,5 %**.

El benchmark externo Python #14 [primaria](https://github.com/orbitalronin94/cobol2py/actions/runs/40925611062) se completó en SHA `9d81975` con 168/500 (33,6 %); el holdout asociado dio 194/500 (38,8 %). Total combinado: **362/1000 = 36,2 %**, 13 programas por debajo del récord conservador. La marca aspiracional de la iteración sigue siendo 425/1000 (42,5 %), pero solo se declarará alcanzada con ambos bloques completos en el mismo SHA.

| Revisión | Primaria | Holdout | Total |
|---|---:|---:|---:|
| Referencia #511, SHA `2307c7b` | 178/500 (35,6 %) | 197/500 (39,4 %) | 375/1000 (37,5 %) |
| Python #7, SHA `13d359c` | 165/500 (33,0 %) | 191/500 (38,2 %) | 356/1000 (35,6 %) |
| Python #12, SHA `8e5e2ec` | 168/500 (33,6 %) | 193/500 (38,6 %) | 361/1000 (36,1 %) |
| Python #14, SHA `9d81975` | 168/500 (33,6 %) | 194/500 (38,8 %) | 362/1000 (36,2 %) |

### Regresiones entre la referencia y el último candidato

La comparación por ID entre los mismos bloques de 500 encontró **8 casos nuevos aprobados y 21 regresiones**, un delta neto de -13 programas (375 → 362). En primaria: 4 ganancias y 14 regresiones; en holdout: 4 ganancias y 7 regresiones.

| Categoría de fallo | Referencia #511 | Python #14 | Delta |
|---|---:|---:|---:|
| Salida o código de retorno diferente | 490 | 472 | -18 |
| Programa traducido agotó el tiempo | 56 | 80 | +24 |
| Error de sintaxis Python | 74 | 75 | +1 |
| Timeout del traductor | 3 | 3 | 0 |
| Límite de captura de salida | 0 | 6 | +6 |
| Aciertos exactos | 375 | 362 | -13 |

La categoría de diferencias de salida se redujo, pero aumentaron los timeouts y los límites de captura. Es una correlación entre ejecuciones; todavía no demuestra que una única modificación sea la causa. Evitar más cambios generales hasta reproducir al menos una familia concreta.

### Casos de regresión a reproducir primero

- **Terminación / salida excesiva:** `fp201612-3-ae4424744f`, `p20161b-4871fdaff9`, `smp002-508ab1c516`, `conta-corrente-55f5a45a05`, `progr02t-ebdd706b74`, `colors-3cb74b9dc4`, `smp001-ccd7110609`, `bds1003-12491860f2`, `gpa-calculator-bcfb8405ce`.
- **Índices multidimensionales:** `nc241a-681f02a7ce`, `nc2344-2-5f8e49c5ac` y `nc2414-2-2f38ed7c87` fallan con `TypeError: list indices must be integers or slices, not str`.
- **Token/nombre ausente:** `clie-ea6fe390da` y `clic-f5b1f6c97a` generan `NameError` para `at`. Hay que inspeccionar el contexto original antes de decidir si comparten causa.

### Prioridades revisadas

1. Reproducir una regresión de timeout con una fuente COBOL mínima y comprobar la condición de avance del bucle; no aumentar límites ni ignorar la salida excesiva.
2. Rastrear la construcción y la resolución de tablas multidimensionales, con fixtures para cada dimensión e índice.
3. Revisar el símbolo `file_cobol_record_information_rec`, presente en 41 resultados de fallo del informe actual (23 primaria, 18 holdout), frente a 41 en la referencia. No introducir globals ficticios para ocultar `NameError`.
4. Clasificar diferencias de salida por patrón semántico y corregir una causa raíz por iteración.
5. Mantener C/Rust como métricas separadas y usar los rechazos para priorizar cobertura, no para sustituir el benchmark externo Python.

El procedimiento de aceptación, las puertas de cierre y el registro de iteraciones están en [`docs/EXTERNAL_BENCHMARK_ITERATION_ROADMAP.md`](EXTERNAL_BENCHMARK_ITERATION_ROADMAP.md).


## Reevaluación experimental: ejecución multilenguaje #621 (commit `e0863d1`)

Se completaron las muestras primaria y holdout de 500 programas cada una para el mismo SHA que sincroniza el traductor de navegador. El criterio sigue siendo stdout exacto + código de retorno exacto.

| Muestra | Python | C | Rust |
|---|---:|---:|---:|
| Primaria (500) | 168/500 (33,6 %) | 20/500 (4,0 %) | 19/500 (3,8 %) |
| Holdout (500) | 194/500 (38,8 %) | 22/500 (4,4 %) | 21/500 (4,2 %) |
| Total Python | **362/1.000 (36,2 %)** | — | — |

La comparación por ID de caso contra los artefactos anteriores de las mismas muestras encontró **cero casos ganados y cero casos perdidos** en primaria y holdout. La corrección de referencias cualificadas anidadas de la PR #40 no cambia el resultado externo; no debe contabilizarse como subida del porcentaje. El benchmark dedicado `external-python-benchmark` sigue siendo la ejecución de scorecard oficial pendiente, pero el experimento multilenguaje completo ya confirma que esta modificación no altera las 1.000 decisiones pass/fail.

### Priorización a partir de los informes #621

Los fallos Python se distribuyen así entre ambas muestras:
- 471 diferencias de stdout o código de retorno;
- 81 timeouts de programa traducido;
- 75 errores de sintaxis Python generado;
- 6 salidas de traducción que superan el límite de captura;
- 3 timeouts del traductor y 2 salidas no exitosas del traductor.

El nombre `file_cobol_record_information_rec` aparece en 23 casos de primaria y 18 de holdout (41 en total), con `NameError` en las líneas generadas que lo indexan. La inspección del backend revela dos rutas que hay que discriminar: (a) `emit_python` omite variables raíz incluidas en `overlay_buffers`, y `normalize_data_reference` solo usa `_cobol_get` para campos de overlay sin subíndices; los grupos de overlay no tienen una representación de acceso completa; (b) un `COPY` no resuelto o una declaración FILE SECTION que no llega al modelo puede dejar referencias a un nombre ausente. Ambas son **hipótesis**, no causas confirmadas: el informe externo no publica el COBOL original ni el modelo parseado. Antes de cambiar el backend, reproducir uno de los casos reales y registrar `prog.unresolved_copybooks`, las declaraciones parseadas, `build_overlay_layout` y los nombres emitidos. No crear una variable por defecto ni cambiar la representación de overlay sin preservar la semántica de almacenamiento compartido.

Siguiente experimento recomendado: reproducir uno de esos casos de registro de archivo y añadir una prueba que falle en la ruta actual; luego corregir solo el recorrido de símbolos/layout implicado y volver a ejecutar las dos muestras completas. Si no se puede reproducir, priorizar las 471 diferencias de salida por familia y las 75 salidas sintácticamente inválidas.


## Scorecard oficial Python #16: subida bruta no atribuible todavía

El workflow dedicado `external-python-benchmark` terminó para el commit `ba56e5d`:
- Primaria: 168/500 (33,6 %).
- Holdout: 195/500 (39,0 %).
- Total: **363/1.000 (36,3 %)**, frente a 362/1.000 en la ejecución #14.
- Comparación por caso: 0 ganancias en primaria; en holdout, 1 ganancia y 0 regresiones. El caso es `rock-paper-scissors-ad6321acf1`.

El programa de ese caso declara `FUNCTION RANDOM` y usa `ACCEPT CURRENT-TIME FROM TIME` antes de decidir el resultado. Por tanto, la diferencia de una sola ejecución puede ser una variación no determinista y **no prueba que el cambio de referencias cualificadas haya causado la subida**. La ejecución #17 sobre el SHA más reciente debe confirmar si el caso vuelve a pasar; incluso si vuelve a pasar, conviene repetir la prueba del caso de forma aislada para verificar estabilidad.

El workflow multilenguaje #621 selecciona muestras de forma distinta: dio 362/1.000. No mezclar su score con el del workflow dedicado; para la serie histórica 37,5 % → 36,2 % → 36,3 %, usar solo scorecards del workflow dedicado y marcar la variabilidad del caso aleatorio. El objetivo de +5 puntos porcentuales sigue sin alcanzarse.


## Iteración siguiente en curso: #41 — OCCURS tridimensional + REDEFINES

El fixture mínimo ya confirmó un fallo real de semántica: después de escribir `ENTRY-3(2,1,2)` en la vista base, leer `ENTRY-3-1(2,1,2)` desde la vista redefinida devolvía espacios. El código emitido mostraba dos diccionarios independientes (`cobol_3_dimension_tbl` y `cobol_3_dem_tbl`), no almacenamiento compartido.

La PR [#41](https://github.com/orbitalronin94/cobol2py/pull/41) incorpora un layout con strides por dimensión y acceso indexado a un buffer común. La prueba nueva y la suite de 292 tests pasan en Python 3.10, 3.11, 3.12 y 3.13; el workflow diferencial interno también pasa. El benchmark externo de 1.000 programas para este SHA sigue pendiente. La hipótesis de que esto resuelva todos los errores `list indices must be integers or slices, not str` no está demostrada; los resultados por caso determinarán si se mantiene o se revierte.


## Estado actualizado — 2026-10-30: iteraciones D/E integradas

Las PR [#54](https://github.com/orbitalronin94/cobol2py/pull/54) y [#55](https://github.com/orbitalronin94/cobol2py/pull/55) se integraron en `main` mediante `b265e50` y `de7fddd`. El benchmark multilenguaje #697 sobre el SHA pre-merge de la iteración E obtuvo **408/1.000 (40,80 %) Python**: 196/500 primaria y 212/500 holdout. Comparado por ID con la scorecard dedicada #80: 8 ganancias y 0 pérdidas; siete ganancias atribuibles a la corrección `cobol_int`, y una variación temporal de `FunctionCall.cbl` no atribuible. La scorecard dedicada #81 [terminó correctamente](https://github.com/orbitalronin94/cobol2py/actions/runs/41088604039) sobre el mismo SHA: 196/500 primaria, 212/500 holdout y **408/1.000 (40,80 %)**.

### Diagnósticos que deja la iteración E

- `NC2384.2` y `NC238A`: después de resolver la coerción `cobol_int`, el código llega a referencias a índices secundarios que el parser no declara. La cláusula `INDEXED BY` puede incluir varios nombres y continuar en líneas posteriores; el modelo actual conserva solo el primero.
- `NC125A` y `NC1254.2`: avanzan más allá del NameError inicial y exponen `KeyError` en acceso/movimiento de grupos. Requiere inspeccionar el layout y las rutas de datos generadas.
- `DECTRANS`: avanza más allá del NameError inicial y expone `ValueError` al convertir un campo alfanumérico o con espacios a entero. Hay que seguir la semántica PIC/uso del campo antes de elegir coerción o valor por defecto.
- No contar esos seis casos como ganancias: son errores posteriores que quedan visibles al corregir el primer bloqueo.

### Próxima familia: múltiples índices de tabla

Prioridad inmediata: representar todos los nombres declarados por `INDEXED BY`, incluyendo continuaciones multilínea y niveles OCCURS anidados. Añadir pruebas para que cada índice tenga almacenamiento, inicialización y alcance correctos; verificar `SET index TO n`, `SET index UP/DOWN BY n` y `SEARCH ... VARYING index`. En particular, no asumir que declarar variables globales basta: la semántica de cada operación debe respetar el índice que nombra el fuente COBOL.

### Siguiente familia separada: nivel 66 RENAMES

Hay dos candidatos compilables del holdout con referencias no resueltas: `CBL0302v01DataLayoutRenames` y `nivel`. Mantenerlos separados de la corrección de índices para poder atribuir ganancias/regresiones con claridad.


## 8. Mapa de causas raíz — scorecard PR-candidate #41133144593 (2026-10-31)

### Base y método

Esta sección sustituye las prioridades anteriores cuando se decide qué familia atacar a continuación. Se inspeccionaron los dos artefactos de `main` de la ejecución [#41133144593](https://github.com/orbitalronin94/cobol2py/actions/runs/41133144593), con SHA `c0b318955967cf8cfd80ff13ee25107f0a5b6daf`. Ambos informes declaran `archive_md5_verified: true`, `tested: 500` y el mismo criterio de equivalencia exacta (stdout completo + código de retorno).

| Muestra | Aciertos | Fallos | Exactitud |
|---|---:|---:|---:|
| Primaria | 197/500 | 303 | 39,4 % |
| Holdout | 216/500 | 284 | 43,2 % |
| **Total** | **413/1.000** | **587** | **41,3 %** |

La ejecución falló únicamente en el trabajo agregador posterior a los artefactos; los doce artefactos individuales de la competición estaban completos. Esta clasificación se reconstruyó desde `external-corpus-report.json` de los dos artefactos baseline, no desde el agregador. Por tanto, el fallo de agregación no invalida los 1.000 resultados individuales.

Las categorías siguientes son mutuamente excluyentes y suman los 587 fallos:

| Resultado final del caso | Casos | % de los fallos | Techo aritmético sobre 1.000 |
|---|---:|---:|---:|
| Código de retorno distinto | 267 | 45,5 % | 26,7 puntos |
| stdout distinto, mismo código de retorno | 143 | 24,4 % | 14,3 puntos |
| Timeout del programa traducido | 99 | 16,9 % | 9,9 puntos |
| Python generado no compila | 67 | 11,4 % | 6,7 puntos |
| Timeout del traductor | 3 | 0,5 % | 0,3 puntos |
| Límite de captura de salida del traductor | 6 | 1,0 % | 0,6 puntos |
| Excepción de recursión en el traductor | 2 | 0,3 % | 0,2 puntos |

Los techos son límites matemáticos, no previsiones de recuperación. Cada programa solo puede recuperarse una vez y las causas pueden compartir una misma corrección.

**Limitación del artefacto:** el informe enumera los 1.000 resultados, pero los archivos fuente y Python generado se adjuntan principalmente para casos fallidos. No se puede calcular honestamente una tasa de fallo condicionada a cada verbo COBOL ni una correlación fallo/éxito por característica sin recuperar también las fuentes de los casos aprobados. Los recuentos de verbos de esta sección se refieren exclusivamente a cohortes fallidas.

### P0 — I/O de archivos sin semántica ejecutable y control de flujo roto

Es la oportunidad más fuerte y mejor respaldada por el código generado. En los 99 timeouts del programa traducido:

- 96 incluyen `OPEN` en el fuente y emiten `# COBOL no traducido: OPEN`.
- 89 incluyen `WRITE` y emiten la sentencia como no traducida.
- 43 incluyen `READ`; 36 lo emiten como no traducido.
- 96 incluyen `CLOSE`; 34 lo emiten como no traducido.
- 90 de los 99 Python generados contienen marcadores `COBOL estructura malformada`.

Los recuentos se solapan. La evidencia no es solo la presencia de verbos: los artefactos muestran bucles que siguen ejecutándose después de que `READ` no haya actualizado el registro ni el estado EOF. En `seqfileexample-697bdaacde`, por ejemplo, el `READ` queda comentado y el programa traducido asigna repetidamente el centinela `'ÿ'`; en `FP201612`, el `OPEN` y el `READ` quedan sin ejecutar, pero la lógica posterior consulta un FILE STATUS que nunca se actualizó. Hay casos que generan cientos de MB o más de 1 GB de stdout antes del timeout.

Hay otros 120 casos en los que Python termina con código 0 mientras GnuCOBOL termina con código 1. En esta cohorte, el Python generado deja sin ejecutar `OPEN` en 84 casos, `READ` en 72, `CLOSE` en 67 y `WRITE` en 52. Los stderr de referencia muestran, entre otros, 57 errores de archivo inexistente, 21 avisos de cierre implícito, 9 errores permanentes de archivo, 5 errores de terminal y 5 errores de `READ/START` sobre archivos no abiertos para input. El candidato no emite stderr en esos 120 casos.

Además, dentro de los 143 casos con stdout distinto y código de retorno igual, 15 contienen al menos un verbo de archivo emitido como comentario no traducido (15 `OPEN`, 12 `READ`, 7 `WRITE`, 15 `CLOSE`; los recuentos por verbo se solapan).

**Cohorte expuesta a esta familia: al menos 234 casos distintos** (99 timeouts + 120 códigos de retorno distintos por el lado de GnuCOBOL + 15 diferencias de stdout con I/O omitida). Esto equivale a un techo de exposición de 23,4 puntos porcentuales, no a una promesa de recuperación. Para convertirlo en mejora real hay que reproducir y corregir cada comportamiento.

Trabajo recomendado:
1. Modelar `SELECT`, `ASSIGN`, `ORGANIZATION`, `ACCESS MODE`, `RECORD KEY`, `FILE STATUS` y las declaraciones `FD` como un modelo de archivo explícito.
2. Implementar un runtime de archivos que respete `OPEN`, `READ`, `WRITE`, `REWRITE`, `START`, `CLOSE`, EOF, `AT END`, `INVALID KEY` y estados de archivo.
3. Empezar por `LINE SEQUENTIAL` y `SEQUENTIAL`; abordar `INDEXED/DYNAMIC` con claves y duplicados como iteración separada.
4. Hacer que un I/O no soportado produzca un diagnóstico explícito, nunca un comentario silencioso que permita continuar con variables/estados ficticios.
5. Añadir fixtures de archivo existente, archivo ausente, EOF, clave inválida, cierre implícito y modo de acceso incompatible. Comparar stdout y return code con GnuCOBOL.
6. Corregir el parser de bloques para que `AT END` y `NOT AT END` queden asociados al `READ` correcto y no generen bloques malformados.

### P1 — Resolución de nombres, layouts, índices y conversiones

Los 267 fallos de código de retorno se descomponen en 140 casos donde Python termina con código 1 y GnuCOBOL con 0, 120 casos en sentido inverso y 7 diferencias restantes de código (códigos de referencia 11/16). Los 140 errores del candidato tienen traceback. Sus excepciones son:

| Excepción final | Casos |
|---|---:|
| `NameError` | 45 |
| `ValueError` | 37 |
| `TypeError` | 29 |
| `KeyError` | 19 |
| `IndexError` | 3 |
| `AttributeError` | 3 |
| `UnboundLocalError` | 3 |
| `ZeroDivisionError` | 1 |

Pistas concretas:
- `NameError`: nombres de campos/registros o índices que no se declaran/resuelven (`cobol_as_dd1_rec`, `loop_count`, `rdf3_5_16`, `debug_sub_1`, `idx_5`).
- `ValueError`: conversión de espacios a entero, conversiones numéricas y número incorrecto de subíndices en campos overlay.
- `TypeError`: acceso a un entero como tabla, índices de cadena tratados como nombres de campo, comparación de string con entero y llamadas a helpers con aridad incorrecta.
- `KeyError`: claves de grupo/tabla ausentes, incluidas `0` y `computed_a`.

Trabajo recomendado:
1. Seguir cada referencia desde declaración COBOL → jerarquía de datos → resolución de nombre → expresión Python.
2. Agrupar `NameError` y `KeyError` por símbolo raíz y origen (COPY, FD, nivel 88, índice, campo cualificado).
3. Tratar PIC, espacios, escala y signo como semántica COBOL; no resolver `ValueError` con conversiones permisivas indiscriminadas.
4. Crear fixtures separados para overlays, MOVE de grupos, OCCURS multidimensional, índices declarados en grupos y campos numéricos inicializados con espacios.

### P2 — Correctitud sintáctica del Python generado

Los 67 casos sintácticos se distribuyen así:

| Patrón | Casos |
|---|---:|
| Expresión/tokenización inválida | 47 |
| Indentación inesperada | 10 |
| Literal de texto sin cerrar | 3 |
| Literal numérico/identificador mal formado | 3 |
| Delimitadores desbalanceados | 2 |
| L-value no asignable | 1 |
| Expresión condicional incompleta | 1 |

Los ejemplos apuntan a causas distintas, no a una sola limpieza final: tokens COBOL residuales (`TRUE COBOL NOT AT END`, `ZEROES TO ...`), condiciones abreviadas, nombres reservados (`VALUE`, `OF`, `FILE-ID`), índices concatenados, referencias multidimensionales y salida de bloques vacíos con indentación incorrecta.

Trabajo recomendado:
1. Ejecutar `compile(generated, filename, "exec")` inmediatamente después de generar Python.
2. Registrar el nodo/statement COBOL que originó la línea inválida.
3. Corregir el parser o generador en el límite COBOL→IR→Python; no aplicar reemplazos globales sobre Python ya generado.
4. Convertir cada una de las 67 muestras en una regresión o agruparlas solo cuando se demuestre una regla común.

### P3 — Diferencias de stdout con código de retorno igual

Los 143 casos que terminan con el mismo return code siguen siendo fallos exactos. Dentro de esta cohorte:
- 66 fuentes contienen `ACCEPT`.
- 49 Python generados contienen marcadores de estructura de control malformada.
- 15 tienen al menos un verbo de archivo emitido como comentario.
- Entre los 131 casos con stdout de referencia no vacío, 38 producen menos del 1 % de la longitud esperada, mientras que 46 quedan entre el 90 % y el 110 %. La longitud parecida no implica igualdad: se compara byte a byte.

Priorizar la asociación correcta de `ACCEPT` con pantalla/terminal y la estructura de `IF/EVALUATE/PERFORM`, después agrupar diffs byte a byte por padding, formato numérico, espacios, codificación, campos editados y orden de salida. No normalizar stdout.

### Orden de ataque revisado

1. **Runtime de archivos + EOF/FILE STATUS + bloques AT END**, porque hay una cohorte observada de 234 casos expuestos y evidencia directa de operaciones convertidas en comentarios.
2. **Resolución de nombres y representación de datos**, empezando por los 140 tracebacks del candidato y separando símbolos, tablas/índices, overlays y conversiones.
3. **Validador de sintaxis Python y reducción de los 67 casos**, para convertir fallos de generación en fixtures pequeños.
4. **ACCEPT, pantalla y diferencias de salida**, con diffs agrupados por causa, no por programa.
5. Mantener la comparación primaria/holdout y el análisis por ID. No modificar corpus, stdin, timeout, captura, stdout ni criterio de equivalencia para mejorar el score.

La primera iteración técnica debería ser una prueba mínima de `OPEN INPUT` + `READ AT END` + `FILE STATUS`, y otra de `OPEN OUTPUT` + `WRITE` + `CLOSE`. Si no pasan contra GnuCOBOL, no se amplía a organizaciones indexadas. La aceptación exige suite, regresiones, primaria y holdout completos sobre el mismo SHA, con ganancias y pérdidas por ID.


## 2026-11-03 — grouped FILE STATUS / invalid READ candidate

The best completed external candidate measurement in this iteration is PR #283, head 609723976a31c8c666d3e3f7106d30cbaaae980c. The eight checksum-verified Python shards completed successfully in workflow #41599425845:

| Sample | Exact matches | Rate |
|---|---:|---:|
| Primary | 249/500 | 49.8% |
| Holdout | 248/500 | 49.6% |
| Combined | 497/1000 | 49.7% |

This is a candidate observation, not a validated new record. The current main translator blob is 345cbd9c8f40f2673670b5db410bb0ba9c6aa2f2; the best current-main holdout remains 243/500 (48.6%) from workflow #41593293825. A same-SHA current-main primary measurement is not yet available, so the 249 primary result cannot yet be compared to current main case-for-case. The older paired 480/1000 result is from a different translator blob and is historical context only.

The separate multilang run #41599425787, on the same candidate SHA, reported Python 247/500 (49.4%), C 22/500 (4.4%), and Rust 21/500 (4.2%). The two Python holdout measurements differ by one case. Per-case comparison identifies three unstable outcomes: rock-paper-scissors (time/random dependent), d12b (program timeout in one run), and exec84-2 (translator timeout in one run). Keep the corpus and exact-match rule unchanged; repeat the measurement and investigate the nondeterminism before promoting a record.

### Root cause and exposed follow-up

The baseline diagnostics showed six NIST cases failing while a grouped FILE STATUS item was represented as a string and then indexed as a group. The candidate now passes SQ136A, SQ147A, SQ149A, SQ150A, and SQ229A. It exposes the next error in SQ155A: after OPEN INPUT, COBOL attempts WRITE; the generated runtime calls handle.write on a read-only handle and raises io.UnsupportedOperation. COBOL requires file status 48 for a WRITE when the file is not open for OUTPUT, EXTEND, or I-O. The next fix adds that mode guard and a regression that first moves "**" into the grouped status item.

The PR test run #41599425917 failed because web/index.html did not contain the current cobol2py.py source. The translator/runtime tests themselves reached the embedded-source synchronization failure; do not merge until the standalone copy is regenerated and the complete matrix passes.

### Promotion policy

Do not update benchmarks/holdout_best.json or merge this candidate on the basis of the 49.7% observation. First validate the WRITE-mode correction, synchronize the standalone HTML, obtain exact-match primary and holdout comparisons against the same pinned main SHA, and repeat the candidate run to check stability. The 75% target remains 750/1000 exact matches.


## 8. Informe vigente para el torneo de siete hipótesis (2026-11-03)

La línea base de main para el ranking iterativo es **250/500 (50,0 %)**, registrada en `benchmarks/holdout-record.json` y validada en el benchmark externo [run #538](https://github.com/orbitalronin94/cobol2py/actions/runs/41602383991). El último informe de fallos analizado corresponde a una candidata posterior y contiene 500 casos:

| Resultado | Casos |
|---|---:|
| Coincidencia exacta | 250 |
| stdout o return code diferente | 169 |
| Error de sintaxis Python generado | 39 |
| Timeout del programa traducido | 38 |
| Salida de traducción por encima del límite de captura | 3 |
| Timeout del traductor | 2 |

Excepciones Python observadas: `ValueError` 18, `NameError` 18, `TypeError` 15, `KeyError` 10, `UnboundLocalError` 4, `ZeroDivisionError` 3, `AttributeError` 2 e `IndexError` 2. Las excepciones son diagnósticos secundarios y pueden solaparse con mismatches.

### Priorización y límites de evidencia

1. **Emisión Python:** investigar los 39 errores sintácticos y agrupar por línea generada/causa antes de cambiar el emisor.
2. **Símbolos y registros:** rastrear `NameError`/`KeyError` desde la declaración COBOL hasta el símbolo emitido; no añadir variables ficticias.
3. **PIC y conversiones:** reproducir `ValueError`/`TypeError` y separar parsing, operación y asignación al receptor.
4. **OCCURS:** revisar índices, rutas anidadas y diferencias lista/diccionario.
5. **MOVE de grupos:** comprobar si el modelo de diccionarios pierde el layout de almacenamiento, padding u overlays.
6. **INSPECT/STRING/UNSTRING:** no atribuir mismatches sin inspeccionar las fuentes; los issues de estas sentencias son pistas para diseñar fixtures, no prueba de que expliquen los 169.
7. **PERFORM y terminación:** los 38 timeouts justifican investigar control de flujo, pero primero hay que descartar entrada ausente, salida excesiva y bucles propios de cada programa.

La especificación de alcance, fixtures esperadas y gate está en [EXPERIMENT_TOURNAMENT_2026-11.md](EXPERIMENT_TOURNAMENT_2026-11.md). Las siete rutas son hipótesis independientes; ninguna categoría de fallo se asigna a un verbo COBOL sin reproducir el caso.

### Criterio de medición vigente

Solo se utiliza la muestra fija de 500 casos con `skip=500`. El baseline es 250/500 y el mínimo para superar es 251/500. Se exigen cuatro shards completos, checksum verificado, tests completos y SHA exacto. La muestra primaria y el benchmark curado de 105 casos no forman parte del ranking. Esta muestra fija se observa repetidamente y no debe describirse como holdout estadístico intacto.


## 2026-11-05 — baseline pareado de main y pantalla posicional

### Medición y variabilidad

El torneo [#41807663012](https://github.com/orbitalronin94/cobol2py/actions/runs/41807663012) produjo dos artefactos completos y checksum-verificados para el candidato `main-baseline`, ambos sobre SHA `cb005cedbb398c102e5e5b3c3c1ce7ce1833a3d2`:

| Muestra | Exact-match |
|---|---:|
| Primaria | 253/500 (50,6 %) |
| Holdout | 251/500 (50,2 %) |
| **Combinado** | **504/1.000 (50,4 %)** |

El workflow global terminó fallido por una prueba de otra candidata; los dos jobs y artefactos de `main-baseline` terminaron correctamente. He comparado los blobs de `cobol2py.py`, `web/index.html`, tests, reparación guiada, runner, Dockerfile y workflow de benchmark: son idénticos entre `cb005ced` y el main actual `e9f2b9b`. Por tanto, 504/1.000 es una observación pareada del código que sigue en main, no una puntuación de una candidata.

No se promueve todavía a récord reproducible. El caso `rock-paper-scissors-ad6321acf1` es no determinista: en el holdout de main produjo stdout de 83 bytes distinto del de GnuCOBOL, con return code 0 en ambos; en la ejecución holdout de PR #344 pasó. La PR #344 obtuvo 252/500, pero su única ganancia frente a main es exactamente ese caso y no guarda relación causal con el cambio `DIVIDE INTO GIVING`. No hay regresiones en esa comparación, pero tampoco una mejora atribuible. Los ficheros de récord no se sustituyen por esta variación de una ejecución.

### Familia reproducida: DISPLAY posicional de terminal

En diez fallos del baseline (cuatro en primaria y seis en holdout) la fuente usa la forma antigua `DISPLAY (línea, columna) ...`. La ejecución de referencia está en modo no interactivo: GnuCOBOL informa `Error opening terminal: unknown.` por stderr, termina con código 1 y no escribe stdout. El Python generado trataba esas sentencias como DISPLAY ordinario, imprimía coordenadas/prompts o generaba una referencia a `erase` inexistente.

Casos confirmados:
- Ocho `NameError: erase`: `fp201612-3-ae4424744f`, `progr02t-ebdd706b74`, `p20161b-4871fdaff9`, `smp002-508ab1c516`, `smp001-ccd7110609`, `smp005-39d6d84a79`, `pcadamg-ae0a29e0e4` y `pnota-ac81563c54`.
- `cep001-1f7cf0de31`: `DISPLAY (08, 27) MASC1` generaba una expresión Python inválida.
- `progr2-ff3935a6eb`: el candidato agotaba el timeout con stdout vacío, mientras GnuCOBOL terminaba con código 1 y stdout vacío.

La PR [#345](https://github.com/orbitalronin94/cobol2py/pull/345), SHA `6a557a1c2bb4b491c0aa1e7fbf10a4b22885ddcc`, introduce un helper para `DISPLAY (línea, columna)` y `DISPLAY (línea) (columna)`. En procesos sin TTY/TERM reproduce el fallo de inicialización de terminal con código 1 y cero bytes de stdout; en terminal emite secuencias de cursor/borrado. Añade tres regresiones y sincroniza el HTML independiente.

La suite completa de la PR terminó correctamente en [#41995725922](https://github.com/orbitalronin94/cobol2py/actions/runs/41995725922). El benchmark holdout [#41995725847](https://github.com/orbitalronin94/cobol2py/actions/runs/41995725847) y el smoke [#41995725844](https://github.com/orbitalronin94/cobol2py/actions/runs/41995725844) siguen pendientes en la última inspección. No se atribuyen recuperaciones a #345 hasta que finalicen y se comparen por ID; la promoción requiere después primaria y holdout completos sobre el mismo SHA.

### Siguiente familia después de la pantalla

La siguiente reproducción prometedora es la continuación multilínea de nombres de índice en cláusulas `OCCURS ... INDEXED [BY]`. En `NC244A.CBL`, los nombres `IDX-5` y `IDX-8` a `IDX-15` aparecen en líneas físicas siguientes; el parser actual conserva `IDX-1` a `IDX-4` y `IDX-6`/`IDX-7`, pero omite los nombres continuados. El traceback de `NC2444.2` termina en `NameError: idx_5`. Se debe corregir el plegado de la cláusula, inicializar todos los índices y probar `SET index TO`/ `SET index UP BY` antes de abrir otra candidata.

El caso `NC252A` (`rdf3_5_16`) es distinto: el nombre es un nivel 66 `RENAMES`, no un índice. No se deben mezclar ambos cambios ni resolver el segundo creando una variable ficticia.


---

## 8. Estado verificado — 2026-11-14

### Baseline de main

- Main actual: f5b9534ddbbc13d3b30c00afd12c1611f7dece47.
- Traductor medido: f2d944c42fa8d6855effa7d97936db843476b9bd; el único commit posterior hasta el main actual modifica README.md, por lo que el blob de cobol2py.py sigue siendo 3e8a08ae175e6fd1a5d8daba8d3a77ca19dd5061.
- Medición completa: [run 43578366403](https://github.com/orbitalronin94/cobol2py/actions/runs/43578366403), **263/500 (52,6 %)**.
- X-COBOL v2: MD5 cbd974caed72b0836777dc2305928ed3, verificado; skip=500, target=500; cuatro shards completos de 125 (63 + 54 + 73 + 73); 500 IDs únicos.
- El artefacto contiene los 500 fingerprints del oráculo GnuCOBOL (hash y longitud de stdout, código de retorno). Este es el baseline de código actual. No sustituye el récord histórico 257/500 de [run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592), ni el baseline de ranking 250/500 de benchmarks/holdout-record.json.

### Ocho candidatas reconstruidas sobre el main actual

Cada PR pasó su suite, smoke externo y benchmark completo de 500 casos. Los reportes se descargaron y se compararon por ID; no se infirió el resultado del nombre del workflow.

| PR | Hipótesis | Resultado | Delta bruto | Deriva del oráculo | Decisión |
|---:|---|---:|---:|---:|---|
| [#371](https://github.com/orbitalronin94/cobol2py/pull/371) | READ SEQUENTIAL fijo | 262/500 | 0 ganancias, 1 regresión | 9 IDs | No elegible |
| [#372](https://github.com/orbitalronin94/cobol2py/pull/372) | UNSTRING TALLYING acumulativo | 261/500 | 0, 2 regresiones | 9 IDs | No elegible; una regresión estable |
| [#373](https://github.com/orbitalronin94/cobol2py/pull/373) | WRITE FROM literal | 259/500 | 0, 4 regresiones | 8 IDs | No elegible; cuatro regresiones estables |
| [#374](https://github.com/orbitalronin94/cobol2py/pull/374) | READ después de AT END | 262/500 | 0, 1 regresión | 8 IDs | No elegible; una regresión estable |
| [#375](https://github.com/orbitalronin94/cobol2py/pull/375) | OPEN con modos mixtos | 264/500 | +1, 0 | 8 IDs | No elegible por deriva |
| [#376](https://github.com/orbitalronin94/cobol2py/pull/376) | INSPECT REPLACING ALL/FIRST | 263/500 | 0, 0 | 8 IDs | No elegible; no gana casos |
| [#377](https://github.com/orbitalronin94/cobol2py/pull/377) | Longitud aritmética en reference modification | 261/500 | 0, 2 regresiones | 9 IDs | No elegible; una regresión estable |
| [#378](https://github.com/orbitalronin94/cobol2py/pull/378) | STRING DELIMITED BY ZEROES | 262/500 | 0, 1 regresión | 8 IDs | No elegible; una regresión estable |

**La candidata más prometedora es #375.** Su única ganancia es sq206a-3536dcf7c2: pasa de código de retorno 1 a 0, con stdout vacío idéntico y fingerprint de GnuCOBOL estable. No introduce regresiones en los 492 casos con oráculo comparable. Sin embargo, los otros ocho fingerprints no coinciden con el baseline; por el gate absoluto de estabilidad en los 500 IDs, no se promociona ni se fusiona.

Los IDs con deriva en #375 son: rolldice-08e3de1a0e, randomnumbers-d8fc7ee85b, date1-f31ce2734d, collatz-6e335e6eda, randombingo-e50339cc12, intrdate-0517c3d81c, cob-simpleinventory-6af451140a y pullydis-9e45af6c84.

En #371, #372 y #377 también deriva rock-paper-scissors-ad6321acf1. No se cuentan esas diferencias como cambios del traductor.

### Estado de los torneos

- PR [#349](https://github.com/orbitalronin94/cobol2py/pull/349) está integrada; el workflow de 30 semillas sigue siendo manual.
- PR [#368](https://github.com/orbitalronin94/cobol2py/pull/368) integró los fingerprints del oráculo antes de la traducción, también en errores/timeouts del traductor.
- El workflow de 30 semillas compara ahora hash/longitud/código de retorno del oráculo por cada ID. La preparación sigue bloqueada: las 30 ramas existen, pero las 30 están divergidas respecto a main. Las semillas 11–15 solo muestran cambios de workflow/documentación, sin implementación del traductor ni tests/reproducers. No se ha lanzado el torneo.
- El intento de la cohorte de 16 candidatas [#43578366416](https://github.com/orbitalronin94/cobol2py/actions/runs/43578366416) falló en discovery: esperaba 15 PRs de manifiesto y encontró 10. No arrancó jobs de candidatos ni produjo ranking.

### Siguiente trabajo

1. Congelar reloj y aleatoriedad del entorno GnuCOBOL, o generar una sola referencia por caso y reutilizar exactamente esos bytes/códigos en baseline y candidatas. La opción elegida debe conservar el protocolo y quedar versionada; no se deben aceptar fingerprints diferentes.
2. Corregir el agregador de current-main-pr-tournament.yml: antes comparaba solo booleanos de pase y podía aceptar una falsa ganancia aunque cambiara el oráculo. La revisión actual añade fingerprints, hashes de fuente, identidad de checkout y rechazo de deriva.
3. Repetir #375 en una comparación con oráculo idéntico para los 500 IDs. Solo si mantiene sq206a-3536dcf7c2, no pierde ningún caso y no existe deriva, será elegible.
4. Reconstruir las 30 semillas desde el main actual, una hipótesis y un reproducer por rama, sin reciclar diffs divergidos.
