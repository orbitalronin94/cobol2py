# Notas de versión — 0.1.0-rc1

> Candidato de validación, no una publicación etiquetada. Los resultados de comportamiento citados se midieron en el commit `4280bff92d45ee6fd8e96026d11a6db5ddcb48e9`; los cambios posteriores en esta secuencia son de documentación.

## Cambios incluidos

- **Semántica numérica acotada:** las operaciones aritméticas básicas aplican el tamaño del PIC receptor para los campos numéricos simples, evitando que un `PIC 99` retenga tres dígitos tras el overflow.
- **Corpus diferencial ampliado:** 102 fixtures COBOL comparadas con GnuCOBOL. El commit de validación obtuvo 102/102 coincidencias exactas de salida y código de retorno (100 %), incluida `arithmetic-receiving-pic`, que cubre `ADD`, `COMPUTE`, `MULTIPLY`, `SUBTRACT` y `DIVIDE` sobre `PIC 99`.
- **COPY REPLACING:** fixture diferencial que cubre dos parejas sencillas de pseudo-texto en una cláusula.
- **Inventario multiarchivo:** se excluyen comentarios COBOL/JCL/SQL reconocidos y se reportan referencias con varios destinos posibles.
- **Piloto integrado:** `tools/modernize_pilot.py` conecta inventario, traducción del subconjunto y comprobación de sintaxis; genera reportes Markdown/JSON sin ejecutar los programas producidos.
- **Demo standalone:** la fuente embebida en `web/index.html` se mantiene idéntica a `cobol2py.py`, verificada por test.

## Evidencia de validación

- Suite completa de GitHub Actions en Python 3.10, 3.11, 3.12 y 3.13: pasó en el commit de código `4280bff`.
- [Benchmark diferencial 102/102 con las cinco operaciones aritméticas](https://github.com/orbitalronin94/cobol2py/actions/runs/40496463428).
- [Suite de pruebas del commit de código](https://github.com/orbitalronin94/cobol2py/actions/runs/40495907342).
- Piloto sobre `samples`: 108 programas fuente traducidos, 0 errores de sintaxis, 0 errores de traducción y 36 archivos con diagnósticos para revisión.

## Limitaciones conocidas

- La puntuación diferencial solo representa el corpus versionado; no mide compatibilidad general con COBOL.
- La adaptación aritmética no cubre toda la semántica de `ON SIZE ERROR`, redondeo, escalado `P` ni todos los casos de precisión/signo.
- El piloto comprueba sintaxis, no equivalencia de comportamiento; para ello hacen falta pruebas diferenciales y datos de ejecución representativos.
- El análisis del agente sigue siendo heurístico. Los destinos ambiguos, referencias externas, llamadas dinámicas y características de proveedor requieren revisión.
- Los 36 archivos con diagnósticos del piloto no se consideran automáticamente correctos ni listos para migración.

## Recomendación

Tratar este estado como candidato de evaluación técnica. Antes de usarlo para una migración real, revisar todos los diagnósticos, añadir casos del dialecto y entorno reales y ejecutar validación diferencial con entradas representativas.
