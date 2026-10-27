# Registro de decisiones de diseño

Este registro recoge decisiones que explican el comportamiento actual. No pretende reconstruir deliberaciones que no quedaron documentadas en su momento: cuando la motivación es una inferencia basada en el código, se indica como tal. Las nuevas decisiones importantes deben añadirse con fecha, estado, contexto y consecuencias.

## D-001 — Un archivo y cero dependencias Python

- **Estado:** aceptada.
- **Decisión:** mantener el traductor principal en `cobol2py.py` y depender solo de la biblioteca estándar.
- **Motivación documentada por el proyecto:** facilidad para descargar, ejecutar, inspeccionar y distribuir.
- **Consecuencias:** baja fricción de uso y despliegue; a cambio, el archivo puede crecer y requiere mantener límites claros entre fases.
- **Revisar si:** el tamaño o complejidad dificultan la revisión y pruebas más de lo que ayuda la distribución en un único archivo.

## D-002 — Priorizar Python legible, no equivalencia total

- **Estado:** aceptada; alcance sujeto a evolución.
- **Decisión:** generar Python que ayude a entender la lógica COBOL, sin afirmar que todas las construcciones o efectos secundarios se preservan.
- **Motivación:** el objetivo descrito por el README es la comprensión de lógica heredada.
- **Consecuencias:** la documentación y los informes deben distinguir legibilidad, sintaxis válida y equivalencia de ejecución.
- **Regla:** no anunciar compatibilidad general basándose solo en que el código generado compila o en una puntuación pequeña del corpus.

## D-003 — Reconocer formato fijo y libre

- **Estado:** aceptada.
- **Decisión:** permitir selección `auto`, `fixed` y `free`.
- **Motivación:** el formato de fuente afecta el tratamiento de columnas, indicadores y comentarios.
- **Consecuencias:** el preprocesado debe tener pruebas para los dos formatos y para líneas de comentario/continuación que se soporten.

## D-004 — Normalizar nombres COBOL para Python

- **Estado:** aceptada.
- **Decisión:** convertir nombres COBOL, incluidos nombres con guiones, en identificadores Python utilizables y legibles.
- **Consecuencias:** la normalización debe ser consistente en declaraciones, referencias y subíndices; hay que evitar colisiones y tratar palabras reservadas.

## D-005 — Modelar el almacenamiento compartido entre párrafos

- **Estado:** aceptada.
- **Decisión:** las variables de `WORKING-STORAGE` utilizadas por los párrafos generados deben conservar su alcance compartido.
- **Motivación:** las variables COBOL de almacenamiento de trabajo no deben convertirse accidentalmente en variables locales independientes de cada párrafo.
- **Consecuencias:** los cambios de generación de funciones deben probar lectura y modificación de estado desde distintos párrafos.

## D-006 — Respetar ancho y truncamiento de campos alfanuméricos

- **Estado:** aceptada para los casos probados.
- **Decisión:** los movimientos hacia campos `PIC X/A` rellenan con espacios o truncan al ancho declarado.
- **Motivación:** los campos alfanuméricos COBOL tienen ancho fijo, a diferencia de los strings Python.
- **Consecuencias:** hay que probar valores más cortos, iguales y más largos, inicialización y tablas. El benchmark mide ejemplos concretos, no todas las variantes de `MOVE`.

## D-007 — Truncamiento de MOVE numérico para PIC 9 sin signo ni escala

- **Estado:** implementada para el subconjunto indicado; verificar en cada cambio.
- **Decisión:** para `PIC 9(n)` sin signo ni escala decimal, un valor de origen con más dígitos conserva los dígitos menos significativos en los casos implementados.
- **Motivación:** se añadió para aproximar el comportamiento observado en los casos de referencia GnuCOBOL.
- **Consecuencias:** no extrapolar esta regla a campos con signo, escala decimal, edición numérica u otras cláusulas sin pruebas específicas.

## D-008 — Ajustar los subíndices COBOL a Python

