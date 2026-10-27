# Alcance de compatibilidad COBOL

## Qué significa «compatible» aquí

La compatibilidad se debe expresar por construcción y por caso de prueba, no como una etiqueta absoluta. Una traducción puede ser sintácticamente válida y aun así cambiar resultados, formato de datos, flujo de control, efectos de E/S o códigos de salida.

El benchmark actual considera que un caso coincide cuando el `stdout` y el código de retorno del Python generado son iguales a los del ejecutable COBOL compilado por GnuCOBOL. El comando termina con código distinto de cero si el candidato tiene discrepancias o una referencia no compila; `--report-only` se reserva para ejecuciones exploratorias que no deban bloquear CI. El manifiesto contiene 101 programas. El corpus amplía la variedad de casos, pero sigue siendo curado y sesgado hacia construcciones concretas. No mide todos los dialectos, cláusulas, estados de error ni combinaciones de sentencias.

## Áreas cubiertas por el corpus actual (101 casos)

Consulta la lista autoritativa en [`benchmarks/cases.json`](../benchmarks/cases.json). A nivel general, incluye:

- `DISPLAY` con literales y variables.
- Declaraciones sencillas de `PIC X` y `PIC 9`, valores iniciales y campos de ancho fijo.
- `MOVE`, relleno/truncamiento alfanumérico y casos básicos de truncamiento numérico.
- Operaciones aritméticas básicas.
- Comparaciones y condiciones `IF/ELSE`, incluidas algunas condiciones compuestas y anidadas.
- `PERFORM TIMES` y llamadas a párrafos.
- `EVALUATE` escalar con `WHEN`, `WHEN OTHER`, `EVALUATE TRUE/FALSE` y rangos `THRU` en casos acotados.
- `COPY` con expansión recursiva, búsqueda por directorios y diagnósticos de faltantes/ciclos; el corpus diferencial incluye un caso de pareja simple de pseudo-texto en `REPLACING`.
- Grupos de datos como diccionarios anidados y referencias básicas a campos hijos.
- Backend Java sobre el mismo AST para el subconjunto cubierto por sus fixtures de compilación/salida.
- Herramienta de diagnóstico GnuCOBOL con `-ftraceall` y snapshots de campos escalares, grupos y elementos `OCCURS` antes de terminar.
- Tablas `OCCURS` y acceso por subíndice en ejemplos acotados.

La lista exacta de características por caso está en el manifiesto; este resumen no amplía por sí mismo el soporte.

En la revisión histórica de PR #9, el traductor candidato coincidió en **100/100 casos (100%)** con GnuCOBOL en `stdout` y código de salida; el snapshot inicial coincidió en **16/100 (16%)** sobre aquel corpus. En el commit [`2b6ab18`](https://github.com/orbitalronin94/cobol2py/commit/2b6ab18ad10f2aace74d24082ccde41139969264), el corpus ampliado de 101 casos obtuvo **101/101 coincidencias (100%)** con la versión inicial de una pareja de reemplazo del caso `copy-replacing-basic`. Después se amplió ese fixture a dos parejas en una cláusula y el commit [`9364ba6`](https://github.com/orbitalronin94/cobol2py/commit/9364ba6f8fd28e0f089409e91f826068d87c1502) volvió a obtener **101/101 coincidencias (100%)**, incluida la fixture ampliada. El snapshot inicial no soporta ese caso. No hubo fallos de compilación de las referencias COBOL. Estos resultados son específicos de esa revisión y del manifiesto versionado; no equivalen a una certificación del lenguaje COBOL.

## Qué no se debe inferir

Un resultado favorable no implica automáticamente soporte para:

- campos con signo, decimales, formatos numéricos editados o todas las reglas de redondeo;
- todas las variantes de `MOVE`, `INITIALIZE`, `REDEFINES`, `RENAMES`, `OCCURS DEPENDING ON` o cláusulas de almacenamiento;
- equivalencia de overlays `REDEFINES`, `RENAMES` o grupos complejos con `OCCURS`;
- todo el lenguaje de condiciones, abreviaturas COBOL o precedencia de operadores;
- `EVALUATE ALSO`, selección múltiple avanzada y todos los matices de ámbito/dialecto;
- bibliotecas calificadas de `COPY`, otras formas de `REPLACING` y reglas avanzadas de sustitución;
- `READ`/`WRITE`, archivos, bases de datos, transacciones, llamadas externas o comportamiento de entorno;
- todas las variantes de `EVALUATE`, `SEARCH`, `STRING`, `UNSTRING`, `INSPECT`, `CALL`, `COPY`, `EXEC SQL` o extensiones de dialecto;
- equivalencia en mensajes de error, salida estándar de error, archivos producidos, estado global externo o efectos secundarios no medidos.

