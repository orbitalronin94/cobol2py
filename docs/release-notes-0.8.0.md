# Notas de hito — madurez 0.8 (borrador de ingeniería)

> Este documento registra el hito de madurez del flujo de trabajo. No implica que exista una etiqueta Git o una publicación binaria 0.8.0; la versión del traductor sigue siendo la declarada en cobol2py.py.

## Cambios del hito

- **Inventario de CALL y literales:** separación entre nombres literales entre comillas e identificadores dinámicos; el CLI y la demo web enmascaran contenido literal para evitar dependencias falsas.
- **Piloto con esquema versionado:** el informe JSON pasa a esquema 2 e incluye versión del traductor, estado sintáctico por archivo y estado semántico explícito `not-evaluated`.
- **Clasificación de diagnósticos:** los avisos se etiquetan como limitación conocida, dependencia sin resolver, posible defecto o revisión pendiente. La clasificación conserva código, línea y mensaje originales; no elimina avisos.
- **Triage de 108 fuentes:** CI confirma 108 traducciones, 0 errores de sintaxis, 0 errores de traducción y 35 fuentes con 50 diagnósticos conocidos (46 avisos de aritmética y 4 de PIC parcial). Se corrigió un falso positivo de formato en `bench_43_table_first.cbl`; la revisión humana de los 35 archivos restantes sigue pendiente.
- **Trazabilidad diferencial:** se enlazan fixtures candidatas solo cuando la ruta de fuente coincide exactamente con el manifiesto. El modo opt-in --differential ejecuta solo esas fixtures y registra estado por caso; un enlace sin ejecutar no implica equivalencia.
- **Informe revisable:** el Markdown incluye resumen por categoría y código, detalle por archivo y una lista de fixtures candidatas.
- **CI:** el job de modernización valida el contrato del informe y publica los ficheros del piloto como artefacto temporal para inspección. El modo diferencial opt-in coincidió en 102/102 fixtures con GnuCOBOL en stdout y código de retorno.
- **Experiencia web:** filtro de texto global, pruebas de rutas Unicode y casos con palabras clave dentro de literales.
- **Formato fuente:** el modo auto conserva terminadores de control más allá de columna 72 cuando detecta código largo indentado.
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

El hito 0.8 se considera una mejora de trazabilidad y proceso, no una certificación de compatibilidad. El detalle por fuente está en [pilot-diagnostics-baseline.md](pilot-diagnostics-baseline.md). Para avanzar hacia 0.9, hay que revisar los resultados por archivo, convertir falsos positivos y defectos confirmados en regresiones, y ejecutar comparación diferencial solo en casos aprobados y reproducibles.
