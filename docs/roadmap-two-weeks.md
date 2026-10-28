# Roadmap de modernización de dos semanas

## Objetivo de producto: v1.0 con ≥75 % de equivalencia diferencial

Este objetivo reemplaza cualquier interpretación de «roadmap terminado» basada únicamente en cerrar tareas internas. La versión 1.0 no se considera lista hasta que el benchmark externo alcance y sostenga el umbral indicado.

### Línea base, meta y definición

- **Línea base inicial:** 53/500 programas (10,60 %) con stdout y código de retorno exactamente iguales a GnuCOBOL.
- **Última medición externa confirmada:** 130/500 (26,00 %) en la muestra primaria y 147/500 (29,40 %) en el holdout disjunto, ambos en el workflow [40687084304](https://github.com/orbitalronin94/cobol2py/actions/runs/40687084304), commit `7d98183c`; las dos muestras de 500 están completas. Frente a la línea base inicial de 53/500 (10,60 %), son +77 y +94 coincidencias exactas. Los tests de CI del mismo commit pasaron en [40687084278](https://github.com/orbitalronin94/cobol2py/actions/runs/40687084278). El umbral del 75 % aún no se alcanza.
- **Meta mínima:** 375/500 (75,00 %) en la muestra externa primaria de 500 programas.
- **Validación anti-sobreajuste:** al menos 75 % en una segunda muestra disjunta de 500 programas, seleccionada con la misma metodología y mantenida separada de la iteración de correcciones.
- **Qué cuenta como éxito:** el traductor termina correctamente, el Python generado compila y se ejecuta, y coinciden exactamente stdout y código de retorno. Un archivo traducido, una salida sintácticamente válida o un workflow que termina con éxito no equivalen a una coincidencia diferencial.
- **Denominador:** solo fuentes únicas que compilan y terminan bajo GnuCOBOL entran en la muestra probada. Los fallos de compilación de referencia y los timeouts de referencia se informan por separado.
- **Alcance:** la cifra mide estas muestras ejecutables y estas dimensiones observables; no demuestra equivalencia de I/O externo, archivos, bases de datos, transacciones, interacciones ni todos los dialectos COBOL.

### Fases obligatorias hacia v1.0

| Fase | Trabajo | Criterio de salida |
|---|---|---|
| 0. Medición fiable | Corregir la publicación de informes, comprobar el checksum del dataset, conservar JSON/Markdown y enlazar el commit medido | El benchmark termina con un informe recuperable incluso si la tasa es baja; errores de infraestructura quedan diferenciados de resultados funcionales |
| 1. Diagnóstico de fallos | Clasificar cada caso por error de traducción, sintaxis Python, excepción/timeout, stdout diferente o código de retorno diferente; agrupar por causa raíz | Informe reproducible con conteos, ejemplos por identificador/hash y familias priorizadas |
| 2. Correcciones de alto impacto | Arreglar primero las familias frecuentes y reutilizables; incorporar una prueba mínima por defecto corregido | Tests de regresión y comparación GnuCOBOL para cada corrección semántica relevante |
| 3. Iteración cuantificada | Ejecutar los mismos 500 casos tras cada grupo de cambios y mantener un registro de evolución | Mejora confirmada sin cambiar el denominador, ocultar fallos ni contar exclusiones como éxitos |
| 4. Validación disjunta | Congelar el candidato y probar una muestra distinta de 500 programas; no usar sus resultados para ajustar el candidato evaluado | ≥75 % en la muestra primaria y en la muestra disjunta; si no, volver a la fase 1 y repetir |
| 5. Candidato v1.0 | Ejecutar CI completo, revisar regresiones internas, actualizar compatibilidad y publicar los dos informes | Todos los jobs obligatorios verdes, ambos umbrales alcanzados, limitaciones visibles y revisión final de release |

### Registro de métricas

No registrar como mejora un resultado cuyo denominador, selección, versión de GnuCOBOL o criterio de coincidencia haya cambiado sin anotarlo. Para cada ejecución se conservarán el SHA del commit, checksum del corpus, número de fuentes descubiertas y únicas, descartes de compilación/ejecución de referencia, identificadores de los casos probados, coincidencias exactas y fallos por categoría. La tasa debe calcularse como `exact_matches / tested`.

### Estado actual del objetivo

- [x] Línea base inicial de 500 casos: 53/500 (10,60 %).
- [x] Corrección del traductor para evitar un bloque `try` Python vacío cuando el párrafo de entrada solo contiene comentarios.
- [x] Prueba de regresión para el caso anterior y sincronización del traductor embebido en la demo web.
- [x] CI unitario verde en Python 3.10, 3.11, 3.12 y 3.13 en la ejecución confirmada tras sincronizar la demo.
- [x] Reparar la escritura del informe del benchmark externo: el contenedor no privilegiado usa UID 65534 y el directorio dedicado de artefactos permite escritura.
- [x] Obtener los informes externos completos para ambas muestras: 111/500 (22,20 %) en primaria y 118/500 (23,60 %) en holdout, en `a9daee71`; artefactos publicados.
- [x] Clasificar el primer resultado: 153 errores Python de sintaxis genéricos, 93 errores por ceros iniciales en literales enteros, 39 errores sintácticos con sugerencia de coma y 130 diferencias de stdout/código de retorno, además de fallos residuales.
- [x] Añadir normalización de literales numéricos con ceros iniciales en la traducción Python y una regresión unitaria; sincronizar el código embebido de la demo web.
- [x] Verificar CI del soporte de condiciones de nivel 88, comportamiento EOF de ACCEPT y traducción de comparaciones compuestas; la revisión `e3284a09` tiene tests y benchmark diferencial verdes.
- [ ] Confirmar el benchmark externo del candidato `e3284a09`; no atribuir mejora hasta que ambas muestras terminen.
- [ ] Subir desde 22,20 % (primaria) y 23,60 % (holdout) hasta ≥75 % con evidencia en ambos benchmarks.
- [ ] Validar ≥75 % en la muestra disjunta de 500 casos.
- [ ] Cumplir todos los criterios de salida de v1.0.


## Continuidad del roadmap: fase posterior al piloto

El calendario de diez días describe la primera iteración y ya se han entregado sus principales artefactos. No debe interpretarse como el límite del proyecto. Esta sección amplía el plan con el trabajo que sigue; los elementos pendientes no se consideran completados hasta aportar pruebas y evidencia de CI.

### Fase A — Precisión del inventario estático

- [x] Validar en CI la puntuación heurística de complejidad del agente: señales, pesos, nivel LOW/MEDIUM/HIGH y exposición de las señales en el informe. El score prioriza revisión; no debe presentarse como estimación de esfuerzo ni prueba de alcance en runtime.

- [x] Generar un triage reproducible por archivo para las fuentes con diagnósticos: categoría primaria, categorías presentes, códigos y líneas, y estado de revisión humana pendiente. El informe se publica como artefacto CI.
- [ ] Adjudicar manualmente los 35 archivos que aún tienen avisos. Se corrigió un falso positivo de la línea base (IF inline truncado por detección de formato); el detalle está en docs/pilot-diagnostics-baseline.md.
- [x] Separar referencias `CALL` literales de llamadas dinámicas mediante identificadores, sin inventar destinos estáticos para llamadas cuyo valor solo se conoce en ejecución. Implementado en el agente Python y la demo web; los destinos dinámicos quedan en `dynamic_calls` y no se cuentan como referencias literales sin resolver. Hay pruebas de regresión de unidad y de navegador.
- [x] Añadir regresiones para comentarios, formato fijo, llamadas dinámicas y palabras clave de dependencias dentro de literales; el inventario enmascara el contenido literal antes de extraer relaciones.
- [x] Publicar denominadores y conteos por archivo, categoría y código diagnóstico, junto con el detalle de cada aviso.
- [ ] Medir precisión/recall real solo después de etiquetar manualmente una muestra; los conteos automáticos no son una métrica de exactitud.

**Criterio de salida:** cada familia frecuente de diagnóstico tiene una explicación, pruebas de regresión y un comportamiento documentado; las referencias desconocidas permanecen explícitamente sin resolver.

### Fase B — Validación del piloto y evidencia diferencial

- [x] Versionar el esquema del informe como v2 e incluir versión del traductor, estado sintáctico, triage, diagnósticos y estado semántico explícito.
- [x] Enlazar fuentes con fixtures diferenciales mediante coincidencia exacta de ruta; el informe advierte que el enlace no implica ejecución.
- [x] Añadir el modo opt-in `--differential`: ejecuta solo fixtures exactas del manifiesto y compara stdout/código de retorno con GnuCOBOL; el modo por defecto nunca ejecuta la traducción.
- [x] Diferenciar `not-evaluated`, `matched`, `discrepancy`, `reference-error` y `not-applicable`; la sintaxis por sí sola no cambia el estado semántico.

**Criterio de salida:** un informe puede indicar exactamente qué se verificó, qué no se verificó y cómo reproducir cada discrepancia.

### Fase C — Experiencia del agente y operación

- [x] Añadir filtro de texto en la demo web para buscar por ruta, símbolo, tipo o característica en todas las tablas. El CLI conserva el informe completo y filtrable por herramientas externas.
- [ ] Mejorar navegación entre dependencias, candidatos ambiguos y archivos de origen, manteniendo el procesamiento local en la demo HTML.
- [x] Añadir regresiones para rutas y nombres Unicode, árboles vacíos, rutas anidadas y 200 fuentes; el smoke de navegador también carga un nombre de archivo Unicode.
- [x] Documentar formatos reconocidos, directorios excluidos, límites heurísticos y la necesidad de revisión humana. Los límites de escala se cubren con una prueba de 200 fuentes, no con una garantía de rendimiento universal.

**Criterio de salida:** las personas que revisan el inventario pueden priorizar y reproducir hallazgos sin confundir análisis heurístico con verificación de comportamiento.

### Fase D — Semántica del traductor

- [x] Priorizar discrepancias diferenciales por pistas de riesgo derivadas de las features (high/medium/low) y ordenar el informe por prioridad. Es una heurística para orientar la revisión, no una evaluación de severidad definitiva; cada corrección semántica sigue necesitando un caso mínimo.
- [x] Revisar y documentar límites de aritmética `PIC`, signo, escala, redondeo y `ON SIZE ERROR`; la implementación completa de estas reglas permanece fuera del alcance validado y no se declara soportada.
- [x] Mantener sincronizado `web/index.html` con `cobol2py.py` mediante test de igualdad del bloque embebido en CI.
- [x] Mantener el benchmark basado en fixtures reproducibles; documentar que compara stdout y código de retorno, no todos los efectos externos.

**Criterio de salida:** las mejoras tienen regresiones reproducibles y el README de compatibilidad no promete más de lo que miden los tests.

### Fase E — Semántica de flujo dinámico y almacenamiento compartido (v0.8.x)

Este bloque se añade a la línea de trabajo v0.8: cerrar fallos que pueden producir Python sintácticamente válido pero con comportamiento COBOL distinto. La fixture de referencia es `LABERINTO-COBOL`, que combina `ALTER`, `GO TO ... DEPENDING ON`, `REDEFINES`, saltos entre párrafos y datos numéricos compartidos.

**Estado de implementación en `main` (27-10-2026):** existe un dispatcher de párrafos para `GO TO`, destinos mutables para `ALTER`, selección ordinal para `GO TO ... DEPENDING ON` y un buffer compartido para overlays simples con `PIC X/A` y numéricos enteros sin signo. Las fixtures `samples/control_flow_redefines.cbl` y `samples/laberinto_cobol.cbl` pasan la comparación diferencial con GnuCOBOL; el corpus total actual es 104/104. La suite pasa en Python 3.10–3.13 y verifica la sincronización de la demo HTML. Los overlays con signo, escala implícita, packed decimal, arrays o layouts complejos siguen fuera de la validación cerrada y deben conservar diagnósticos explícitos.

- [x] **Caracterizar `LABERINTO-COBOL` con GnuCOBOL:** `samples/laberinto_cobol.cbl` está en el manifiesto diferencial y coincide en stdout/código de retorno; el resultado final medido es `222240` y el mensaje inicial aparece dos veces.
- [x] **Implementación inicial de `ALTER`:** modelar el destino del `GO TO` alterable como estado mutable consultado en tiempo de ejecución. Cada `ALTER` posterior debe reemplazar el destino anterior; no convertir la sentencia en comentario ni congelar el destino durante la traducción.
- [x] **Implementación inicial de `GO TO ... DEPENDING ON`:** preservar la selección ordinal COBOL basada en 1. Añadir pruebas para cada destino válido y para selector fuera de rango; en este ejemplo, si no se toma ninguna rama, debe respetarse la sentencia siguiente del párrafo.
- [x] **Implementación y regresión de `REDEFINES` simple:** describir offsets, longitudes y vistas del almacenamiento base; leer/escribir una vista se refleja en las demás. No emitir diccionarios vacíos independientes para campos que se superponen.
- [x] **Preservar el flujo de párrafos en el subconjunto probado:** el dispatcher representa saltos entre párrafos sin introducir retornos de función artificiales; la fixture completa `LABERINTO-COBOL` valida el ciclo, los saltos y las transferencias dinámicas.
- [x] **Pruebas unitarias mínimas:** destinos `ALTER` antes y después de la mutación, selección de cada ordinal, rango inválido, lecturas `REDEFINES` antes/después de modificar el búfer y layouts válidos/invalidos para PIC numérico.
- [x] **Validar regresión integrada:** `samples/control_flow_redefines.cbl` y `samples/laberinto_cobol.cbl` pasan en el job diferencial; stdout y código de retorno coinciden con GnuCOBOL.
- [ ] **Exponer límites sin degradación silenciosa:** hasta que cada construcción esté implementada y probada, emitir diagnóstico explícito y clasificar la traducción como incompleta; no reemplazar instrucciones por comentarios sin que el informe lo refleje.
- [ ] **Sincronizar las interfaces:** mantener `web/index.html` alineado con `cobol2py.py` y añadir el contrato del diagnóstico en las pruebas de la demo.

**Criterio de salida:** las pruebas específicas de cada construcción y la fixture integrada coinciden con GnuCOBOL en stdout/código de retorno; los casos no soportados quedan explícitamente diagnosticados. El resultado solo certifica los casos medidos, no compatibilidad general con `ALTER`, `REDEFINES` ni todos los dialectos COBOL.

### Cadencia de revisión

Al cerrar cada bloque, actualizar el estado de esta lista, el README, las notas de versión cuando proceda y la evidencia de CI. Si el análisis revela una limitación que no se puede resolver con seguridad, registrar la limitación y el diagnóstico en lugar de ocultarlos.

## Objetivo

Mejorar la fiabilidad verificable de `cobol2py` y la utilidad de su agente de inventario sin presentar el subconjunto implementado como compatibilidad COBOL completa. El plan se ejecuta en diez días laborables; se puede paralelizar por responsabilidad, pero cada cambio entra integrado y probado.

## Reglas de ejecución

1. Mantener `main` en estado integrado: cambios pequeños, pruebas y documentación en el mismo ciclo.
2. No aceptar una traducción solo porque el Python/Java generado compile; comparar comportamiento cuando exista una referencia ejecutable.
3. Todo caso no soportado conocido debe producir un diagnóstico visible o quedar documentado como riesgo.
4. Las métricas deben declarar el corpus, entorno y dimensiones comparadas.
5. La demo HTML debe mantener el traductor embebido sincronizado con `cobol2py.py`.
6. Si un job falla, corregir la causa y verificar una nueva ejecución antes de declarar la fase terminada.

## Calendario

| Día | Foco | Entregable verificable |
|---|---|---|
| 1 | Línea base, contratos y backlog | Inventario de workflows, áreas soportadas/parciales/no soportadas y defectos priorizados |
| 2 | Semántica de datos y control de flujo | Casos mínimos de regresión para los defectos de mayor impacto; diagnósticos conservadores |
| 3 | Copybooks y preprocesado | Pruebas para expansión anidada, rutas, ciclos, faltantes, formatos y reemplazos admitidos |
| 4 | Verificación diferencial | Corpus ejecutable contra GnuCOBOL y reporte de discrepancias reproducible |
| 5 | Integración y estabilidad | CI verde, demo sincronizada y limitaciones documentadas |
| 6 | Inventario multiarchivo | Dependencias y referencias sin resolver con clasificación de hallazgos |
| 7 | Plan de modernización | Informe Markdown/JSON con pasos, riesgos y límites claros |
| 8 | CLI y demo | Mensajes de error y diagnósticos más accionables; instrucciones reproducibles |
| 9 | Prueba extremo a extremo | Ejemplo desde inventario hasta traducción y validación diferencial |
| 10 | Cierre | Revisión completa de CI, benchmark, documentación y notas de versión |

## Criterios de aceptación

- Todos los jobs obligatorios pasan en el commit candidato final.
- Cada corrección semántica relevante incluye una prueba de regresión.
- Cuando sea técnicamente viable, las correcciones incluyen comparación con GnuCOBOL.
- `--strict` y `--diagnostics-json` exponen limitaciones detectadas de forma consistente.
- La demo standalone y el traductor de línea de comandos usan el mismo código fuente embebido.
- El agente distingue hallazgos estáticos de pruebas de comportamiento y advierte de la ambigüedad de la resolución por nombre.
- README, compatibilidad, arquitectura y decisiones describen el comportamiento real.

## Fuera de alcance

No se promete compatibilidad completa con todos los dialectos, traducción automática de cualquier sistema, equivalencia de integraciones externas ni migración de producción sin revisión. La cobertura se expresa por construcciones y casos medidos, no por un porcentaje universal de COBOL soportado.

## Registro de progreso

- [x] Corregir la divergencia entre `web/index.html` y `cobol2py.py` y ampliar las pruebas de `COPY ... REPLACING`.
- [x] Registrar una línea base actualizada de workflows y clasificar el primer defecto de CI.
- [x] Mejorar el análisis estático para reducir dependencias falsas procedentes de comentarios.
- [x] Marcar referencias con varios destinos candidatos en el informe JSON y Markdown.
- [x] Añadir un caso diferencial COBOL/GnuCOBOL para `COPY ... REPLACING` básico.
- [x] Añadir un caso diferencial de `COPY ... REPLACING` con dos parejas (101/101 casos coinciden en el commit `9364ba6`).
- [x] Añadir una fixture diferencial para overflow de `PIC 99` en `ADD`, `COMPUTE` y `MULTIPLY`; validar el resultado en GnuCOBOL.
- [x] Ampliar el corpus diferencial a 102 casos: `arithmetic-receiving-pic` verifica el ajuste a `PIC 99` en `ADD`, `COMPUTE`, `MULTIPLY`, `SUBTRACT` y `DIVIDE`.
- [x] Mejorar el inventario con filtrado de comentarios y referencias ambiguas.
- [x] Integrar inventario → traducción → comprobación de sintaxis con informe auditable.
- [x] Ejecutar y revisar CI y benchmark del commit `4280bff`: suite completa verde en [GitHub Actions](https://github.com/orbitalronin94/cobol2py/actions/runs/40496456454) y benchmark 102/102 en [el workflow diferencial](https://github.com/orbitalronin94/cobol2py/actions/runs/40496463428); la demo HTML coincide exactamente con `cobol2py.py`. Los commits posteriores solo ajustan documentación.
- [x] Preparar notas de candidato `0.1.0-rc1` con alcance, evidencia de pruebas y limitaciones.
- [x] Conectar inventario, traducción del subconjunto y comprobación sintáctica en `tools/modernize_pilot.py`; el informe separa sintaxis de equivalencia semántica.
- [x] Ejecutar el piloto sobre `samples`: 108/108 fuentes traducidas, 0 errores de sintaxis, 0 errores de traducción y 36 fuentes con diagnósticos para revisión.

Este registro es deliberadamente conservador: una tarea solo se marca como terminada cuando hay evidencia comprobable en el repositorio o en CI.

- [x] Añadir una segunda interfaz HTML independiente para el agente: selección local de archivos, inventario resumido, referencias sin resolver/ambiguas y exportación Markdown/JSON. Añadir pruebas de contrato y documentar que el análisis del navegador es heurístico y no sustituye al CLI Python. El smoke de Playwright comprueba carga de archivos, detección de referencia ausente y exportación JSON.

## Hitos de madurez ampliados: v0.1 → v0.8

Esta escala resume entregables acumulados del proyecto para ordenar el roadmap. **No afirma que existan tags o publicaciones oficiales con cada número**; la versión del traductor sigue siendo la que declara cobol2py.py. El hito 0.8 describe madurez del flujo de ingeniería, no compatibilidad general con COBOL.

| Hito | Entregable que queda como base | Evidencia / límite |
|---|---|---|
| v0.1 — Traductor autónomo | CLI de un archivo, salida Python y pruebas unitarias iniciales | La sintaxis generada no garantiza equivalencia |
| v0.2 — Diagnósticos explícitos | Modo estricto, diagnósticos JSON y advertencias de construcciones parciales | Solo se detectan las formas cubiertas por las heurísticas actuales |
| v0.3 — Verificación diferencial | Corpus versionado comparado con GnuCOBOL | 102 casos medidos en la línea base documentada; la puntuación solo describe ese corpus |
| v0.4 — Datos y preprocesado | Mejoras acotadas de tamaño PIC y COPY REPLACING, con regresiones | No cubre toda la semántica de escala, signo, redondeo ni pseudo-texto |
| v0.5 — Inventario de cartera | Agente multiarchivo, dependencias, referencias ambiguas y destinos dinámicos | Análisis estático por nombres, no enlazado completo |
| v0.6 — Piloto integrado | Inventario → traducción del subconjunto → comprobación sintáctica por archivo | Por defecto no ejecuta código generado; el modo diferencial explícito solo ejecuta fixtures exactas y no certifica comportamiento global |
| v0.7 — Acceso y cobertura web | Demo standalone del traductor y demo local del agente; prueba de navegador | La UI del agente sigue siendo heurística y trabaja con los archivos que el usuario selecciona |
| v0.8 — Evidencia auditable | Esquema de informe versionado, clasificación de diagnósticos, enlace exacto a fixtures candidatas, detalle por archivo y artefacto de CI | La clasificación automática prioriza revisión; no sustituye la decisión de un especialista ni convierte una fixture enlazada en prueba ejecutada |

### Definición de terminado para el hito 0.8

- [x] Los diagnósticos del piloto tienen una categoría explícita y se cuentan por código y categoría.
- [x] El informe incluye detalle por archivo, línea, código y mensaje, además del estado sintáctico.
- [x] El esquema identifica la versión del traductor y separa not-evaluated de una validación semántica real.
- [x] Las fixtures diferenciales solo se enlazan cuando la ruta de origen coincide exactamente con la del manifiesto; el enlace no afirma que se hayan ejecutado.
- [x] CI valida el contrato del informe y publica los reportes del piloto como artefacto descargable.
- [x] Las llamadas CALL literales y dinámicas se distinguen en el agente CLI y en la demo web, con pruebas unitarias y de navegador.
- [ ] Revisar humanamente los 35 archivos que siguen con avisos conocidos de aritmética/PIC. Se corrigió un falso positivo de la línea base de 36; el [triage por fuente](pilot-diagnostics-baseline.md) documenta los restantes. No usar la clasificación automática como autorización de migración.
- [x] La equivalencia se informa por caso y de forma opt-in: el corpus actual de 104/104 fixtures coincide en stdout/código de retorno. Esto no equivale a una garantía global ni cubre todas las entradas o efectos externos.

### Trabajo prioritario de cierre v0.8.x

Antes de ampliar el alcance a más verbos, priorizar estas brechas semánticas con una fixture end-to-end:

1. `ALTER`: destino de salto mutable en ejecución, con una prueba que demuestre que un segundo ALTER sustituye al primero.
2. `GO TO ... DEPENDING ON`: selección 1-based, pruebas de todos los ordinales y comportamiento fuera de rango.
3. `REDEFINES`: almacenamiento compartido, offsets/longitudes verificables y coherencia entre vistas después de una escritura.
4. Flujo de párrafos: saltos y ciclos sin retornos artificiales de llamadas Python.
5. Evidencia diferencial: LABERINTO-COBOL frente a GnuCOBOL, incluyendo stdout y código de retorno, con versión/flags del compilador registrados.

La salida de referencia debe obtenerse ejecutando la fuente COBOL con el compilador de referencia; no asumir que una traducción manual representa por sí sola la semántica del dialecto. El valor final del acumulador que se espera del ejemplo es 222240 y el mensaje inicial aparece dos veces, pero estos valores deben quedar confirmados por la fixture diferencial antes de considerarlos baseline oficial.

### Siguiente ciclo después de 0.8

1. **0.8.x — Cierre de revisión:** adjudicar cada diagnóstico de samples como limitación confirmada, falso positivo reproducible, posible defecto o dependencia externa; convertir cada falso positivo/defecto en regresión.
2. **0.9 — Validación diferencial por módulo:** ejecutar solo fixtures identificadas y aprobadas explícitamente; guardar stdout, código de retorno, versión de GnuCOBOL y resultado reproducible. Nunca ejecutar traducciones arbitrarias durante el inventario estático.
3. **0.10 — Navegación avanzada:** filtros por relación y nivel de confianza, navegación entre aristas y fuentes, y pruebas con corpus mayores que 200 fuentes.
4. **1.0 — Criterios de adopción:** contratos de informe estables, documentación de dialectos/entornos soportados, matriz de compatibilidad revisada y CI obligatoria verde. No depende de alcanzar un porcentaje universal de COBOL soportado.

El criterio de avance no es el número de versión: cada hito exige cambios integrados, regresiones, evidencia de CI y límites documentados. Un hallazgo no se marca como falso positivo solo porque la salida Python compile.
