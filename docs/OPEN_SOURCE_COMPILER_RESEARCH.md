# Investigación de arquitectura: compiladores COBOL y traductores

**Fecha de corte:** 2026-10-29  
**Propósito:** extraer patrones de diseño aplicables a Cobol2Py; no copiar código ni inferir equivalencia semántica a partir de claims de marketing. Las puntuaciones del benchmark externo estricto siguen siendo la única medida de éxito del traductor Python.

## Hallazgos verificados en las fuentes

### 1. ProLeap: separar sintaxis y semántica

Fuentes:
- https://github.com/uwol/proleap-cobol-parser
- https://github.com/uwol/proleap-cobol
- Gramática: https://github.com/uwol/proleap-cobol-parser/blob/master/src/main/antlr4/io/proleap/cobol/Cobol.g4

El README del parser describe una gramática ANTLR4 que produce AST y ASG. El AST representa la estructura sintáctica; el ASG se construye con análisis semántico y expone información sobre datos y flujo, como los accesos a variables. El proyecto también tiene un preprocesador para COPY/REPLACE y extrae los bloques EXEC SQL/SQLIMS/CICS como texto. El README afirma que pasa la suite NIST; esto es una afirmación del propio proyecto, no una medición comparable con el corpus externo de Cobol2Py.

**Patrón a adoptar:** la resolución de nombres, jerarquía de datos y referencias no debería depender de volver a aplicar regex al texto de cada sentencia. Construir una tabla de símbolos semántica a partir de declaraciones ya parseadas y hacer que las expresiones resuelvan a símbolos con identidad y ruta de acceso.

**Aplicación prioritaria:** los fallos de índices multidimensionales, nombres cualificados, registros de archivo y REDEFINES. Antes de generar Python, validar referencias no resueltas y registrar su ubicación y causa.

### 2. GnuCOBOL: definir semántica observable

Fuentes:
- Código fuente (espejo mantenido por OCamlPro): https://github.com/OCamlPro/gnucobol
- Parser: https://github.com/OCamlPro/gnucobol/blob/master/cobc/parser.y
- Chequeo semántico/tipos: https://github.com/OCamlPro/gnucobol/blob/master/cobc/typeck.c
- Generación de código: https://github.com/OCamlPro/gnucobol/blob/master/cobc/codegen.c
- Modelo y almacenamiento de campos: https://github.com/OCamlPro/gnucobol/blob/master/cobc/field.c
- Manual: https://gnucobol.sourceforge.io/doc/gnucobol.html

Se inspeccionaron los archivos fuente indicados y se confirmó la separación por componentes `cobc` y `libcob` que documenta el README del espejo. El manual documenta que `cobc -E` preprocesa directivas y expande COPY; `cobc -C` traduce COBOL a C; `cobc -S` compila a ensamblador.

GnuCOBOL debe seguir siendo el oráculo de ejecución. El código C emitido es una herramienta de investigación para casos concretos: comparar cómo se representa una operación, qué llamadas de runtime genera y cómo se materializan registros, archivos y control de flujo. No conviene intentar reimplementar todo el runtime de una vez.

**Patrón a adoptar:** para cada fallo representativo, conservar el COBOL original, la salida/código de retorno de referencia y, cuando ayude, el C generado. Esos artefactos sirven para formular una hipótesis semántica y diseñar un fixture mínimo. Nunca relajar la comparación exacta de stdout y return code.

**Detalle observado en la fuente:** el modelo de campos de `cobc/field.c` valida restricciones de REDEFINES, incluyendo casos donde la definición original no puede tener longitud variable. Esto apunta a una lección concreta: validar restricciones entre declaraciones antes del codegen, en lugar de tratar REDEFINES como una simple asignación de dos nombres al mismo buffer. La lógica relacionada está en el código fuente enlazado; no se ha portado código.

### 3. opensource COBOL 4J: compilador por etapas y runtime

Fuentes:
- https://github.com/opensourcecobol/opensourcecobol4j
- README y changelog del proyecto.

El README confirma que el compilador traduce COBOL a Java y comparte una parte considerable de su base con opensource COBOL, que traduce a C. El proyecto declara soporte para operaciones de datos, flujo de control, llamadas, archivos secuenciales/indexados/relativos y SORT. Su changelog muestra que la cobertura evoluciona por correcciones concretas: por ejemplo, OCCURS DEPENDING ON, VALUE ALL, FILE/WRITE y generación de GO TO.

