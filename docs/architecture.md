# Arquitectura actual

## Objetivo y no objetivos

`cobol2py` es un traductor pequeño de COBOL a Python legible, implementado en un solo archivo y sin dependencias externas de Python. Su propósito principal es ayudar a inspeccionar y entender lógica COBOL. Que una salida parezca Python válida no significa que preserve toda la semántica del programa original.

El soporte es incremental: se incorporan construcciones cuando hay implementación y pruebas que las respaldan. No se debe presentar el proyecto como compilador COBOL completo ni como herramienta que certifique una migración de sistemas críticos.

## Flujo de procesamiento

La implementación actual en `cobol2py.py` sigue, de forma simplificada, estas etapas:

1. **Preprocesado** — `preprocess()` detecta o aplica el formato de fuente y normaliza las líneas útiles, conservando números de línea para diagnóstico y análisis.
2. **Modelo de datos** — `CobolVar`, `Node` y `Program` representan variables, unidades de procedimiento y el programa analizado.
3. **Variables** — `parse_variables()` interpreta las declaraciones de almacenamiento que el traductor reconoce, incluidos usos básicos de `PIC`, `VALUE` y `OCCURS`.
4. **Procedimientos** — `split_paragraph_into_units()`, `build_tree()` y `parse_procedure()` separan sentencias y construyen una estructura de control para las construcciones soportadas.
5. **Expresiones y sentencias** — funciones como `translate_expr()`, `translate_condition()` y `translate_statement()` traducen nombres, expresiones y verbos COBOL a Python.
6. **Emisión** — `emit_python()` genera el archivo Python final y el punto de entrada.

Estos pasos describen la organización actual, no una gramática COBOL formal. No se debe asumir que cualquier programa aceptado por un compilador COBOL puede analizarse correctamente aquí.

## Decisiones de implementación relevantes

- Se prioriza una implementación compacta y fácil de inspeccionar frente a una arquitectura con dependencias y un parser completo.
- La detección de formato fijo/libre existe porque el formato de fuente cambia cómo deben interpretarse columnas, comentarios y sentencias.
- Los nombres COBOL se normalizan a identificadores Python, preservando una correspondencia legible; las palabras reservadas requieren tratamiento especial.
- El almacenamiento `WORKING-STORAGE` debe seguir siendo accesible desde los párrafos que lo usan.
- La traducción de sentencias respeta los cierres explícitos reconocidos, como `END-IF`, `END-PERFORM` y `END-EVALUATE`, en las estructuras que soporta.
- Los índices de tablas COBOL son normalmente base 1; al emitir acceso a estructuras Python, hay que ajustar el índice sin cambiar la semántica visible.
- El parser reconoce `IF` estándar sin `THEN` y `ELSE`/`END-IF` como unidades estructurales, dentro de los patrones cubiertos por pruebas.
- `PERFORM n TIMES` en línea se representa como un bucle Python cuando el cuerpo pertenece al subconjunto reconocido; no implica soporte de todas las variantes de `PERFORM`.
- Las comparaciones alfanuméricas con literales aplican relleno de espacios en los casos implementados para aproximar la comparación de campos de ancho fijo COBOL.

## Errores y límites

El traductor no es un sustituto de un compilador COBOL. Las construcciones no implementadas, las cláusulas complejas y las diferencias entre dialectos pueden generar errores o traducciones que no son equivalentes. Antes de extender una regla compartida, añade un caso de regresión pequeño y una comparación diferencial cuando GnuCOBOL pueda servir de referencia.

## Cómo validar una modificación

Desde la raíz del repositorio:

```bash
python -m unittest discover -s tests -v
python benchmarks/run_benchmark.py --translator cobol2py.py
```

El benchmark requiere GnuCOBOL instalado. Las pruebas unitarias comprueban comportamientos específicos; el benchmark compara los casos versionados contra el programa COBOL compilado. Ninguna de estas comprobaciones demuestra equivalencia general.


## Diagnósticos

