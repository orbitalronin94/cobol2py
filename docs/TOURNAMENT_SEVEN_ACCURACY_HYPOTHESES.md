# Torneo de siete hipótesis para elevar la exactitud

**Estado:** propuestas falsables; ninguna se considera mejora hasta completar el benchmark diferencial.
**Punto de comparación:** `main` integrado, **240/500 = 48,00 %** (SHA de referencia registrado en el README/PR del torneo).
**Pista experimental:** rama `tournament/string-overflow-semantic-runtime` (incluye los prototipos de PR #210).
**Restricción dura:** no leer para selección, modificar ni ejecutar `benchmarks/legacy_primary/` ni `benchmarks/edge_cases/`.

## Protocolo de torneo

- Crear una rama por hipótesis y mantener cada cambio pequeño, revisable y reversible.
- Comparar siempre con el mismo commit base, comando, corpus permitido, intérprete, dependencias y criterio de equivalencia exacta.
- Registrar SHA, numerador/denominador, fixtures nuevos, tests, tiempo de pared y fallos diferenciales.
- No atribuir una subida de exactitud a una mejora de velocidad. Publicar ambos números por separado.
- Para ganar por exactitud: superar 240/500 en el mismo corpus y sin regresiones en las suites obligatorias. Un empate no gana.
- Para ganar por velocidad: mantener la exactitud en 240/500 o más, pasar los mismos gates y demostrar menor tiempo con varias repeticiones comparables; reportar mediana y dispersión.
- Si una hipótesis no puede aislarse, no combinarla con otra hasta disponer de una medición individual.
- El corpus fijo usado durante el desarrollo no se debe llamar *holdout intacto*.

## H1 — Semántica exacta de `STRING` y puntero

**Predicción:** recuperar casos fallidos en los que el puntero COBOL empieza en una posición no inicial, avanza tras cada envío, o la capacidad del receptor se agota.

**Cambio aislado:** implementar/ajustar el cálculo de posición 1-based, consumo por longitud efectiva y actualización del puntero; preservar el contenido previo y el relleno del receptor según el caso de uso soportado. Mantener `ON OVERFLOW` y `NOT ON OVERFLOW` como ramas mutuamente correctas.

**Fixtures:** puntero 1, puntero intermedio, longitud exacta, un carácter de exceso, receptor ya parcialmente ocupado y puntero fuera de rango.

**Falsación:** cero nuevas coincidencias exactas en los fallos relacionados, o cualquier regresión diferencial fuera de ellos.

## H2 — Longitud COBOL frente a longitud Unicode de Python

**Predicción:** algunos fallos de cadenas proceden de confundir longitud lógica COBOL con longitud de caracteres Python, especialmente con bytes, espacios finales y caracteres multibyte.

**Cambio aislado:** definir explícitamente la unidad de longitud para cada ruta soportada; no aplicar `len(str)` como sustituto universal de longitud de almacenamiento. Para datos byte-oriented, operar con bytes/codec declarado y rechazar codificaciones ambiguas en vez de adivinar.

**Fixtures:** espacios finales, ASCII, caracteres no ASCII en la ruta de texto, truncamiento exacto y comparación por bytes cuando el contrato de salida sea byte-oriented.

**Falsación:** el caso de prueba no reproduce el fallo bajo el contrato documentado, o el cambio rompe el resultado de cualquier fixture previo.

## H3 — Aritmética decimal COBOL sin flotantes binarios

**Predicción:** conversiones `MOVE`, `COMPUTE` y comparaciones con `PIC 9/V/S` pierden coincidencias por usar `float`, redondear donde toca truncar o aplicar mal la capacidad de dígitos.

**Cambio aislado:** encaminar solo las expresiones cuya semántica PIC esté resuelta a decimal exacto; respetar escala, signo, redondeo explícito y desbordamiento. No activar el adaptador globalmente.

**Fixtures:** positivos/negativos, valores en mitad de unidad, truncamiento hacia cero, `ROUNDED`, límites de dígitos y overflow.

**Falsación:** no aumenta el recuento exacto en los programas aritméticos afectados, o el adaptador cambia una ruta no soportada.

## H4 — Normalización léxica y expansión conservadora de PIC

**Predicción:** declaraciones válidas equivalentes se interpretan de forma distinta por espacios, repeticiones `X(n)`/`9(n)`, `USAGE` o colocación de `COMP-3`.

**Cambio aislado:** robustecer tokenizer/parser de PIC y normalizar la representación intermedia sin cambiar aún offsets físicos ni inferir cláusulas ausentes. Todo PIC no reconocido debe marcarse como no soportado, no reinterpretarse silenciosamente.

**Fixtures:** `S9(5)V99 COMP-3`, `PIC X(10)`, `PIC 9(4) COMP`, puntos decimales implícitos y sintaxis deliberadamente inválida.

**Falsación:** ningún caso válido nuevo se reconoce correctamente, o una declaración no soportada pasa a producir una representación aparentemente válida.

## H5 — `OCCURS` y `OCCURS DEPENDING ON` con límites efectivos

**Predicción:** las tablas COBOL fallan por expandirse siempre a la capacidad máxima, usar índices con base cero sin traducirlos, o ignorar el controlador de longitud.

**Cambio aislado:** conservar capacidad máxima y longitud efectiva como conceptos distintos; traducir índices COBOL 1-based explícitamente. Si no se conoce el controlador, mantener el caso como no soportado en vez de inventar su valor.

**Fixtures:** primer/último índice válido, límite máximo, controlador mínimo/máximo y acceso fuera de rango.

**Falsación:** el corpus no contiene una regresión de esta clase o la solución requiere cambios de layout ajenos a esta hipótesis.

## H6 — `REDEFINES`: overlay compartido, no copia independiente

**Predicción:** los grupos redefinidos difieren porque el traductor crea campos independientes donde COBOL comparte el mismo almacenamiento.

**Cambio aislado:** introducir layout/offsets solo para estructuras soportadas y vistas sobre el mismo buffer; no deducir offsets de `PIC` incompletos ni asumir que todos los usos tienen ABI conocido.

**Fixtures:** dos vistas del mismo byte, lectura tras escritura por la vista alternativa, longitudes compatibles y layout no soportado.

**Falsación:** ninguna ganancia diferencial atribuible a overlays o cualquier aliasing accidental entre campos que no se redefinen.

## H7 — Resolución de nombres cualificados y condiciones de nivel 88

**Predicción:** referencias ambiguas a campos repetidos en grupos, `OF/IN` y condiciones de nivel 88 generan accesos al símbolo incorrecto o comparaciones literales incorrectas.

**Cambio aislado:** resolver símbolos con su cadena de cualificación en el árbol de símbolos; representar nivel 88 como condición sobre el campo padre, no como almacenamiento independiente. No cambiar la precedencia general de expresiones en la misma PR.

**Fixtures:** nombres repetidos en grupos hermanos, cualificación `OF`/`IN`, condición 88 con uno y varios valores, y condición falsa.

**Falsación:** no hay incremento de exactitud en los fallos de resolución o se altera una referencia inequívoca existente.

## Orden sugerido

1. H4 (barato, parser y fixtures fáciles de aislar).
2. H1 (alta especificidad; el torneo actual ya investiga `STRING`).
3. H3 (impacto transversal potencial, pero requiere pruebas de borde estrictas).
4. H7 (resolver símbolos antes de alterar emisión).
5. H5 (tablas y límites).
6. H6 (layout compartido, mayor riesgo de regresión).
7. H2 (solo tras confirmar el contrato de bytes/codec de las rutas afectadas).

Este orden es una prioridad experimental, **no una afirmación de impacto demostrado**. Cada hipótesis debe tener PR/candidato propio y su scorecard antes de combinarse.
