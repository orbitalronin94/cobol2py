# Triage de diagnósticos del piloto sobre samples

> Informe estático generado por CI a partir del código actual. El artefacto descargable [modernization-pilot-diagnostics](https://github.com/orbitalronin94/cobol2py/actions/runs/40521702715/artifacts/12742122278) contiene el JSON/Markdown completos, traducciones generadas e inventario. Esta página conserva la clasificación de la línea base para revisión y no sustituye el artefacto por commit.

## Resultado actual

- Fuentes COBOL analizadas: **108**
- Traducidas: **108/108**
- Errores de sintaxis Python: **0**
- Errores de traducción: **0**
- Fuentes con diagnósticos: **35**
- Diagnósticos totales: **50**
- Clasificación automática: **50 limitaciones conocidas**, **0 posibles defectos** en la revisión actual
- Códigos: **46 ARITHMETIC_SIZE_ERROR_UNSUPPORTED**, **4 PARTIAL_NUMERIC_PIC_SEMANTICS**
- Revisión humana pendiente: **35 archivos**
- Validación diferencial explícita: **105/105 fixtures coincidentes** en stdout y código de retorno con GnuCOBOL; las otras 6 fuentes no tienen fixture exacta en el manifiesto y figuran como no aplicables.

## Corrección de falso positivo

La línea base anterior tenía 36 fuentes con diagnósticos, incluyendo `bench_43_table_first.cbl` con `MALFORMED_CONTROL_FLOW`. El archivo contiene un `END-IF` después de la columna 72. La detección automática de formato lo trataba como COBOL fixed-format y truncaba el terminador. Se ajustó la heurística para preferir free-format cuando detecta verbos de control más allá de la columna 72; la regresión verifica que END-IF se conserva y que el diagnóstico desaparece. La fixture `table-first` sigue coincidiendo con GnuCOBOL.

## Clasificación por fuente

| Fuente | Avisos | Códigos | Fixture diferencial | Estado de fixture | Triage | Revisión humana |
|---|---:|---|---|---|---|---|
| `arithmetic_size.cbl` | 5 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `arithmetic-receiving-pic` | `matched` | known-limitations-only | pendiente |
| `bench_061_numeric-61.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-61` | `matched` | known-limitations-only | pendiente |
| `bench_062_numeric-62.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-62` | `matched` | known-limitations-only | pendiente |
| `bench_063_numeric-63.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-63` | `matched` | known-limitations-only | pendiente |
| `bench_064_numeric-64.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-64` | `matched` | known-limitations-only | pendiente |
| `bench_065_numeric-65.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-65` | `matched` | known-limitations-only | pendiente |
| `bench_066_numeric-66.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-66` | `matched` | known-limitations-only | pendiente |
| `bench_067_numeric-67.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-67` | `matched` | known-limitations-only | pendiente |
| `bench_068_numeric-68.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-68` | `matched` | known-limitations-only | pendiente |
| `bench_074_perform-74.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `perform-74` | `matched` | known-limitations-only | pendiente |
| `bench_075_perform-75.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `perform-75` | `matched` | known-limitations-only | pendiente |
| `bench_076_perform-76.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `perform-76` | `matched` | known-limitations-only | pendiente |
| `bench_077_numeric-77.cbl` | 3 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-77` | `matched` | known-limitations-only | pendiente |
| `bench_087_numeric-87.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-87` | `matched` | known-limitations-only | pendiente |
| `bench_088_numeric-88.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-88` | `matched` | known-limitations-only | pendiente |
| `bench_089_numeric-89.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-89` | `matched` | known-limitations-only | pendiente |
| `bench_090_numeric-90.cbl` | 2 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-90` | `matched` | known-limitations-only | pendiente |
| `bench_091_numeric-91.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-91` | `matched` | known-limitations-only | pendiente |
| `bench_096_perform-96.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `perform-96` | `matched` | known-limitations-only | pendiente |
| `bench_097_numeric-97.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-97` | `matched` | known-limitations-only | pendiente |
| `bench_099_numeric-99.cbl` | 2 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-99` | `matched` | known-limitations-only | pendiente |
| `bench_12_numeric_add.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-add` | `matched` | known-limitations-only | pendiente |
| `bench_13_numeric_subtract.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-subtract` | `matched` | known-limitations-only | pendiente |
| `bench_14_numeric_multiply.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-multiply` | `matched` | known-limitations-only | pendiente |
| `bench_15_numeric_compute.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-compute` | `matched` | known-limitations-only | pendiente |
| `bench_16_compute_expr.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-compute-expression` | `matched` | known-limitations-only | pendiente |
| `bench_33_numeric_increment.cbl` | 2 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-increment` | `matched` | known-limitations-only | pendiente |
| `bench_34_numeric_decrement.cbl` | 2 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `numeric-decrement` | `matched` | known-limitations-only | pendiente |
| `bench_38_compute_subtract.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `compute-subtract` | `matched` | known-limitations-only | pendiente |
| `bench_39_compute_multiply.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `compute-multiply` | `matched` | known-limitations-only | pendiente |
| `bench_40_compute_divide_exact.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `compute-divide-exact` | `matched` | known-limitations-only | pendiente |
| `hello.cbl` | 3 | `PARTIAL_NUMERIC_PIC_SEMANTICS`, `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | — | `not-applicable` | known-limitations-only | pendiente |
| `java_backend.cbl` | 1 | `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | — | `not-applicable` | known-limitations-only | pendiente |
| `numeric_semantics.cbl` | 2 | `PARTIAL_NUMERIC_PIC_SEMANTICS` | — | `not-applicable` | known-limitations-only | pendiente |
| `realtest.cbl` | 3 | `PARTIAL_NUMERIC_PIC_SEMANTICS`, `ARITHMETIC_SIZE_ERROR_UNSUPPORTED` | `realtest` | `matched` | known-limitations-only | pendiente |

## Qué significan los códigos

- **ARITHMETIC_SIZE_ERROR_UNSUPPORTED (46):** el programa usa ADD/SUBTRACT/MULTIPLY/DIVIDE/COMPUTE. La semántica completa de overflow, ON SIZE ERROR, redondeo y escalado no está garantizada. El aviso es conservador: no significa que cada operación desborde.
- **PARTIAL_NUMERIC_PIC_SEMANTICS (4):** hay campos PIC con signo, escala o escalado (S/V/P). Debe revisarse la precisión y el formato requerido por el programa.
- **Estado de revisión:** la clasificación automática separa limitaciones conocidas de defectos potenciales, pero no determina si el riesgo afecta al uso real. No se declara ningún archivo listo para migrar solo por pasar sintaxis o una fixture.

## Evidencia y siguiente paso

- [CI del piloto y benchmark diferencial](https://github.com/orbitalronin94/cobol2py/actions/runs/40521702715)
- [Descargar el artefacto del piloto](https://github.com/orbitalronin94/cobol2py/actions/runs/40520567099/artifacts/12740274709)
- [Roadmap de modernización](roadmap-two-weeks.md)
- [Alcance de compatibilidad](compatibility.md)

La siguiente tarea manual es revisar los 35 archivos según los requisitos del sistema objetivo y convertir cualquier discrepancia real en un caso mínimo. La cobertura diferencial es útil pero no cubre todos los valores de entrada, dialectos ni efectos externos. La cifra de 105/105 corresponde al manifiesto actual y debe actualizarse junto con el artefacto cuando cambie el corpus.
