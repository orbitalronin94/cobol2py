# Documentación de ingeniería

Esta carpeta documenta el diseño actual, las decisiones técnicas, el alcance semántico y el proceso para validar cambios de `cobol2py`.

## Documentos

- [Arquitectura](architecture.md): flujo de traducción, estructuras internas y límites.
- [Registro de decisiones](decisions.md): decisiones tomadas, motivación, consecuencias y estado.
- [Compatibilidad COBOL](compatibility.md): comportamientos implementados, verificación y limitaciones conocidas.
- [Proceso de cambios](change-process.md): cómo proponer, medir y documentar mejoras.

## Principio de mantenimiento

La documentación describe el comportamiento comprobable del código actual. Una intención de diseño no equivale a una garantía de compatibilidad. Si el código, las pruebas y los documentos discrepan, hay que resolver la discrepancia y actualizar las tres piezas; no asumir que la documentación prevalece automáticamente.
