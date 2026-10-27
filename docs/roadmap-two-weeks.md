# Roadmap de modernización de dos semanas

## Continuidad del roadmap: fase posterior al piloto

El calendario de diez días describe la primera iteración y ya se han entregado sus principales artefactos. No debe interpretarse como el límite del proyecto. Esta sección amplía el plan con el trabajo que sigue; los elementos pendientes no se consideran completados hasta aportar pruebas y evidencia de CI.

### Fase A — Precisión del inventario estático

- [ ] Clasificar los 36 archivos de `samples` que reportaron diagnósticos en la ejecución registrada del piloto: diagnóstico esperado, falso positivo, limitación real o posible defecto.
- [x] Separar referencias `CALL` literales de llamadas dinámicas mediante identificadores, sin inventar destinos estáticos para llamadas cuyo valor solo se conoce en ejecución. Implementado en el agente Python y la demo web; los destinos dinámicos quedan en `dynamic_calls` y no se cuentan como referencias literales sin resolver. Hay pruebas de regresión de unidad y de navegador.
- [ ] Añadir fixtures para cada patrón reproducible encontrado durante la clasificación y verificar que comentarios y literales no generan dependencias falsas.
- [ ] Documentar métricas de precisión con denominadores y ejemplos revisables; no usar solo el número bruto de advertencias como métrica de calidad.

**Criterio de salida:** cada familia frecuente de diagnóstico tiene una explicación, pruebas de regresión y un comportamiento documentado; las referencias desconocidas permanecen explícitamente sin resolver.

### Fase B — Validación del piloto y evidencia diferencial

- [ ] Versionar el esquema de los informes del piloto e incluir versión del traductor, estado sintáctico, diagnósticos y estado semántico con valores no ambiguos.
- [ ] Añadir enlaces entre fuentes traducidas y fixtures diferenciales aplicables, cuando exista correspondencia demostrable.
- [ ] Diseñar una integración opcional de validación diferencial que compare salida y código de retorno con GnuCOBOL en un entorno controlado; no ejecutar código generado en el modo de inventario.
- [ ] Diferenciar claramente `no evaluado`, `comparado y coincidente`, `discrepancia` y `no aplicable`; no inferir equivalencia por compilación.

**Criterio de salida:** un informe puede indicar exactamente qué se verificó, qué no se verificó y cómo reproducir cada discrepancia.

### Fase C — Experiencia del agente y operación

- [ ] Añadir filtros por tipo de hallazgo, relación, nivel de confianza y ruta tanto a los informes como a la interfaz web cuando los datos disponibles lo permitan.
- [ ] Mejorar navegación entre dependencias, candidatos ambiguos y archivos de origen, manteniendo el procesamiento local en la demo HTML.
- [ ] Probar informes con nombres de archivo y contenido que incluyan Unicode, rutas anidadas, entradas vacías y grandes cantidades de archivos.
- [ ] Documentar límites de escala, formatos reconocidos, reglas de exclusión y pasos de revisión humana.

**Criterio de salida:** las personas que revisan el inventario pueden priorizar y reproducir hallazgos sin confundir análisis heurístico con verificación de comportamiento.

### Fase D — Semántica del traductor

- [ ] Priorizar discrepancias por impacto en datos, control de flujo y E/S; cada cambio semántico debe incluir un caso mínimo.
- [ ] Revisar límites conocidos de aritmética `PIC`, signos, escalas decimales, redondeo y `ON SIZE ERROR` antes de ampliar las afirmaciones de compatibilidad.
- [ ] Mantener sincronizado `web/index.html` con `cobol2py.py` y ejecutar el test de sincronización en CI para cada cambio del traductor.
- [ ] Ampliar el benchmark solo con casos reproducibles y describir con precisión qué dimensiones se comparan.

**Criterio de salida:** las mejoras tienen regresiones reproducibles y el README de compatibilidad no promete más de lo que miden los tests.

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
| v0.6 — Piloto integrado | Inventario → traducción del subconjunto → comprobación sintáctica por archivo | No ejecuta código generado ni certifica comportamiento |
| v0.7 — Acceso y cobertura web | Demo standalone del traductor y demo local del agente; prueba de navegador | La UI del agente sigue siendo heurística y trabaja con los archivos que el usuario selecciona |
| v0.8 — Evidencia auditable | Esquema de informe versionado, clasificación de diagnósticos, enlace exacto a fixtures candidatas, detalle por archivo y artefacto de CI | La clasificación automática prioriza revisión; no sustituye la decisión de un especialista ni convierte una fixture enlazada en prueba ejecutada |

### Definición de terminado para el hito 0.8

- [x] Los diagnósticos del piloto tienen una categoría explícita y se cuentan por código y categoría.
- [x] El informe incluye detalle por archivo, línea, código y mensaje, además del estado sintáctico.
- [x] El esquema identifica la versión del traductor y separa not-evaluated de una validación semántica real.
- [x] Las fixtures diferenciales solo se enlazan cuando la ruta de origen coincide exactamente con la del manifiesto; el enlace no afirma que se hayan ejecutado.
- [x] CI valida el contrato del informe y publica los reportes del piloto como artefacto descargable.
- [x] Las llamadas CALL literales y dinámicas se distinguen en el agente CLI y en la demo web, con pruebas unitarias y de navegador.
- [ ] La clasificación automática de los 36 archivos con diagnósticos debe revisarse humanamente antes de usarla para decidir una migración real. El reporte generado por CI es el backlog verificable para esa revisión; los avisos no se descartan como falsos positivos sin evidencia.
- [ ] La equivalencia semántica sigue siendo una comprobación por caso con GnuCOBOL y entradas representativas, no una propiedad global del piloto.

### Siguiente ciclo después de 0.8

1. **0.8.x — Cierre de revisión:** adjudicar cada diagnóstico de samples como limitación confirmada, falso positivo reproducible, posible defecto o dependencia externa; convertir cada falso positivo/defecto en regresión.
2. **0.9 — Validación diferencial por módulo:** ejecutar solo fixtures identificadas y aprobadas explícitamente; guardar stdout, código de retorno, versión de GnuCOBOL y resultado reproducible. Nunca ejecutar traducciones arbitrarias durante el inventario estático.
3. **0.10 — Navegación y filtros:** filtros de hallazgos por código/categoría/ruta, navegación entre aristas y fuentes, y pruebas con Unicode, rutas profundas y repositorios grandes.
4. **1.0 — Criterios de adopción:** contratos de informe estables, documentación de dialectos/entornos soportados, matriz de compatibilidad revisada y CI obligatoria verde. No depende de alcanzar un porcentaje universal de COBOL soportado.

El criterio de avance no es el número de versión: cada hito exige cambios integrados, regresiones, evidencia de CI y límites documentados. Un hallazgo no se marca como falso positivo solo porque la salida Python compile.
