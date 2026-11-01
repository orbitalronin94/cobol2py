# STRING ... ON OVERFLOW: siguiente iteración semántica

## Punto de partida

Esta rama nace del HEAD de la PR #203, que a su vez parte del `main` con baseline integrado de **240/500 (48,00 %)**. El torneo sintáctico #203–#209 no superó ese resultado: el máximo válido fue 239/500. Esta iteración no debe relajar ni reemplazar ese baseline.

## Hipótesis

Las variantes de detección conservadora del torneo cambian principalmente cómo se reconoce la cláusula, pero no implementan su semántica. El siguiente intento debe dejar de competir con otra expresión regular y comprobar si la traducción de un subconjunto acotado de `STRING ... ON OVERFLOW` recupera programas ejecutables sin alterar casos no relacionados.

## Alcance inicial propuesto

Implementar únicamente casos que puedan representarse sin ambigüedad en el runtime actual:

- Concatenación de literales y referencias simples en un receptor alfanumérico declarado con `PIC X(n)`.
- Aplicar el límite de capacidad del receptor según el comportamiento COBOL medido con GnuCOBOL.
- Ejecutar `ON OVERFLOW` cuando la longitud resultante exceda la capacidad y `NOT ON OVERFLOW` en caso contrario.
- Mantener la semántica de los operandos y el receptor sincronizada entre `cobol2py.py` y `web/index.html`.
- Rechazar explícitamente combinaciones fuera del subconjunto implementado (por ejemplo, delimitadores complejos, punteros, receptores múltiples o identificadores con subíndices) hasta que tengan pruebas diferenciales.

No asumir de antemano cómo se resuelven truncamiento, contenido parcial del receptor o evaluación de las ramas: cada regla debe quedar fijada por una fixture mínima ejecutada contra GnuCOBOL.

## Pruebas obligatorias

1. Caso sin overflow: la longitud concatenada cabe exactamente en el receptor y se ejecuta solo `NOT ON OVERFLOW`.
2. Caso con overflow: el resultado excede la capacidad y se ejecuta solo `ON OVERFLOW`.
3. Límite exacto: resultado de longitud igual a la capacidad.
4. Resultado de longitud cero / operandos vacíos si el parser los admite.
5. Receptor inicializado con contenido previo, para documentar si se conserva o reemplaza según la forma COBOL admitida.
6. Literal con texto `"ON OVERFLOW"`: no debe activar falsamente el diagnóstico.
7. Variantes de espacios y saltos de línea.
8. Paridad Python/navegador y regresiones para cada fallo corregido.

Cada fixture debe conservar el fuente COBOL, la salida esperada de GnuCOBOL, el resultado traducido y el motivo de inclusión. No convertir diferencias del oráculo o casos que no compilan en fallos del traductor.

## Gate de benchmark

- No ejecutar el corpus primario retirado.
- Usar el mismo corpus fijo de evaluación de 500 casos, el mismo denominador y el mismo criterio de coincidencia exacta (stdout y código de retorno).
- Registrar SHA del candidato y scorecard por ejecución.
- **No integrar si el candidato no supera 240/500**, aunque supere la referencia histórica de 236/500.
- Exigir CI y pruebas diferenciales verdes; ningún workflow omitido cuenta como validación.
- Comparar tiempo de ejecución solo entre mediciones con el mismo corpus y configuración.

## Criterio de salida

Esta nota define el contrato de trabajo, no afirma que la semántica esté implementada ni que haya mejorado el benchmark. La PR debe permanecer abierta hasta que incluya implementación real, regresiones reproducibles, paridad Python/navegador y una ejecución externa que supere el baseline integrado.
