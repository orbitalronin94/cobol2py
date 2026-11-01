# SOTA semántica COBOL2PY: plan de integración por gates

Este plan recoge las ocho líneas propuestas para la iteración semántica. No declara integradas las dependencias externas ni atribuye mejoras de benchmark que no se hayan medido.

## Reglas de aceptación

- Canario Maquinas: stdout numérico esperado [70.5882352941, 29.4117647059] (confirmar el formato exacto del harness antes de convertirlo en fixture).
- Baseline de main: **240/500 (48,00 %)**; no aceptar una regresión como resultado integrable.
- No leer, modificar ni ejecutar benchmarks/legacy_primary/ ni benchmarks/edge_cases/.
- La muestra fija de 500 casos es un corpus de evaluación ya consultado durante el desarrollo, no un holdout estadístico intacto.
- No integrar cambios de semántica si las pruebas unitarias, el canario, la comparación diferencial y el scorecard del SHA candidato no están verificados.

## Paquetes de trabajo y estado

| Tarea | Alcance | Estado en esta iteración |
|---|---|---|
| 1. Adaptadores de runtime | Decimal fijo, cadenas de ancho fijo y vistas de grupo sobre almacenamiento compartido | **Prototipo añadido** en ronin/runtime_adapters.py; todavía no es el runtime predeterminado del emisor |
| 2. Copybooks | Metadatos PIC, expansión conservadora de OCCURS y anotación de REDEFINES | **Parser inicial añadido** en ronin/copybook_parser.py; no calcula offsets ABI exactos ni resuelve todos los layouts |
| 3. Puente Cobrix | JSON Lines a un proceso Java y fallback explícito | Pendiente: determinar instalación/versionado/licencia y contrato CLI reproducible antes de introducir dependencia |
| 4. Verificación Z3 | Comprobaciones de equivalencia, modelos SAT y reportes de contraejemplos | Pendiente: un resultado UNSAT solo es certificado respecto de las fórmulas y supuestos codificados; no equivale por sí solo a equivalencia completa del programa |
| 5. Caché dual | SQLite por AST normalizado y ChromaDB semántico | Pendiente: no habilitar cache semántica en traducciones ejecutables sin validación de equivalencia; no contaminar resultados de benchmark con cachés entre candidatos |
| 6. Parser AST/ASG | Backend ANTLR/ProLeap o cobol-py, con fallback | Pendiente: medir cobertura de dialectos y distribución/licencia; mantener el parser actual como ruta estable |
| 7. Diff byte-perfect | Comparar stdout como bytes y código de retorno | La evaluación externa ya usa stdout/código de retorno; pendiente extraer un comparador reutilizable con diagnóstico del primer byte |
| 8. Esqueletos y brief | TODO(high), informe JSON y brief acotado | Pendiente: debe evitar presentar esqueletos incompletos como traducciones ejecutables |

## Secuencia segura

1. Completar la semántica acotada de STRING ... ON OVERFLOW en la PR de esta rama, con fixtures verificadas contra GnuCOBOL y paridad Python/navegador.
2. Ejecutar la suite de tests y el canario Maquinas; documentar el comando y resultado real.
3. Evaluar la rama con el corpus fijo completo de 500 casos y adjuntar SHA, denominador, stdout/código de retorno y scorecard.
4. Mantener separados los cambios de runtime, copybooks, parser y verificadores en commits/PRs pequeños; cada paquete necesita contrato, pruebas diferenciales y fallback seguro.
5. Integrar cada componente en el traductor solo después de demostrar que el comportamiento del subconjunto actual no cambia inesperadamente.

## Riesgos semánticos explícitos

- CobolDecimal es un adaptador experimental. Los límites de dígitos, escalas implícitas P, redondeo COBOL, ON SIZE ERROR y precisión intermedia requieren pruebas con compilador real.
- CobolString trabaja con cadenas Python y ofrece una clave EBCDIC explícita; no convierte automáticamente todo el almacenamiento a EBCDIC.
- GroupView usa offsets de bytes proporcionados por el llamador. No calcula layouts ni resuelve REDEFINES.
- parse_pic_string y el parser de copybooks solo cubren una gramática deliberadamente limitada. Cualquier PIC/uso no soportado debe fallar o quedar marcado, nunca inventar offsets.
- Z3 puede encontrar contraejemplos a fórmulas, pero no demuestra equivalencia de un traductor completo si la codificación omite efectos, tipos o reglas de ejecución.
- Una caché semántica puede devolver una traducción incorrecta aunque el fragmento parezca similar; por defecto, debe permanecer desactivada para traducción ejecutable hasta disponer de un criterio de equivalencia.