**Patrón a adoptar:** usar cambios pequeños y tests específicos por constructo; estudiar tanto el compilador como su runtime. La semántica no termina al generar código sintácticamente válido: depende de rutinas de datos y ejecución.

### 4. Koopa: preprocesamiento y formatos fuente

Fuente:
- https://github.com/krisds/koopa

Su README describe un parser generador para COBOL, island parsing, formatos fixed/free/variable, tolerancia a fragmentos CICS/SQL y preprocesamiento de COPY con REPLACING y REPLACE.

**Patrón a adoptar:** separar claramente normalización de formato/preprocesamiento del parseo de sentencias. Un bloque embebido no soportado debe conservarse como una unidad identificable y diagnosticable, no corromper silenciosamente el texto que le rodea.

### 5. CobGo: frontera AST → IR → backend

Fuentes:
- https://github.com/CoreBankLang/CobGo_community
- https://github.com/CoreBankLang/CobGo_community/blob/main/docs/ARCHITECTURE.md
- https://github.com/CoreBankLang/CobGo_community/blob/main/pkg/ir/converter.go

La documentación describe etapas de parser/AST, generación de IR, validación de tipos, codegen y runtime. El conversor AST→IR usa una frontera explícita, acumula errores de conversión y transporta ubicaciones de línea/columna en nodos IR. Este proyecto debe estudiarse como referencia de estructura, no asumir que toda su cobertura o sus claims se trasladan a Cobol2Py.

**Patrón a adoptar:** una IR pequeña y tipada, con ubicaciones de origen, errores explícitos y una frontera estable entre análisis y generación. No intentar diseñar una IR universal completa antes de demostrar el beneficio en un subconjunto de sentencias.

### 6. PythonBol-Translator: comparación de backend y runtime

Fuentes:
- https://github.com/IronAdamant/PythonBol-Translator
- https://github.com/IronAdamant/PythonBol-Translator/blob/main/src/cobol_safe_translator/mapper_codegen.py
- https://github.com/IronAdamant/PythonBol-Translator/blob/main/src/cobol_safe_translator/parser.py

El repositorio se presenta como traductor Python sin dependencias, con un parser por regex/máquina de estados, módulos separados para parsing de procedimiento, PIC y generación, y adaptadores runtime. Su propio README advierte que genera skeleton code y que ciertas integraciones middleware requieren trabajo adicional. Por tanto, sus claims de validación/sintaxis **no equivalen** a la tasa de acierto semántico exacto del benchmark de Cobol2Py.

**Patrón a adoptar:** modularizar parser, PIC, bloques de control, generación y runtime; estudiar el manejo de nombres duplicados, OCCURS y overlays como casos comparativos. No tomar su sintaxis válida como evidencia de equivalencia.

## Arquitectura incremental recomendada para Cobol2Py

No reescribir el proyecto de golpe. Mantener el parser actual y construir una frontera semántica incremental:

1. **Fuente normalizada:** preservar número de línea, formato, expansión COPY y diagnósticos.
2. **Modelo de declaraciones:** completar jerarquía padre/hijo, PIC, VALUE, OCCURS/DEPENDING, REDEFINES y metadatos FD/SD.
3. **Tabla de símbolos:** resolver nombre + calificadores + subíndices a un símbolo concreto; registrar ambiguos/no resueltos en vez de inventar variables.
4. **IR mínima de procedimiento:** representar expresiones, referencias, asignaciones, condiciones, llamadas PERFORM y operaciones I/O en nodos tipados con ubicación de origen. No mezclar todavía todos los verbos COBOL.
5. **Validación semántica previa a codegen:** referencias, dimensiones, destinos de asignación y nombres de párrafo; emitir diagnósticos que señalen la fuente.
6. **Backend Python:** generar desde nodos resueltos y reutilizar helpers de runtime para semántica COBOL, en vez de interpretar fragmentos de texto de nuevo.
7. **Ejecución diferencial:** compilar el resultado, ejecutar contra la referencia GnuCOBOL, comparar stdout y return code, y clasificar cada diferencia.

## Primer experimento de ingeniería (sin reescritura)

