# Informe de fallos del benchmark externo y plan de mejora concentrada

**Fecha:** 2026-10-29  
**Proyecto:** `cobol2py`  
**Propósito:** priorizar cambios con mayor potencial de recuperar casos en el corpus externo, sin alterar el corpus ni la métrica.

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