- **Estado:** aceptada para los accesos soportados.
- **Decisión:** traducir índices COBOL base 1 a índices Python base 0.
- **Consecuencias:** probar primer elemento, elementos posteriores e índice variable; revisar límites y comportamiento fuera de rango por separado.

## D-009 — Comparación diferencial contra GnuCOBOL

- **Estado:** aceptada.
- **Decisión:** mantener programas COBOL de referencia versionados y comparar la salida de Python traducido con la salida de GnuCOBOL.
- **Métrica:** porcentaje de casos cuyo `stdout` y código de salida coinciden exactamente.
- **Consecuencias:** un fallo de caso es evidencia útil y debe permanecer visible. El porcentaje describe solo el corpus de esa revisión; no es porcentaje de semántica COBOL implementada.
- **Herramientas:** `benchmarks/cases.json`, `benchmarks/run_benchmark.py` y el workflow `differential-benchmark.yml`.

## D-010 — Los cierres explícitos de control son unidades independientes

- **Estado:** aceptada para las construcciones soportadas.
- **Decisión:** tratar `END-IF`, `END-PERFORM` y `END-EVALUATE` como cierres estructurales independientes, no como parte del texto de la sentencia anterior.
- **Motivación:** reduce errores de anidamiento y permite generar bloques Python más consistentes.
- **Consecuencias:** añadir pruebas para anidamiento, sentencias posteriores al cierre y combinaciones de cierres.

## D-011 — Mantener un corpus diferencial de 100 programas

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para la revisión del corpus; los resultados se deben volver a medir en cada cambio.
- **Contexto:** el corpus previo de 50 casos no ofrecía suficiente variedad para evaluar regresiones y se añadieron 50 programas, además de corregir fixtures que no compilaban con GnuCOBOL.
- **Decisión:** versionar los 100 casos en `benchmarks/cases.json` y exigir comparación diferencial contra GnuCOBOL, además de pruebas de regresión unitarias para nuevas reglas de traducción.
- **Validación observada en PR #9:** candidato 100/100 (100%) y snapshot inicial 16/100 (16%) en el mismo corpus; las 100 referencias compilaron.
- **Consecuencias:** el porcentaje solo representa este conjunto de programas. Se debe ampliar la diversidad y dificultad de los casos, mantener los casos fallidos y evitar presentar la puntuación como equivalencia COBOL general.
- **Revisión:** añadir casos de estrés y revaluar cuando se incorporen construcciones como `EVALUATE`, escalas decimales, condiciones abreviadas y estructuras anidadas.

## Plantilla para nuevas decisiones

Añadir una sección con:

- **ID y título**
- **Fecha**
- **Estado:** propuesta, aceptada, reemplazada o rechazada
- **Contexto:** problema concreto y evidencia
- **Decisión:** qué se hará
- **Alternativas:** qué otras opciones se consideraron, si se conocen
- **Consecuencias:** ventajas, costes y riesgos
- **Validación:** tests/casos de benchmark que la respaldan
- **Revisión:** qué evidencia podría hacer cambiar la decisión


## D-012 — Tratar literales antes de detectar comentarios y límites de sentencia

- **Estado:** aceptada.
- **Decisión:** el preprocesado elimina el marcador `*>` solo fuera de literales entre comillas y el splitter mantiene cada literal como una unidad al buscar verbos de sentencia.
- **Contexto:** una búsqueda textual ciega puede truncar valores válidos que contengan `*>` o dividir una sentencia al encontrar palabras reservadas dentro de una cadena.
- **Consecuencias:** los casos de regresión deben cubrir comillas duplicadas, marcadores de comentario en literales y verbos COBOL dentro de texto. Esto reduce errores de lexicalización frecuentes, pero no convierte el splitter heurístico en un parser COBOL formal.

## D-013 — El benchmark diferencial debe ser una barrera de CI

- **Estado:** aceptada.
- **Decisión:** el benchmark devuelve un código distinto de cero si el candidato no coincide con GnuCOBOL en todos los casos o si una referencia no compila. `--report-only` queda disponible para análisis exploratorio.
- **Contexto:** un informe que muestra discrepancias pero termina con código cero puede dejar pasar regresiones en integración continua.
- **Consecuencias:** CI falla de forma visible ante cambios incompatibles; las métricas siguen limitadas al corpus versionado y no prueban equivalencia general de COBOL.