**Hipótesis:** resolver referencias de datos una sola vez desde un modelo jerárquico reducirá los errores de acceso a tablas y campos cualificados sin introducir regresiones en los programas que ya pasan.

**Subconjunto inicial:** referencias simples y cualificadas, OCCURS anidado/multidimensional y REDEFINES; dejar fuera cambios amplios a control de flujo en esta iteración.

**Pruebas mínimas:**
- campo simple, campo con OF/IN y nombres duplicados en grupos distintos;
- tabla unidimensional, tabla multidimensional, grupo OCCURS con campo elemental;
- REDEFINES sobre campos del mismo padre;
- referencias de registro FD/SD;
- programa de regresión que compara salida y código de retorno con GnuCOBOL.

**Aceptación:** pruebas unitarias/diferenciales verdes; ninguna regresión no explicada; benchmark externo primaria y holdout completos para el mismo SHA; comparar ganados/perdidos con la referencia 375/1000. Si el cambio no demuestra mejora o introduce regresiones sin explicación, no declararlo avance.

## Límites de la investigación actual

Esta nota se basa en README, documentación de arquitectura, gramática y archivos fuente seleccionados de los repositorios enlazados. No afirma que se haya compilado o ejecutado cada proyecto, ni que se haya completado una auditoría de sus repositorios. Antes de adoptar una técnica concreta, inspeccionar su implementación y tests relevantes. Revisar licencias antes de reutilizar cualquier código; la intención aquí es aprender patrones, no copiar implementaciones.


## Segunda pasada: detalles de implementación contrastados

Esta sección amplía la lectura de fuentes más allá de los README. Sigue siendo investigación estática; no se ha portado código de terceros ni ejecutado sus suites completas.

### GnuCOBOL: REDEFINES es una relación estructural, no un alias nominal

En `cobc/field.c`, `cb_resolve_redefines`:
- rechaza un destino `REDEFINES` cualificado o con subíndices;
- busca una definición previa con ese nombre;
- exige que el destino esté bajo el mismo padre y tenga el mismo nivel;
- por defecto rechaza redefinir una entrada que ya es una redefinición indirecta, y recorre la cadena hasta la definición original.

En la validación de campos se comprueba además que la cláusula aparezca en el orden permitido y se rechazan definiciones redefinidas u originales de longitud variable en los casos correspondientes. La validación de `OCCURS DEPENDING ON` también impone restricciones sobre dónde puede estar la tabla en la jerarquía, según las opciones de dialecto.

**Consecuencia para Cobol2Py:** no incorporar un arreglo general que convierta todo `REDEFINES` en dos atributos Python que apuntan al mismo objeto. Hay que resolver el nombre de la definición original, validar padre/nivel/orden y representar el almacenamiento compartido con offsets y longitudes. Si la representación actual no conserva esos datos, primero añadirlos al modelo; si no se puede demostrar equivalencia para un caso, emitir un diagnóstico en vez de generar una traducción aparentemente correcta.

