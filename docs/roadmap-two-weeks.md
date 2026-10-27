# Roadmap de modernización de dos semanas

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
- [ ] Ampliar las pruebas diferenciales en otras áreas priorizadas.
- [x] Mejorar el inventario con filtrado de comentarios y referencias ambiguas; el flujo extremo a extremo sigue pendiente.
- [ ] Ejecutar y revisar CI y benchmark del commit actual; confirmar la sincronización de la demo HTML.
- [ ] Completar la integración extremo a extremo del agente con traducción y validación.

Este registro es deliberadamente conservador: una tarea solo se marca como terminada cuando hay evidencia comprobable en el repositorio o en CI.