## D-014 — Modo estricto y diagnósticos estructurados

- **Estado:** aceptada.
- **Decisión:** exponer `--strict` para rechazar sentencias no soportadas, copybooks no resueltos, estructuras de control malformadas, `REDEFINES` y cláusulas `PIC` numéricas cuya semántica no está garantizada; `--diagnostics-json` emite diagnósticos con código, severidad, línea y mensaje por stderr.
- **Contexto:** comentarios de advertencia en el código generado son útiles para lectura, pero pueden pasar inadvertidos en automatizaciones.
- **Consecuencias:** los consumidores pueden distinguir una traducción parcial de una salida sin los diagnósticos conocidos. El modo estricto solo cubre las limitaciones detectables por el parser actual; no garantiza equivalencia semántica.


## D-015 — Preservar la terminación del programa con STOP RUN

- **Estado:** aceptada para los backends generados.
- **Decisión:** Python propaga una señal interna de terminación hasta el párrafo de entrada, que la captura para no ejecutar sentencias posteriores; Java emite `System.exit(0)`. `GOBACK` y `EXIT PROGRAM` siguen siendo retornos del ámbito actual.
- **Contexto:** traducir `STOP RUN` como un `return` local permite que el párrafo llamador continúe, a diferencia del comportamiento de terminación del programa.
- **Consecuencias:** la regresión cubre `STOP RUN` dentro de un párrafo invocado. El modelo sigue siendo el de un programa independiente; no pretende modelar todos los casos de subprogramas COBOL ni cláusulas de código de retorno.


## D-016 — Registrar fallos de ejecución de la referencia del benchmark

- **Estado:** aceptada.
- **Decisión:** si el ejecutable de referencia GnuCOBOL no puede iniciarse o excede el timeout, el benchmark registra `reference_ok: false`, conserva el detalle en el informe y devuelve un estado de fallo en vez de abortar sin artefactos.
- **Contexto:** un corpus puede contener un bucle infinito o un entorno de ejecución defectuoso; un fallo abrupto dificulta diagnosticarlo y puede impedir publicar el informe.
- **Consecuencias:** los fallos de referencia quedan diferenciados de las discrepancias del traductor, aunque ambos bloquean la barrera por defecto. Un código de salida no cero normal del programa COBOL sigue siendo una referencia válida y se compara exactamente.


## D-017 — Advertir de la aritmética sin semántica completa de tamaño

- **Estado:** aceptada.
- **Decisión:** `--strict` genera `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` para `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE` y `COMPUTE` hasta implementar y verificar la capacidad de dígitos del campo receptor y `ON SIZE ERROR`.
- **Contexto:** la aritmética Python sin límites puede producir resultados que COBOL truncaría, rechazaría o manejaría mediante una rama de error.
- **Consecuencias:** el modo estricto es conservador para programas con aritmética; no afirma que cada operación vaya a desbordar, sino que la equivalencia completa aún no está garantizada.


## D-018 — Decodificar comillas duplicadas en literales COBOL

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para literales completos reconocidos por el traductor.
- **Decisión:** al traducir un literal entre comillas simples o dobles, convertir cada pareja de comillas delimitadoras duplicadas en una sola y serializar el resultado con el escape propio del lenguaje destino.
- **Contexto:** COBOL escapa la comilla delimitadora duplicándola; copiar el contenido textual directamente a Python o Java cambia el valor producido.
- **Consecuencias:** hay regresiones unitarias para ambos delimitadores y ambos backends. Esto no resuelve por sí solo el análisis léxico de literales con comillas duplicadas en todos los contextos de sentencia; el splitter de operandos sigue siendo una limitación que requiere cobertura adicional.
- **Validación:** el código y las pruebas se han actualizado en `main`; la suite completa aún necesita una ejecución verificable.


