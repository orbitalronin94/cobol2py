# Documentación de ingeniería

Esta carpeta documenta el diseño actual, las decisiones técnicas, el alcance semántico y el proceso para validar cambios de `cobol2py`. El único roadmap de producto vigente hacia v1.0 está en el README raíz; los documentos de hitos anteriores se conservan solo como registro histórico.

## Documentos

- [Arquitectura](architecture.md): flujo de traducción, estructuras internas, límites y arquitectura del agente de repositorio.
- [Agente de modernización](repo-modernization-agent.md): uso del inventario multiarchivo, esquema de informes y plan de migración.
- [Interfaz web del agente](repo-modernization-agent.md#interfaz-web): demo estática `web/agent.html`, exportación de informes y límites del análisis.
- [Registro de decisiones](decisions.md): decisiones tomadas, motivación, consecuencias y estado.
- [Compatibilidad COBOL](compatibility.md): comportamientos implementados, verificación y limitaciones conocidas.
- [Proceso de cambios](change-process.md): cómo proponer, medir y documentar mejoras.
- [Plan técnico del benchmark externo](EXTERNAL_BENCHMARK_FAILURE_ANALYSIS.md): medición de referencia, distribución de fallos y prioridades para recuperar casos sin alterar la métrica.
- [Notas de versión 0.1.0-rc1](release-notes-0.1.0-rc1.md): alcance, resultados medidos y limitaciones del candidato.
- [Notas de hito 0.8 (borrador de ingeniería)](release-notes-0.8.0.md): esquema de informe v2, clasificación de diagnósticos, artefacto de CI y límites del hito; no representa una publicación etiquetada.
- [Triage de diagnósticos de samples](pilot-diagnostics-baseline.md): clasificación por fuente de los 35 archivos que mantienen avisos en el piloto, con el falso positivo corregido y las limitaciones pendientes.

## Principio de mantenimiento

La documentación describe el comportamiento comprobable del código actual. Una intención de diseño no equivale a una garantía de compatibilidad. Si el código, las pruebas y los documentos discrepan, hay que resolver la discrepancia y actualizar las tres piezas; no asumir que la documentación prevalece automáticamente.

