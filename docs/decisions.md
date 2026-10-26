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