## D-019 — Hacer visibles las declaraciones de datos no modeladas

- **Fecha:** 2026-10-26.
- **Estado:** aceptada.
- **Decisión:** emitir diagnósticos para `OCCURS DEPENDING ON` sin longitud activa dinámica, niveles `66 RENAMES` y nombres de condición de nivel `88`.
- **Contexto:** el parser omitía algunas declaraciones o conservaba solo la capacidad máxima de una tabla, lo que podía aparentar soporte completo.
- **Consecuencias:** `--strict` falla cuando se detectan estas construcciones; los diagnósticos ayudan a localizar la brecha, pero no implementan la semántica omitida.
- **Validación:** se añadieron pruebas de regresión para los tres códigos de diagnóstico; la ejecución real de la suite aún está pendiente de confirmación en CI.


## D-020 — Diagnosticar EVALUATE ALSO no soportado

- **Fecha:** 2026-10-26.
- **Estado:** aceptada.
- **Decisión:** emitir `UNSUPPORTED_EVALUATE_ALSO` cuando el sujeto de `EVALUATE` o una alternativa `WHEN` contiene `ALSO`.
- **Contexto:** el backend actual no implementa la selección múltiple `ALSO`; traducirla como una comparación escalar puede producir código incorrecto o inválido.
- **Consecuencias:** `--strict` rechaza estos casos detectados en lugar de aparentar compatibilidad. Otras formas de selección no soportadas pueden requerir diagnósticos separados.
- **Validación:** prueba unitaria de `collect_diagnostics`; la ejecución completa de la suite todavía no está confirmada.


## D-021 — Diagnosticar OCCURS sobre grupos

- **Fecha:** 2026-10-26.
- **Estado:** aceptada.
- **Decisión:** emitir `OCCURS_GROUP_UNSUPPORTED` cuando un grupo de datos tenga `OCCURS`, porque el backend no representa cada ocurrencia como un registro anidado independiente.
- **Contexto:** la generación actual de valores por defecto puede colapsar el grupo a un único diccionario en vez de una lista de grupos.
- **Consecuencias:** el modo estricto detecta esta forma de almacenamiento y evita sugerir equivalencia; la implementación de tablas de grupos queda pendiente.
- **Validación:** prueba unitaria que comprueba el diagnóstico y su línea de origen; la suite completa todavía no está confirmada en CI.


## D-022 — Evitar palabras reservadas en identificadores generados

- **Fecha:** 2026-10-26.
- **Estado:** aceptada.
- **Decisión:** prefijar los nombres COBOL que coincidan con palabras reservadas de Python o Java con `cobol_`, aplicando la misma normalización a declaraciones, referencias y subíndices.
- **Contexto:** un nombre de dato o párrafo legal en COBOL puede coincidir con una palabra reservada del lenguaje destino y producir salida inválida.
- **Consecuencias:** se prioriza la sintaxis válida sobre conservar literalmente el nombre; el prefijo debe aplicarse de forma consistente en ambos backends.
- **Validación:** pruebas unitarias de normalización para `CLASS` e índices con `INT`; la suite completa sigue pendiente de confirmación en CI.


## D-023 — Reescribir operadores solo fuera de literales

- **Fecha:** 2026-10-26.
- **Estado:** aceptada.
- **Decisión:** normalizar palabras reservadas y operadores de condiciones únicamente en fragmentos de código fuera de literales COBOL entre comillas.
- **Contexto:** reemplazos textuales de `AND`, `NOT` o `IS` podían alterar el valor de una cadena y cambiar la condición generada.
- **Consecuencias:** las comillas y su contenido permanecen intactos durante la normalización de operadores; la conversión del literal se hace después por el traductor del lenguaje destino.
- **Validación:** regresiones para literales con comillas duplicadas y palabras como `NOT`/`AND`; la ejecución completa de tests sigue pendiente de confirmación en CI.


