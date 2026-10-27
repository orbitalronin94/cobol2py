# Notas de hito — madurez 0.8 (borrador de ingeniería)

> Este documento registra el hito de madurez del flujo de trabajo. No implica que exista una etiqueta Git o una publicación binaria 0.8.0; la versión del traductor sigue siendo la declarada en cobol2py.py.

## Cambios del hito

- **Inventario de CALL:** separación entre nombres literales entre comillas e identificadores dinámicos, en el agente Python y en la demo web.
- **Piloto con esquema versionado:** el informe JSON pasa a esquema 2 e incluye versión del traductor, estado sintáctico por archivo y estado semántico explícito `not-evaluated`.
- **Clasificación de diagnósticos:** los avisos se etiquetan como limitación conocida, dependencia sin resolver, posible defecto o revisión pendiente. La clasificación conserva código, línea y mensaje originales; no elimina avisos.
- **Trazabilidad diferencial:** se enlazan fixtures candidatas solo cuando la ruta de fuente coincide exactamente con el manifiesto. Un enlace no implica que la fixture se haya ejecutado en el piloto.
- **Informe revisable:** el Markdown incluye resumen por categoría y código, detalle por archivo y una lista de fixtures candidatas.
- **CI:** el job de modernización valida el contrato del informe y publica los ficheros del piloto como artefacto temporal para inspección.
- **Roadmap:** se añade una escala de hitos de madurez v0.1–v0.8 y se separa el triage automatizado de la adjudicación humana pendiente.

## Cómo reproducir

```bash
python -m unittest discover -s tests -p 'test_modernize_pilot.py' -v
python tools/modernize_pilot.py samples --out-dir /tmp/cobol2py-pilot
```

Los ficheros principales son:

- `/tmp/cobol2py-pilot/translation-report.json`
- `/tmp/cobol2py-pilot/translation-report.md`
- `/tmp/cobol2py-pilot/inventory.json`
- `/tmp/cobol2py-pilot/inventory.md`

En GitHub Actions, el artefacto se publica con el nombre `modernization-pilot-diagnostics`.

## Límites y revisión pendiente

- La ejecución del piloto comprueba sintaxis; no ejecuta el Python generado ni prueba equivalencia semántica.
- La categoría automática es un triage inicial. Cada uno de los 36 archivos con diagnósticos debe revisarse antes de declarar falsos positivos o autorizar una migración.
- El benchmark diferencial actual cubre 102 casos y compara salida estándar y código de retorno; no representa todos los dialectos ni efectos externos.
- La demo web del agente sigue siendo heurística; el CLI Python es la salida más completa y reproducible.
- Los diagnósticos de aritmética PIC, tablas, overlays, comparaciones alfanuméricas y otras construcciones parciales continúan siendo límites conocidos hasta que haya implementación y regresiones específicas.

## Criterio de aceptación

El hito 0.8 se considera una mejora de trazabilidad y proceso, no una certificación de compatibilidad. Para avanzar hacia 0.9, hay que revisar los resultados por archivo, convertir falsos positivos y defectos confirmados en regresiones, y ejecutar comparación diferencial solo en casos aprobados y reproducibles.