El backend Java tiene un subconjunto más acotado que el backend Python y requiere revisar cada sentencia no cubierta antes de usar la salida. Esta lista no afirma que cada elemento esté completamente ausente del código; indica que el corpus actual no basta para declarar equivalencia general de esas áreas.

## Política para añadir casos

1. Crear un programa mínimo y autónomo que aísle una semántica concreta.
2. Confirmar que GnuCOBOL lo compila y guardar la salida esperada en la comparación, no como una expectativa copiada a mano.
3. Añadirlo a `benchmarks/cases.json` con un ID estable y características precisas.
4. Mantener el caso aunque falle el traductor; el fallo representa una brecha real de cobertura.
5. Cuando se corrija la brecha, añadir o conservar un test de regresión unitario que falle si la regresión reaparece.
6. Evitar casos duplicados que inflen el número sin añadir un comportamiento nuevo.
7. Registrar limitaciones y cualquier diferencia específica de dialecto.

## Interpretación del porcentaje

`casos coincidentes / casos ejecutados × 100`

Cada caso pesa lo mismo, independientemente de su tamaño o complejidad. Por ello, el porcentaje es una métrica de regresión del corpus, no una estimación estadística de equivalencia para programas COBOL arbitrarios. Cambiar el corpus puede cambiar la puntuación aunque el traductor no cambie; las comparaciones entre versiones deben usar el mismo manifiesto.


## Modo estricto y diagnósticos

`--strict` termina con código 2 cuando el traductor detecta sentencias no soportadas, copybooks sin resolver, bloques de control malformados, overlays `REDEFINES` o semántica numérica `PIC` parcialmente cubierta. `--diagnostics-json` emite una lista JSON por stderr con `code`, `severity`, `line` y `message`. Estos diagnósticos son una ayuda para automatizar revisiones, no una prueba de que una traducción sin advertencias sea semánticamente equivalente a COBOL.


`STOP RUN` se emite como señal de terminación que se propaga hasta el párrafo de entrada en Python y como `System.exit(0)` en Java. `GOBACK` y `EXIT PROGRAM` se mantienen como retornos locales. La semántica de códigos de retorno y de subprogramas COBOL sigue fuera de la garantía general.


El benchmark también registra los errores de lanzamiento o timeout al ejecutar la referencia COBOL (`reference_ok: false`) y termina con error de forma controlada. Un código de salida no cero producido por el programa COBOL no se considera por sí solo un fallo de referencia: forma parte del resultado esperado y se compara con el traductor.


El modo estricto también señala `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE` y `COMPUTE`, ya que el tamaño del campo receptor y `ON SIZE ERROR` no están implementados de forma completa. Es una advertencia conservadora sobre la cobertura, no una afirmación de que cada operación concreta produzca un desbordamiento.


## Literales y comillas escapadas

Los literales completos entre comillas simples o dobles decodifican las comillas delimitadoras duplicadas de COBOL, incluso en operandos y expresiones. Por ejemplo, `"DON""T"` representa el texto `DON"T`. Se han añadido regresiones para Python, Java y cláusulas `VALUE`. El splitter y el parser siguen siendo heurísticos; no debe inferirse soporte de todas las construcciones de literal ni de todos los dialectos.


## Declaraciones de datos omitidas o aproximadas

`OCCURS DEPENDING ON` se reserva con el máximo de ocurrencias, pero la longitud activa no se actualiza según el contador; `--strict` emite `OCCURS_DEPENDING_ON_UNSUPPORTED`. Los niveles `66 RENAMES` y `88` se omiten del modelo de variables y ahora generan `UNSUPPORTED_RENAMES` y `UNSUPPORTED_CONDITION_NAME_88`. No se deben tratar estos programas como equivalentes aunque el resto del código se traduzca.


`EVALUATE ALSO` no se traduce como selección múltiple. El modo estricto emite `UNSUPPORTED_EVALUATE_ALSO` si detecta `ALSO` en el sujeto o en una alternativa `WHEN`; esto no garantiza que todas las variantes avanzadas de `EVALUATE` estén detectadas.