## D-024 — Mostrar PIC con V como dígitos implícitos en DISPLAY

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para PIC numéricas simples con `V`.
- **Decisión:** al emitir `DISPLAY` de un campo numérico con decimal implícito, formatear la escala declarada y eliminar el punto decimal, rellenando hasta el número de posiciones `9`.
- **Contexto:** `V` declara una posición decimal implícita; no es un carácter visible del campo almacenado.
- **Consecuencias:** la salida de `DISPLAY` es más cercana a la representación numérica COBOL para el subconjunto sencillo. Signo, redondeo, edición y precisión aritmética siguen siendo límites independientes.
- **Validación:** prueba unitaria de la expresión generada; no se ha ejecutado la suite completa en este entorno.


## D-025 — Aplicar NOT al predicado en el backend Java

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para predicados simples; las combinaciones con cadenas y AND/OR siguen siendo parciales.
- **Decisión:** agrupar la negación como `!(predicado)` antes de emitir la condición Java, en vez de anteponer `!` al primer operando.
- **Contexto:** la traducción directa de `NOT WS-X = valor` como `!ws_x == valor` no es Java válido para operandos numéricos y no representa la negación del predicado completo.
- **Consecuencias:** se corrige la precedencia para las condiciones simples cubiertas; condiciones abreviadas y gramáticas complejas siguen requiriendo pruebas adicionales.
- **Validación:** prueba unitaria para `NOT WS-B = 2`; la suite completa todavía no se ha confirmado en CI.


## D-026 — Advertir sobre ordenación alfanumérica incompleta

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para comparaciones detectadas en IF.
- **Decisión:** emitir `ALPHANUMERIC_ORDER_COMPARISON_UNSUPPORTED` cuando una condición `IF` compara un campo `PIC X/A` con un literal mediante `<`, `>`, `<=` o `>=`.
- **Contexto:** la comparación COBOL aplica reglas de ancho y relleno; el backend Java además no puede usar operadores relacionales directamente sobre `String`.
- **Consecuencias:** `--strict` bloquea estas condiciones detectadas hasta implementar comparaciones relacionales compatibles en ambos backends. El diagnóstico actual no cubre todas las expresiones compuestas o contextos distintos de IF.
- **Validación:** prueba unitaria de detección para un campo `PIC X`; la suite completa no se ha confirmado en CI.


## D-027 — No confundir verbos aislados con etiquetas de párrafo

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para GOBACK, CONTINUE y EXIT.
- **Decisión:** excluir estos verbos de la detección heurística de nombres de párrafo cuando aparecen solos con punto, y traducir CONTINUE/EXIT como no-ops.
- **Contexto:** la expresión regular de etiquetas podía interpretar `GOBACK.` como un párrafo nuevo y descartar la sentencia, alterando el flujo de control.
- **Consecuencias:** se preserva el retorno local de GOBACK y se evita que CONTINUE/EXIT desaparezcan. Otros nombres de una sola palabra que colisionen con verbos pueden requerir tratamiento específico.
- **Validación:** prueba de regresión para GOBACK seguido de una sentencia que no debe ejecutarse; la suite completa sigue sin resultado verificable.


## D-028 — No reescribir el signo igual de una desigualdad

- **Fecha:** 2026-10-26.
- **Estado:** aceptada.
- **Decisión:** excluir también `!` del contexto previo al normalizar `=` a `==`, para conservar operadores `!=` ya producidos por `NOT EQUAL TO` y `<>`.
- **Contexto:** la normalización secuencial podía transformar `!=` en el operador inválido `!==`.
- **Consecuencias:** las condiciones de desigualdad vuelven a generar operadores válidos en ambos backends.
- **Validación:** pruebas unitarias para `NOT EQUAL TO` en Python y Java; ejecución completa de la suite aún pendiente.


## D-029 — Preservar el carácter de SPACE en contextos sin tamaño receptor

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para DISPLAY y literales sin contexto de campo receptor.
- **Decisión:** traducir `SPACE`/`SPACES` como un carácter de espacio cuando se usa como literal independiente; `MOVE` a campos alfanuméricos sigue rellenando el ancho del receptor.
- **Contexto:** traducir ambos figurativos a cadena vacía eliminaba un carácter observable en `DISPLAY`.
- **Consecuencias:** el espacio se conserva en ambos backends; las reglas de longitud de figurativos en todos los contextos COBOL siguen siendo más amplias que este caso.
- **Validación:** pruebas unitarias para los dos figurativos en Python y Java; la suite completa aún no está confirmada en CI.


