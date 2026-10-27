# Documentación de ingeniería

Esta carpeta documenta el diseño actual, las decisiones técnicas, el alcance semántico y el proceso para validar cambios de `cobol2py`.

## Documentos

- [Arquitectura](architecture.md): flujo de traducción, estructuras internas, límites y arquitectura del agente de repositorio.
- [Agente de modernización](repo-modernization-agent.md): uso del inventario multiarchivo, esquema de informes y plan de migración.
- [Registro de decisiones](decisions.md): decisiones tomadas, motivación, consecuencias y estado.
- [Compatibilidad COBOL](compatibility.md): comportamientos implementados, verificación y limitaciones conocidas.
- [Proceso de cambios](change-process.md): cómo proponer, medir y documentar mejoras.
- [Roadmap de dos semanas](roadmap-two-weeks.md): calendario de ejecución, entregables, aceptación y seguimiento.
- [Notas de versión 0.1.0-rc1](release-notes-0.1.0-rc1.md): alcance, resultados medidos y limitaciones del candidato.

## Principio de mantenimiento

La documentación describe el comportamiento comprobable del código actual. Una intención de diseño no equivale a una garantía de compatibilidad. Si el código, las pruebas y los documentos discrepan, hay que resolver la discrepancia y actualizar las tres piezas; no asumir que la documentación prevalece automáticamente.