Los grupos de datos con `OCCURS` tampoco se representan todavía como listas de registros anidados; el modo estricto emite `OCCURS_GROUP_UNSUPPORTED`. Esta advertencia es distinta de `OCCURS_DEPENDING_ON_UNSUPPORTED`, que se refiere a la longitud activa dinámica de una tabla.


Para un `DISPLAY` simple de un campo numérico con `V` implícita, el backend Python emite las posiciones de dígitos sin punto decimal visible. Esto no implica que todas las reglas de redondeo, signo, aritmética o PIC editadas estén cubiertas.


Las comparaciones relacionales de campos `PIC X/A` con literales en condiciones `IF` no están garantizadas. El modo estricto emite `ALPHANUMERIC_ORDER_COMPARISON_UNSUPPORTED` para los casos directos detectados; la cobertura de expresiones compuestas y otros contextos es incompleta.


Las comparaciones directas entre dos campos alfanuméricos en `IF` también pueden diferir cuando sus anchos no coinciden. El modo estricto emite `ALPHANUMERIC_FIELD_COMPARISON_UNSUPPORTED` para los casos simples detectados; no cubre todas las referencias cualificadas, subíndices ni expresiones compuestas.


Los nombres de párrafo que colisionan con variables globales o con otra función generada, y los nombres de datos que convergen al mismo identificador normalizado, pueden sobrescribirse o confundirse en Python. El modo estricto emite `PYTHON_IDENTIFIER_COLLISION` para los casos directos detectados; la salida normal no renombra automáticamente estas colisiones.


`ACCEPT` convierte la entrada de campos numéricos simples y recorta/rellena campos `PIC X/A` según su ancho. No reproduce toda la validación de entrada COBOL ni todas las reglas de signo, escala o conversión inválida.

En Java, las comparaciones directas de un campo `PIC X/A` con un literal a la derecha usan comparación por valor y padding básico, incluso en condiciones compuestas sencillas con `AND`/`OR`. Las comparaciones de cadenas invertidas (literal a la izquierda), comparaciones entre campos alfanuméricos y referencias cualificadas complejas siguen fuera de la garantía; el modo estricto no detecta todas estas formas.


Las comparaciones alfanuméricas con un literal a la izquierda (`"A" = WS-NAME`) no están garantizadas; el modo estricto emite `ALPHANUMERIC_LITERAL_LEFT_COMPARISON_UNSUPPORTED` para las formas directas detectadas.


## Alcance específico de COPY REPLACING

El resolvedor acepta cláusulas con una o más parejas de pseudo-texto de la forma:

```cobol
COPY FIELD REPLACING ==:FIELD-NAME:== BY ==WS-CODE==.
```

Aplica las sustituciones al texto leído del copybook antes de analizarlo. La coincidencia es literal, insensible a mayúsculas/minúsculas y no se interpreta como expresión regular. Esto es una implementación acotada, no el algoritmo completo de sustitución léxica de COBOL: no debe suponerse que respete límites de tokens, todas las reglas de pseudo-texto o todas las variantes de dialecto. Si la cláusula no coincide con la forma admitida, el traductor deja una advertencia explícita de copybook no resuelto en lugar de omitirla silenciosamente.

La regresión unitaria `test_copy_replacing_applies_pseudo_text_before_parsing` comprueba el caso cubierto. Ese test no forma parte de la puntuación del benchmark diferencial de 100 programas, por lo que no debe presentarse como evidencia de equivalencia general ni como cobertura de reemplazos complejos.


## Regresión diferencial de COPY REPLACING

El caso `copy-replacing-basic` usa `samples/copy_replacing.cbl` y `samples/R.cpy` para comparar el programa traducido con el resultado compilado por GnuCOBOL. Verifica dos parejas sencillas en una sola cláusula: renombrado de campo y reemplazo del texto de una cláusula `PIC`. No cubre pseudo-texto complejo, límites léxicos generales ni reglas avanzadas de dialecto.


## Aritmética y tamaño del campo receptor

Las sentencias básicas `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE` y `COMPUTE` aplican una adaptación acotada al PIC numérico receptor: se conserva la capacidad de dígitos y se descartan dígitos de orden superior en los casos simples cubiertos. La fixture diferencial `arithmetic-receiving-pic` valida overflow de `PIC 99` con GnuCOBOL. Esto no implementa toda la semántica de `ON SIZE ERROR`, redondeo, escalado `P`, ni todas las reglas de signo y precisión decimal; los casos fuera del subconjunto deben tratarse como limitación.