## D-030 — Advertir sobre comparaciones entre campos alfanuméricos

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para comparaciones directas detectadas en IF.
- **Decisión:** emitir `ALPHANUMERIC_FIELD_COMPARISON_UNSUPPORTED` cuando dos campos `PIC X/A` se comparan directamente en una condición `IF`.
- **Contexto:** COBOL puede rellenar el operando más corto con espacios; comparar directamente strings Python/Java de longitudes distintas puede cambiar igualdad y orden.
- **Consecuencias:** el modo estricto señala esta diferencia en vez de afirmar equivalencia; otras expresiones compuestas y referencias cualificadas aún pueden escapar al patrón heurístico.
- **Validación:** prueba unitaria para campos de ancho distinto; la suite completa no se ha confirmado en CI.


## D-031 — Detectar colisiones entre nombres de párrafo y datos

- **Fecha:** 2026-10-26.
- **Estado:** aceptada como diagnóstico conservador.
- **Decisión:** emitir `PYTHON_IDENTIFIER_COLLISION` cuando dos nombres de datos se normalizan al mismo identificador, o los nombres de función de párrafo generados colisionan entre sí o con una variable de `WORKING-STORAGE`.
- **Contexto:** Python comparte el espacio de nombres de variables globales y funciones; una colisión puede sobrescribir una variable o la función de entrada.
- **Consecuencias:** `--strict` detecta los casos heurísticos; la generación normal todavía requiere renombrar el código fuente o resolver manualmente la colisión.
- **Validación:** pruebas unitarias con variable/párrafo `MAIN` y nombres `PRINT`/`COBOL-PRINT` que colisionan tras normalizar; la suite completa no se ha confirmado en CI.


## D-032 — Resolver referencias de datos en EVALUATE Python

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para el subconjunto escalar soportado.
- **Decisión:** pasar el mapa de variables al traducir el sujeto de `EVALUATE` y las alternativas `WHEN`, igual que en las condiciones `IF`.
- **Contexto:** las referencias no cualificadas a campos hijos de grupos podían generarse como variables globales inexistentes.
- **Consecuencias:** se conserva la resolución básica de campos anidados en `EVALUATE`; la selección múltiple `ALSO` y las reglas completas de comparación siguen fuera de cobertura.
- **Validación:** prueba end-to-end para `EVALUATE` sobre un campo hijo no cualificado; la suite completa no se ha confirmado en CI.


## D-033 — Advertir sobre padding de cadenas en EVALUATE

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para sujetos PIC X/A y alternativas WHEN literales detectadas.
- **Decisión:** emitir `EVALUATE_ALPHANUMERIC_PADDING_UNSUPPORTED` cuando una alternativa literal tiene una longitud distinta al ancho PIC del sujeto alfanumérico.
- **Contexto:** la comparación COBOL rellena el operando más corto con espacios; la comparación escalar generada actualmente puede comparar cadenas de longitudes distintas sin padding.
- **Consecuencias:** `--strict` señala los casos directos detectados. El diagnóstico no cubre todas las alternativas variables, sujetos cualificados complejos ni reglas de dialecto.
- **Validación:** prueba unitaria con `PIC X(5)` frente a un literal de tres caracteres; la suite completa sigue sin confirmación en CI.


## D-034 — Convertir ACCEPT según el PIC receptor

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para PIC numéricos y alfanuméricos simples.
- **Decisión:** convertir la entrada a número y aplicar truncamiento básico para PIC numéricos; recortar/rellenar el texto para PIC X/A en ambos backends.
- **Contexto:** asignar siempre `input()`/`Scanner.nextLine()` dejaba strings en variables numéricas y no respetaba el ancho de campos alfanuméricos.
- **Consecuencias:** los casos sencillos de ACCEPT son utilizables con operaciones posteriores; reglas completas de validación de entrada, signo, escala y errores de conversión siguen pendientes.
- **Validación:** pruebas end-to-end Python y unitarias de generación Java; la suite completa no se ha confirmado en CI.


