# Proceso para cambios técnicos

## Antes de cambiar el traductor

1. Identificar el comportamiento concreto que falta o falla.
2. Crear un ejemplo mínimo de COBOL que lo reproduzca.
3. Determinar el comportamiento de referencia con GnuCOBOL cuando sea aplicable.
4. Localizar la fase afectada: preprocesado, análisis de variables, estructura de procedimiento, traducción de expresiones/sentencias o emisión Python.
5. Añadir una prueba que falle antes del cambio, si es posible.

## Al implementar

- Mantener cambios pequeños y enfocados.
- Evitar arreglar un caso rompiendo silenciosamente otros formatos o sentencias.
- Para semántica que afecte a ejecución, preferir tests diferenciales además de tests de texto generado.
- No convertir errores reales en éxito mediante exclusión de casos, normalización excesiva de salida o relajación accidental de la comparación.
- Si el cambio altera una decisión documentada, actualizar el registro y explicar por qué.

## Validación mínima

```bash
python -m unittest discover -s tests -v
python -m py_compile cobol2py.py
python cobol2py.py programa.cbl --strict
python benchmarks/run_benchmark.py --translator cobol2py.py
```

El benchmark requiere GnuCOBOL y falla con código distinto de cero si alguna referencia no compila o el candidato no coincide exactamente. Usa `--report-only` solo para exploración. Revisa el informe caso por caso, no solo el porcentaje. En CI, consulta tanto el workflow de tests como el de benchmark diferencial.

## Qué registrar en cada mejora

Para cada PR o cambio semántico importante, documentar:

- **Problema observado:** entrada COBOL mínima y resultado previo.
- **Comportamiento de referencia:** salida/código de retorno de GnuCOBOL o referencia documental cuando no sea viable.
- **Cambio realizado:** regla nueva o corrección y fase afectada.
- **Regresiones añadidas:** nombres de tests y/o IDs del benchmark.
- **Resultados:** tests ejecutados y porcentaje del corpus, incluyendo el denominador.
- **Riesgos y límites:** casos cercanos no cubiertos.
- **Decisión afectada:** ID de `decisions.md`, si aplica.

No es necesario añadir un documento largo por cada cambio trivial. Los cambios semánticos deben quedar en el historial de decisiones o en una nota de versión; los detalles de implementación también deben estar en el mensaje/PR para que la historia sea rastreable.

## Plantilla breve para un registro de mejora

```markdown
### [AAAA-MM-DD] Título breve

- **Problema:**
- **Referencia:**
- **Cambio:**
- **Pruebas/benchmark:**
- **Resultado antes → después:**
- **Límites conocidos:**
- **Decisión relacionada:**
```

## Evolución del corpus

- No borrar casos difíciles para mejorar el porcentaje.
- Mantener IDs estables; si un caso cambia de objetivo, crear uno nuevo o explicar el cambio.
- Registrar si se añade o retira un caso y por qué.
- Comparar versiones con el mismo manifiesto siempre que se quiera atribuir el cambio de puntuación al traductor.
- Informar el número de casos ejecutados, fallidos y no ejecutados, además del porcentaje.


El benchmark debe producir informes aun cuando falle la ejecución de la referencia: verifica que compile, que termine dentro del timeout y que su salida/código de retorno puedan usarse como oráculo. No confundas un código de retorno COBOL distinto de cero con un fallo de infraestructura.
