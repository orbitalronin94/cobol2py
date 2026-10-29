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