## D-035 — Diagnosticar comparaciones alfanuméricas con literal a la izquierda

- **Fecha:** 2026-10-26.
- **Estado:** aceptada para comparaciones directas detectadas en IF.
- **Decisión:** emitir `ALPHANUMERIC_LITERAL_LEFT_COMPARISON_UNSUPPORTED` si un literal aparece a la izquierda de una comparación con un campo `PIC X/A`.
- **Contexto:** el backend Python no aplica todavía padding al literal de la izquierda y el backend Java no convierte todas esas formas a comparación por valor.
- **Consecuencias:** `--strict` señala los casos directos detectados; expresiones compuestas o cualificadas pueden quedar fuera del patrón.
- **Validación:** prueba unitaria con literal a la izquierda; la suite completa aún no se ha confirmado en CI.

## D-013 — Separar el análisis de cartera del traductor

- **Fecha:** 2026-10-27.
- **Estado:** aceptada para la primera iteración.
- **Contexto:** modernizar una aplicación empresarial requiere entender programas, copybooks, llamadas, JCL y SQL antes de traducir módulos de forma aislada.
- **Decisión:** añadir `cobol2py_agent.py`, un analizador estático de repositorio que genera informes Markdown/JSON y un plan por etapas. Se mantiene independiente del traductor actual y sin dependencias externas.
- **Alternativas:** reemplazar el traductor por un agente LLM o integrar de inmediato un framework de agentes. Se descartan en esta fase porque añaden variabilidad y complejidad antes de disponer de un inventario y criterios de verificación.
- **Consecuencias:** hay una entrada útil para planificar sistemas multiarchivo, pero las referencias se resuelven con heurísticas de texto y nombre; el informe necesita revisión humana y no prueba completitud ni equivalencia.
- **Validación:** pruebas unitarias sintéticas para inventario, dependencias COPY/CALL/JCL/SQL, referencias sin resolver, indicadores de riesgo y serialización JSON. Estas pruebas no se han ejecutado automáticamente en esta modificación.
- **Revisión:** reconsiderar el diseño cuando existan fixtures representativos de repositorios reales y evidencia de precisión/recall del grafo, antes de automatizar escrituras o reparaciones.


## D-036 — Mantener sincronizada la demo HTML con el traductor

- **Fecha:** 2026-10-27.
- **Estado:** aceptada.
- **Contexto:** la mejora del resolvedor de copybooks añadió soporte acotado para parejas de pseudo-texto en `COPY ... REPLACING`, pero la copia del traductor embebida en `web/index.html` quedó desactualizada y falló la prueba de coherencia.
- **Decisión:** sincronizar el bloque `translator-source` con el contenido exacto de `cobol2py.py` en cada cambio del motor y mantener la prueba `test_embedded_translator_stays_in_sync_with_python_source` como guardarraíl.
- **Consecuencias:** la demo ejecuta el mismo código Python que el traductor de línea de comandos; los cambios al traductor deben incluir una actualización del HTML embebido. Esto no elimina las limitaciones semánticas del traductor ni las necesidades de conectividad de Pyodide.
- **Validación:** el bloque embebido se ha regenerado desde el archivo fuente. La suite completa y el resultado del workflow de CI de esta revisión quedan pendientes de confirmación.

## D-037 — Detectar código más allá de la columna 72 antes de inferir formato fijo

- **Fecha:** 2026-10-27.
- **Estado:** aceptada para el modo auto.
- **Decisión:** si una línea larga tiene verbos COBOL de control/sentencia más allá de la columna 72, no inferir formato fijo solo por la sangría de siete espacios. Mantener el contenido para que un END-IF inline no se trunque silenciosamente.
- **Contexto:** el piloto detectó un MALFORMED_CONTROL_FLOW en bench_43_table_first.cbl; la línea contenía END-IF fuera de la zona fija y la heurística lo descartaba.
- **Consecuencias:** se reduce un falso positivo de diagnóstico y se mantiene la traducción de la fixture; los proyectos con formato conocido deben seguir indicando fixed/free explícitamente cuando haya ambigüedad.
- **Validación:** regresión de conservación de END-IF, test de sincronización HTML y benchmark diferencial de 102 casos.


