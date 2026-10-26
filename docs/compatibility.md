# Alcance de compatibilidad COBOL

## Qué significa «compatible» aquí

La compatibilidad se debe expresar por construcción y por caso de prueba, no como una etiqueta absoluta. Una traducción puede ser sintácticamente válida y aun así cambiar resultados, formato de datos, flujo de control, efectos de E/S o códigos de salida.

El benchmark actual considera que un caso coincide cuando el `stdout` y el código de retorno del Python generado son iguales a los del ejecutable COBOL compilado por GnuCOBOL. El comando termina con código distinto de cero si el candidato tiene discrepancias o una referencia no compila; `--report-only` se reserva para ejecuciones exploratorias que no deban bloquear CI. El manifiesto contiene 100 programas. El corpus amplía la variedad de casos, pero sigue siendo curado y sesgado hacia construcciones concretas. No mide todos los dialectos, cláusulas, estados de error ni combinaciones de sentencias.

## Áreas cubiertas por el corpus actual (100 casos)

Consulta la lista autoritativa en [`benchmarks/cases.json`](../benchmarks/cases.json). A nivel general, incluye:

- `DISPLAY` con literales y variables.
- Declaraciones sencillas de `PIC X` y `PIC 9`, valores iniciales y campos de ancho fijo.
- `MOVE`, relleno/truncamiento alfanumérico y casos básicos de truncamiento numérico.
- Operaciones aritméticas básicas.
- Comparaciones y condiciones `IF/ELSE`, incluidas algunas condiciones compuestas y anidadas.
- `PERFORM TIMES` y llamadas a párrafos.
- `EVALUATE` escalar con `WHEN`, `WHEN OTHER`, `EVALUATE TRUE/FALSE` y rangos `THRU` en casos acotados.
- `COPY` simple con expansión recursiva, búsqueda por directorios explícitos y diagnósticos de faltantes/ciclos.
- Grupos de datos como diccionarios anidados y referencias básicas a campos hijos.
- Backend Java sobre el mismo AST para el subconjunto cubierto por sus fixtures de compilación/salida.
- Herramienta de diagnóstico GnuCOBOL con `-ftraceall` y snapshots de campos escalares, grupos y elementos `OCCURS` antes de terminar.
- Tablas `OCCURS` y acceso por subíndice en ejemplos acotados.

La lista exacta de características por caso está en el manifiesto; este resumen no amplía por sí mismo el soporte.

En la revisión de PR #9, el traductor candidato coincidió en **100/100 casos (100%)** con GnuCOBOL en `stdout` y código de salida; el snapshot inicial coincidió en **16/100 (16%)** sobre el mismo corpus. No hubo fallos de compilación de las referencias COBOL. Estos resultados son específicos de esa revisión y del manifiesto versionado; no equivalen a una certificación del lenguaje COBOL.

## Qué no se debe inferir

Un resultado favorable no implica automáticamente soporte para:

- campos con signo, decimales, formatos numéricos editados o todas las reglas de redondeo;
- todas las variantes de `MOVE`, `INITIALIZE`, `REDEFINES`, `RENAMES`, `OCCURS DEPENDING ON` o cláusulas de almacenamiento;
- equivalencia de overlays `REDEFINES`, `RENAMES` o grupos complejos con `OCCURS`;
- todo el lenguaje de condiciones, abreviaturas COBOL o precedencia de operadores;
- `EVALUATE ALSO`, selección múltiple avanzada y todos los matices de ámbito/dialecto;
- `COPY ... REPLACING`, bibliotecas calificadas y reglas avanzadas de sustitución;
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