`collect_diagnostics()` inspecciona el AST y las referencias de copybooks para reportar construcciones no soportadas o malformadas. La CLI permite mostrar JSON estructurado y rechazar esos casos con `--strict`. El análisis es deliberadamente conservador y no sustituye a una validación semántica con GnuCOBOL.


El backend Python trata `STOP RUN` como terminación del programa: una señal interna se propaga desde cualquier párrafo llamado y se captura en el punto de entrada, evitando que el párrafo llamador continúe ejecutando sentencias. El backend Java usa `System.exit(0)` para el programa independiente generado.


El modo estricto también advierte sobre operaciones aritméticas (`ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE`, `COMPUTE`) porque la semántica completa de desbordamiento del campo receptor y `ON SIZE ERROR` todavía no está garantizada.


## Literales COBOL

La conversión de literales reconoce las comillas delimitadoras duplicadas de COBOL y serializa el valor decodificado con el escape del lenguaje destino. Los patrones de tokenización de operandos y expresiones deben mantener el literal completo como un único token. Esta regla no sustituye un lexer COBOL completo.


## Normalización de identificadores

Los nombres COBOL se normalizan de forma consistente en declaraciones, referencias cualificadas y subíndices. Si el nombre coincide con una palabra reservada de Python o Java, se antepone `cobol_` para evitar código de destino sintácticamente inválido. Esta transformación cambia el identificador generado, no el nombre del campo en el programa COBOL original.


## Normalización de condiciones

La traducción de condiciones separa los fragmentos de código de los literales COBOL. Las palabras reservadas de condición y los operadores se reescriben solo fuera de cadenas entre comillas, incluidas las comillas delimitadoras duplicadas. Esto evita alterar literales como `"NOT"` o `"AND"` al normalizar condiciones.

## Agente de modernización a nivel de repositorio

El módulo `cobol2py_agent.py` añade una capa separada del traductor: inventaría programas COBOL, copybooks, ficheros JCL y SQL; extrae referencias de texto; resuelve destinos locales por nombre cuando puede; y produce un plan Markdown/JSON con referencias no resueltas y construcciones que requieren revisión. Solo usa la biblioteca estándar y no ejecuta ni modifica el sistema analizado.

Este bloque **no reemplaza** el parser ni el backend determinista. Es una primera pieza de análisis de cartera y planificación, con heurísticas explícitas. La arquitectura objetivo para modernización de sistemas completos es:

1. **Analizador de repositorio**: inventario y grafo provisional de dependencias.
2. **Planificador**: agrupa el trabajo en pilotos y oleadas, con criterios de salida verificables.
3. **Adaptador del traductor**: utiliza el motor actual y sus diagnósticos.
4. **Verificador**: compila el destino y compara el comportamiento con una referencia COBOL, incluyendo archivos y otros efectos observables cuando puedan reproducirse.
5. **Analizador de divergencias**: identifica qué caso, entrada, variable o dependencia explica una diferencia.
6. **Bucle de reparación**: en una fase futura, propone cambios aislados, ejecuta de nuevo las pruebas y deja un diff revisable.

Un LLM futuro podrá explicar hallazgos y proponer cambios acotados, pero no debe ser la fuente de verdad de la semántica. La aceptación de una migración debe depender de evidencia de compilación y pruebas diferenciales, no de la plausibilidad del código generado.

### Ejecutar y validar el planificador

```bash
python cobol2py_agent.py /ruta/al/sistema --out migration-plan.md --json-out migration-plan.json
python -m unittest tests.test_modernize_agent -v
```

El JSON versionado contiene `summary`, `files`, `dependencies`, `unresolved_references`, `recommended_sequence`, `review_first` y `limitations`. La resolución por nombre no es un enlazador: puede haber referencias dinámicas, destinos externos, ambigüedad y falsos positivos. Consulta [repo-modernization-agent.md](repo-modernization-agent.md) para el uso, el esquema y las limitaciones.

La futura automatización debe operar en un workspace aislado, producir diffs inspeccionables y pedir revisión ante incertidumbre. No debe tener acceso implícito a credenciales de producción ni aceptar cambios sin ejecutar las verificaciones acordadas.