## D-038 — Enmascarar literales antes de extraer dependencias estáticas

- **Fecha:** 2026-10-27.
- **Estado:** aceptada para el inventario CLI y la demo web.
- **Decisión:** conservar offsets y saltos de línea, pero enmascarar el contenido entre comillas antes de detectar COPY, PROGRAM-ID, CALL dinámico, EXEC PGM, INCLUDE y características. Los destinos CALL entre comillas se extraen solo si el verbo CALL está fuera de un literal.
- **Contexto:** patrones como DISPLAY "COPY GHOST" podían producir aristas falsas en un inventario basado en expresiones regulares.
- **Consecuencias:** menos falsos positivos procedentes de cadenas; la extracción sigue siendo heurística y no sustituye un parser de dialecto.
- **Validación:** tests para palabras clave dentro de literales, llamadas literales/dinámicas y smoke test del navegador.


## D-039 — Separar el piloto sintáctico de la ejecución diferencial opt-in

- **Fecha:** 2026-10-27.
- **Estado:** aceptada.
- **Decisión:** el piloto usa esquema v2, clasifica diagnósticos y enlaza fixtures por ruta exacta. Solo el flag explícito --differential ejecuta fixtures del manifiesto contra GnuCOBOL; por defecto no ejecuta el código generado.
- **Contexto:** compilar sintácticamente no demuestra equivalencia, y ejecutar fuentes arbitrarias durante un inventario puede tener efectos no deseados.
- **Consecuencias:** cada archivo declara not-evaluated, matched, discrepancy, reference-error o not-applicable. Los reportes incluyen detalle por fuente y se publican como artefacto de CI.
- **Validación:** CI del piloto: 108/108 fuentes traducidas, cero errores sintácticos/de traducción y 102/102 fixtures diferenciales coincidentes en stdout/código de retorno. Quedan 35 fuentes con avisos de aritmética/PIC que requieren revisión humana.

## D-040 — Soportar ADD ... TO ... GIVING y REDEFINES anidados

- **Estado:** aceptada para el subconjunto probado.
- **Decisión:** traducir el resultado de `ADD operandos TO receptor GIVING destino` al destino separado, y permitir que el elemento base y sus vistas `REDEFINES` sean hermanos dentro de un grupo de datos.
- **Consecuencias:** el almacenamiento físico compartido prevalece sobre la representación anidada de los grupos en Python; la fixture diferencial `LABERINTO-COBOL` cubre `ALTER`, `GO TO ... DEPENDING ON`, `REDEFINES` anidado y `ADD ... GIVING`. `samples/laberinto_cobol_original.cbl` conserva además la declaración `PIC S9(9) COMP` original para regresión de ejecución; el formato de salida DISPLAY de campos signed COMP no se certifica con el benchmark diferencial.


## D-041 — Implementar un subconjunto verificable de SEARCH ALL

- **Estado:** aceptada para el subconjunto probado.
- **Decisión:** representar tablas `OCCURS` de registros como listas de diccionarios, conservar la longitud máxima y limitar `SEARCH ALL` por `DEPENDING ON`; requerir `ASCENDING KEY` y `INDEXED BY` y traducir la búsqueda como búsqueda binaria con conversión del índice base 1.
- **Contexto:** la fixture inicial no declaraba una clave ascendente y sus claves no estaban ordenadas, por lo que no constituía un caso válido para `SEARCH ALL`. También omitía los efectos de salida al desenrollar el `PERFORM` recursivo.
- **Consecuencias:** se añadió una fixture corregida y una prueba unitaria; no se anuncia coincidencia diferencial hasta ejecutar la fixture con GnuCOBOL.