Fuente inspeccionada: [`cobc/field.c`](https://github.com/OCamlPro/gnucobol/blob/master/cobc/field.c), especialmente `cb_resolve_redefines`, `validate_occurs` y la validación de REDEFINES.

### ProLeap: el grammar reconoce ODO, pero el parser no sustituye la resolución semántica

En `Cobol.g4`, la entrada de datos permite `OCCURS`, un límite opcional `TO`, `DEPENDING ON` con un `qualifiedDataName`, y cláusulas de ordenación e índices. Esto permite reconocer una estructura más rica que un simple `OCCURS n`.

**Consecuencia para Cobol2Py:** no basta con extraer el primer número de `OCCURS`. El modelo debe distinguir mínimo/máximo, campo controlador, índice y ruta de datos; el paso semántico debe resolver el controlador a un símbolo. La gramática es una referencia útil para construir fixtures, pero no se adopta automáticamente la gramática completa de ProLeap.

Fuente inspeccionada: [`Cobol.g4`](https://github.com/uwol/proleap-cobol-parser/blob/master/src/main/antlr4/io/proleap/cobol/Cobol.g4), reglas `dataOccursClause` y `dataOccursDepending`.

### opensource COBOL 4J: las tablas dinámicas afectan más que la declaración

La revisión de `cobj/codegen.c` muestra que el generador consulta `occurs_depending` al calcular tamaños/offsets y al generar el límite usado por `SEARCH`; si no hay campo controlador, utiliza el máximo declarado. Su changelog registra correcciones independientes para `OCCURS DEPENDING ON`, `SEARCH` sobre tablas dinámicas, `COMPUTE`, `ADD/SUBTRACT`, comparaciones numéricas y `INSPECT`.

**Consecuencia para Cobol2Py:** si abordamos ODO, la prueba debe cubrir declaración, inicialización, límites de iteración, referencias con índice y `SEARCH`, no solo la sintaxis. Para operaciones aritméticas conviene aislar operandos, truncamiento/escala y salida en fixtures mínimos, no modificar varias familias de verbos en una sola iteración.

Fuentes inspeccionadas: [`cobj/codegen.c`](https://github.com/opensourcecobol/opensourcecobol4j/blob/develop/cobj/codegen.c) y [`CHANGELOG.md`](https://github.com/opensourcecobol/opensourcecobol4j/blob/develop/CHANGELOG.md).

### PythonBol-Translator: útil como comparación, no como oráculo de semántica

La implementación consultada preescanea nombres elementales repetidos y crea un mapa `(nombre, grupo padre) → nombre Python`; también recorre los niveles `OCCURS` para generar estructuras anidadas. Para `REDEFINES`, genera adaptadores/alias y deja un comentario TODO si no encuentra el destino original. El parser consultado extrae `OCCURS` y `OCCURS DEPENDING ON` con regex.

Esto aporta dos ideas concretas que podemos evaluar: detectar colisiones de nombres antes de generar código y conservar la ruta del grupo padre en el mapa de símbolos. Pero el propio README caracteriza el resultado como *skeleton* y sus métricas de parseo/compilación sintáctica no prueban equivalencia de stdout y return code. Un campo dinámico reducido a una cantidad fija o un destino `REDEFINES` ausente no debe considerarse resuelto por generar Python válido.

Fuentes inspeccionadas: [`mapper_codegen.py`](https://github.com/IronAdamant/PythonBol-Translator/blob/main/src/cobol_safe_translator/mapper_codegen.py), [`parser.py`](https://github.com/IronAdamant/PythonBol-Translator/blob/main/src/cobol_safe_translator/parser.py) y [README](https://github.com/IronAdamant/PythonBol-Translator/blob/main/README.md).

### CobGo y Koopa: adoptar fronteras, no asumir cobertura equivalente

El conversor AST→IR de CobGo acumula errores de conversión y devuelve un error agregado si existen; esta frontera explícita evita confundir un nodo no convertido con una traducción completa. Sin embargo, el repositorio se orienta a una ruta de modernización COBOL/DSL hacia Go, así que su IR no debe tratarse como una implementación de toda la semántica COBOL.

Koopa enfatiza formatos de fuente fixed/free/variable, gramática extensible y preprocesamiento COPY/REPLACING. Para Cobol2Py, el principio aplicable es mantener separados normalización/preprocesamiento, análisis de declaraciones y generación. No hace falta reemplazar el parser actual hasta demostrar con el corpus que esa sustitución arreglaría más casos de los que rompe.

Fuentes: [CobGo converter](https://github.com/CoreBankLang/CobGo_community/blob/main/pkg/ir/converter.go) y [Koopa README](https://github.com/krisds/koopa).

## Decisión técnica provisional tras la segunda pasada

1. **No portar código de terceros ni reemplazar el parser todavía.**
2. Antes de ampliar el cambio de referencias cualificadas, comparar los resultados externos completos y revisar ganados/perdidos del mismo SHA.
3. El siguiente candidato de arquitectura es una resolución de símbolos basada en jerarquía y ruta (nombre + ancestros + índices), con detección explícita de ambiguos/no resueltos. Debe poder probarse aislada contra los casos reales del corpus.
4. Dejar REDEFINES para una iteración separada: requiere layout/offsets y reglas de validación; no es seguro añadirlo como un parche de alias.
5. Tratar ODO como una familia transversal que afecta tamaño, referencias y control de iteración; diseñar una batería pequeña de pruebas diferenciales antes de tocarla.

No se afirma aún ninguna mejora porcentual derivada de esta investigación. El benchmark externo completo, en el mismo SHA, es el criterio para aceptar una optimización.


### GnuCOBOL: subíndices y ODO se comprueban semánticamente antes del codegen

En `cobc/typeck.c`, la resolución de referencias compara el número de subíndices suministrados con las dimensiones declaradas (`f->indexes`), rechaza accesos a campos sin `OCCURS`, y puede emitir comprobaciones de límites y de la longitud activa de una tabla `OCCURS DEPENDING ON`. La validación ODO también comprueba que el controlador sea numérico y aplica reglas sobre su posición, campos posteriores y anidamiento según el dialecto.

**Implicación concreta para los errores de Cobol2Py:** los casos en que una lista se indexa por una clave de texto o se omite una dimensión no se arreglan solo convirtiendo el índice a entero. El resolver debe saber cuántas dimensiones espera cada símbolo, qué nivel de tabla corresponde a cada subíndice y si el acceso está dentro del rango activo de ODO. Crear fixtures diferenciales para: número correcto/incorrecto de subíndices, tabla de una y varias dimensiones, índice literal y variable, y lectura/escritura dentro y fuera del rango ODO.

Fuente inspeccionada: [`cobc/typeck.c`](https://github.com/OCamlPro/gnucobol/blob/master/cobc/typeck.c), comprobación de subíndices y validación de `OCCURS DEPENDING`.


### Caso de estudio reproducible: tablas NIST de tres dimensiones

La suite de pruebas de ProLeap incluye [`NC234A.CBL`](https://github.com/uwol/proleap-cobol-parser/blob/main/src/test/resources/gov/nist/NC234A.CBL). La declaración `3-DIMENSION-TBL` contiene tres niveles de tablas anidadas `OCCURS 10 TIMES`; una segunda vista `3-DEM-TBL REDEFINES 3-DIMENSION-TBL` declara otra jerarquía de tres dimensiones. El procedimiento usa referencias como `ENTRY-3-1 (SUB-1, SUB-2, SUB-3)` y `SEARCH GRP3-ENTRY-1 VARYING IDX-3-1`.

Los fallos del corpus externo `nc2344-2-5f8e49c5ac`, `nc241a-681f02a7ce` y `nc2414-2-2f38ed7c87` son coherentes con esta familia: el Python generado falla al indexar estructuras anidadas, y la prueba de referencia contiene tablas de tres dimensiones y REDEFINES. No se debe asumir que el error sea solo una conversión de índice a entero: hay que comprobar conjuntamente la ruta jerárquica, el número/orden de subíndices y la vista de almacenamiento redefinida.

**Siguiente fixture mínimo:** reducir la estructura a una tabla con tres niveles `OCCURS`, una segunda definición `REDEFINES`, escritura y lectura en las dos vistas, y una búsqueda indexada. Comparar salida y código de retorno con GnuCOBOL. La corrección de calificadores anidados de la PR #40 no alteró esos casos del informe multilenguaje; la siguiente iteración debe aislar la interacción entre la jerarquía de tablas y REDEFINES, no repetir el mismo parche de regex.


### Experimento aplicado: vista REDEFINES sobre OCCURS de tres dimensiones

La PR [#41](https://github.com/orbitalronin94/cobol2py/pull/41) ya contiene un fixture reducido derivado de `NC234A.CBL`: escribir en `ENTRY-3(2, 1, 2)` de la tabla original y leer `ENTRY-3-1(2, 1, 2)` desde la vista `REDEFINES`. Antes del cambio, la primera lectura devolvía el texto correcto y la segunda espacios; el traductor generaba dos diccionarios independientes en vez de almacenamiento compartido.

La implementación candidata calcula el ancho de los grupos incluyendo `OCCURS`, conserva el stride de cada dimensión y enruta lecturas/escrituras indexadas de campos redefinidos por el buffer común. La nueva prueba y la suite completa pasan en Python 3.10–3.13; también ha pasado el workflow diferencial interno. El benchmark externo de primaria/holdout para este SHA sigue pendiente, por lo que todavía no se atribuye ninguna subida porcentual a esta corrección.

Límite conocido: es el subconjunto de almacenamiento DISPLAY que el backend ya soporta. No demuestra aún equivalencia para todos los usos de `REDEFINES`, datos numéricos con escala implícita, redefiniciones de longitud variable ni referencias a grupos completos sin subíndices.
