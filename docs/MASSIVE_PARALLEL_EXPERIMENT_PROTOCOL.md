# Protocolo de experimentación masiva en paralelo contra main

**Fecha:** 2026-11-03  
**Estado:** protocolo y orquestación preparados en la PR #315; requieren merge para activarse. Las 212 candidatas funcionales aún deben crearse y validarse. No autoriza merges automáticos.

## 1. Objetivo

Cambiar el modo de buscar mejoras en COBOL → Python. Hasta ahora se trabajaba con un número pequeño de hipótesis muy elaboradas (el torneo histórico de siete candidatas). Ese enfoque ayuda a producir cambios profundos, pero puede estancarse: después de varias rondas, las mejoras marginales se reducen y se exploran pocas alternativas.

La nueva estrategia consiste en abrir muchas líneas de experimentación independientes que compitan contra **el mismo commit de main**, medirlas de forma homogénea y conservar únicamente las que demuestren una mejora real. La hipótesis que queremos probar es:

> Una búsqueda amplia, diversificada y automatizada puede encontrar combinaciones de cambios útiles que una búsqueda pequeña y artesanal no está descubriendo.

Esto es una hipótesis, no una promesa. Multiplicar ramas no multiplica automáticamente la calidad: si las mutaciones son aleatorias sin fundamento, solo se multiplican el ruido, los costes de CI y las oportunidades de regresión.

## 2. Punto de partida conocido

- Baseline registrado: **250/500 (50,0 %)** en la muestra fija X-COBOL v2.
- SHA de main usado como baseline en el registro: `a3563994cc41749f0e0c9555099e52c974aa6a26`.
- Run de referencia: [Actions #538](https://github.com/orbitalronin94/cobol2py/actions/runs/41602383991).
- Una candidata necesita al menos **251/500**, los 500 casos completos, checksum verificado, suite completa verde y resultado asociado al SHA exacto evaluado.
- El criterio de coincidencia es estricto: stdout byte a byte y código de retorno idéntico a GnuCOBOL.
- La muestra se consulta repetidamente durante el desarrollo. Es una muestra fija de evaluación, no un holdout estadístico intacto; optimizar contra ella puede producir sobreajuste.

Los fallos agregados registrados (169 diferencias de stdout/return code, 39 errores de sintaxis Python, 38 timeouts del programa traducido, 3 salidas excesivas y 2 timeouts del traductor) son señales para investigar, no una atribución causal. No se debe asignar una familia de fallos a una sentencia COBOL sin reproducirla y clasificarla.

## 3. Qué significa «muchas peleas simultáneas»

Cada candidata debe ser una rama aislada, creada desde **el mismo SHA de main congelado para esa ronda**. Cada rama plantea una hipótesis concreta y produce un cambio funcional real. La candidata se evalúa contra ese mismo baseline y el mismo conjunto de 500 IDs.

No significa:
- crear cien ramas vacías;
- cambiar nombres, comentarios o formato para simular diversidad;
- introducir mutaciones arbitrarias que no tengan una hipótesis verificable;
- comparar unas candidatas contra otras con bases diferentes;
- juntar cambios antes de saber qué aporta cada uno;
- permitir que una candidata cambie main o se auto-promueva.

La aleatoriedad puede utilizarse para generar variantes, elegir parámetros de búsqueda o explorar distintas implementaciones. Pero cada variante debe superar revisión estática, pruebas locales y benchmark. La semilla, el tipo de mutación y los archivos modificados deben quedar registrados para que el experimento sea reproducible.

## 4. Diseño de la ronda masiva

### 4.1 Congelar la referencia

Al comenzar una ronda, registrar:
- SHA exacto de main;
- checksum y versión del corpus;
- los 500 identificadores de caso y su asignación a los cuatro shards;
- versión de Python, GnuCOBOL, dependencias y configuración de timeout;
- SHA del workflow y de los scripts de benchmark.

Todas las candidatas de esa ronda parten de ese SHA. Si main cambia durante la ronda, no se cambia silenciosamente la base: se termina la comparación contra la referencia congelada y después se repite la validación de los ganadores contra el nuevo main.

### 4.2 Generar un conjunto diverso de hipótesis

Las candidatas se distribuyen entre familias de problemas, por ejemplo:
1. generación de Python sintácticamente válida;
2. símbolos, ámbitos, nombres cualificados y registros;
3. semántica numérica PIC/USAGE y asignaciones;
4. OCCURS, subíndices y tablas;
5. layout de grupos, MOVE y overlays;
6. INSPECT, STRING y UNSTRING;
7. PERFORM, rangos de párrafos y terminación;
8. manejo de archivos y operaciones de entrada/salida;
9. análisis léxico/parser y recuperación de construcciones no soportadas;
10. optimizaciones o refactorizaciones internas con pruebas de equivalencia.

La lista es un mapa de exploración, no una afirmación de que todas esas áreas expliquen los fallos observados. Se pueden añadir familias cuando un informe de caso lo justifique.

Cada candidata incluye una ficha breve:
- hipótesis y evidencia que la motiva;
- cambio funcional esperado;
- archivos y subsistemas afectados;
- casos mínimos de reproducción;
- regresiones añadidas;
- riesgos conocidos y límites de alcance.

Se permiten varias variantes de una misma hipótesis, pero deben ser realmente distintas (por ejemplo, estrategias de implementación alternativas), no duplicados con cambios cosméticos.

### 4.3 Escalar por oleadas, no lanzar cien trabajos ciegamente

Propuesta de crecimiento:
- **Piloto:** 10–16 candidatas.
- **Oleada 2:** 25–32 candidatas si el piloto es estable.
- **Oleada 3:** 50–64 candidatas.
- **Escala objetivo inicial:** hasta 100 candidatas por ronda.

El número es el tamaño del espacio de búsqueda, no la concurrencia obligatoria. La ejecución debe limitarse por capacidad real de GitHub Actions, minutos disponibles, rate limits y tiempo de cola. Es preferible mantener 8–16 evaluaciones activas y una cola reproducible que lanzar 100 jobs a la vez y saturar el CI.

Antes de superar el torneo de siete candidatas hay que auditar y, si hace falta, adaptar el workflow actual: su nombre y diseño históricos son de siete candidatas. No se debe asumir que descubre, agenda y recoge correctamente cien PRs sin modificarlo y probarlo. La ampliación debe conservar permisos de solo lectura, sin endpoints de merge ni pushes a main.

### 4.4 Puertas de evaluación en cascada

Para ahorrar cómputo, cada candidata pasa por etapas:

**Puerta A — validez**
- rama creada desde el SHA congelado;
- diff no vacío, acotado y revisable;
- no modifica corpus, checksum, selección, denominador, timeouts ni criterio de scoring;
- no contiene secretos ni cambios de workflow destinados a auto-promoverse.

**Puerta B — pruebas rápidas**
- lint/compilación y tests unitarios relevantes;
- fixtures mínimas para la hipótesis;
- prueba de que el cambio realmente se activa en el caso objetivo;
- descarte temprano de errores sintácticos o fallos triviales.

**Puerta C — suite completa**
- suite completa del repositorio verde;
- regresiones anteriores preservadas;
- sin tests deshabilitados, debilitados o eliminados para conseguir verde.

**Puerta D — benchmark externo**
- ejecutar los cuatro shards deterministas de 125 casos;
- completar exactamente 500/500;
- verificar checksum y SHA;
- producir scorecard por caso y artefactos diagnósticos;
- nunca sumar shards de ejecuciones o commits distintos.

**Puerta E — comparación pareada**
- comparar la candidata con main sobre los mismos 500 IDs;
- calcular aciertos nuevos, fallos corregidos y regresiones;
- comprobar especialmente que todos los casos que pasaban en main siguen pasando.

Las candidatas que no pasan una puerta se etiquetan con el motivo y no consumen etapas más caras.

## 5. Criterio de victoria: mejorar sin regresiones

La línea base es 250/500. Una candidata solo puede ser considerada ganadora si cumple simultáneamente:

1. **500/500 casos evaluados** con checksum correcto.
2. **Más de 250 aciertos**; el mínimo técnico para superar el baseline es 251/500 (50,2 %).
3. **Cero regresiones sobre los casos que main ya pasaba.** Ningún ID que era acierto en main puede convertirse en fallo en la candidata.
4. Suite completa y regresiones enfocadas verdes.
5. Resultado reproducible para el SHA exacto.
6. Diff revisable y explicación técnica de por qué mejora.

Una subida neta del porcentaje que esconda regresiones no cumple el objetivo. Se publicarán al menos estas cifras por candidata:
- aciertos totales y porcentaje;
- aciertos conservados de main;
- casos nuevos corregidos;
- regresiones (debe ser cero para ganar);
- casos que siguen fallando;
- duración, timeouts y estado de cada shard.

La mejora se informa en puntos porcentuales y en número de casos. Por ejemplo, pasar de 250/500 a 260/500 equivale a +10 casos y +2,0 puntos porcentuales; no debe describirse como una mejora del 2 % relativo.

## 6. Cómo elegir ganadores y construir PRs finales

Las candidatas se ordenan primero por cumplimiento de las puertas obligatorias, después por mayor número de aciertos y, en caso de empate, por menor complejidad/riesgo y mejor cobertura de regresiones.

No se combinan automáticamente todos los ganadores. Dos cambios individualmente buenos pueden entrar en conflicto o perder la mejora al integrarse. Procedimiento:
1. conservar cada candidata ganadora aislada;
2. agrupar solo cambios compatibles y con áreas de código suficientemente independientes;
3. crear una rama de integración desde el main vigente;
4. aplicar el conjunto elegido;
5. ejecutar suite completa y benchmark completo de nuevo sobre el SHA integrado;
6. comparar de nuevo contra main y exigir cero regresiones;
7. abrir la PR de integración con scorecard, SHAs, enlaces de runs y lista de cambios;
8. solicitar revisión humana.

Se pueden organizar cuatro carriles o lotes de trabajo y abrir hasta cuatro PRs de integración si hay cuatro conjuntos compatibles y validados. El número de PRs no debe forzarse: si solo hay un ganador, se abre una sola PR; si no hay ganadores, no se abre ninguna PR de integración. Las ramas experimentales y las PRs de evaluación no son PRs de integración.

**No hay merge automático.** La decisión de merge sigue siendo humana y requiere revisar la implementación, no solo el porcentaje.

## 7. Qué hacer si aparecen muchas candidatas ganadoras

Si varias candidatas ganan:
- probar combinaciones por pares solo cuando sus cambios sean compatibles;
- volver a ejecutar las puertas completas en cada combinación;
- descartar combinaciones que introduzcan una regresión, aunque cada cambio aislado fuese ganador;
- evitar integrar dos soluciones distintas al mismo problema sin una comparación específica;
- mantener un registro de resultados negativos y de conflictos.

Si ninguna gana, el resultado de la ronda sigue siendo útil: identifica familias que no dieron resultado bajo esa configuración. No se debe bajar el umbral, alterar el corpus ni redefinir «sin regresiones» para declarar un éxito.

## 8. Métricas para saber si escalar merece la pena

El experimento no se evalúa solo por la mejor puntuación. Registrar:
- candidatas generadas, válidas, ejecutadas y completadas;
- porcentaje descartado en cada puerta;
- número de candidatas con mejora neta y número con cero regresiones;
- mejor score y distribución de scores;
- ganancia por cada 10/25/50/100 candidatas;
- minutos de Actions, concurrencia máxima y tiempo total de pared;
- coste de revisión humana;
- duplicados entre hipótesis;
- ganadores que sobreviven al integrar y revalidar.

Comparar el nuevo método con el histórico de siete candidatas usando presupuestos comparables (minutos de CI y esfuerzo de revisión), no solo el número bruto de ramas. Si cien candidatas consumen diez veces más recursos para encontrar la misma mejora, no se habrá demostrado que el método sea más eficiente.

Una señal convincente sería que las oleadas grandes descubran mejoras reproducibles que no aparecían en las siete candidatas, que sobrevivan a la integración y mantengan cero regresiones. El resultado puede ser también negativo: si no mejora la tasa de descubrimiento, se reduce el tamaño de la búsqueda o se cambia la generación de hipótesis.

## 9. Riesgos y controles

| Riesgo | Control |
|---|---|
| Saturar Actions o límites API | Cola limitada, concurrencia configurable y oleadas |
| Candidatas duplicadas o cosméticas | Ficha de hipótesis, hash/diff y detección de duplicados |
| Sobreajuste a los 500 casos | Declarar la limitación; reservar validación disjunta para una fase independiente |
| Falsas mejoras por benchmark incompleto | 500/500, cuatro shards, checksum y SHA exacto |
| Regresiones ocultas por score neto | Comparación por ID y cero regresiones sobre aciertos de main |
| Conflictos al combinar ganadores | Rebenchmark obligatorio de cada integración |
| Promoción accidental | Permisos mínimos, sin merge/push y aprobación humana |
| Resultados difíciles de reproducir | Semillas, SHAs, configuración y artefactos conservados |

## 10. Entregables de cada ronda

Cada oleada debe dejar:
- manifiesto de candidatas con nombre de rama, hipótesis, semilla y SHA base;
- estado de cada puerta y motivo de descarte;
- scorecard comparable por candidata;
- lista de ganadores y no ganadores;
- informe de costes y capacidad del CI;
- PR(s) de integración solo si existe al menos un conjunto ganador compatible;
- conclusión explícita: escalar, mantener o reducir el tamaño de la búsqueda.

## 11. Condición de éxito del programa

El programa se considera útil cuando demuestra, en rondas repetibles, que la exploración amplia aumenta la probabilidad de encontrar mejoras reales por unidad de recursos, y que esas mejoras sobreviven a la integración con main sin regresiones.

**No se promete una mejora «absurda» ni un porcentaje concreto.** El éxito es descubrir una mejora medible, reproducible y segura; si no aparece, se publica el resultado negativo y se ajusta la estrategia en lugar de fingir una victoria.

## 12. Próximos pasos de implementación

1. Revisar el workflow de torneo actual, que nació para siete candidatas, y verificar sus límites reales de descubrimiento, matriz, concurrencia, artefactos y permisos.
2. Añadir un manifiesto de ronda y scorecard por ID para comparación pareada main/candidata.
3. Implementar primero el piloto de 10–16 candidatas, con concurrencia limitada.
4. Validar que el workflow no puede hacer merge ni escribir en main.
5. Medir el piloto frente a la referencia histórica de siete candidatas.
6. Escalar a 32, 64 y 100 solo si los datos justifican el coste y la infraestructura soporta el volumen.
7. Mantener la evaluación de la muestra primaria separada del ranking rutinario, conforme a la política vigente.

---

## Referencias internas

- [Política de evaluación externa](HOLDOUT_ONLY_EVALUATION_POLICY.md)
- [Torneo de siete hipótesis](EXPERIMENT_TOURNAMENT_2026-11.md)
- [Análisis de fallos del benchmark externo](EXTERNAL_BENCHMARK_FAILURE_ANALYSIS.md)
- [Registro de baseline](../benchmarks/holdout-record.json)
- [Workflow de torneo](../.github/workflows/seven-candidate-tournament.yml)


## 13. Orquestación disponible en la PR #315

La PR #315 también adapta el workflow `.github/workflows/seven-candidate-tournament.yml` para admitir lotes manuales de **16, 32, 64 o 100 candidatas**. El nombre histórico del archivo se conserva para no romper referencias existentes; el coordinador sigue ejecutándose una sola vez por despacho o push relevante a main.

Tras integrar la PR #315 en `main`, se podrá lanzar el workflow desde GitHub Actions con `workflow_dispatch` y elegir `cohort_size`. Para cada tamaño, el descubrimiento exige exactamente ese número de PRs abiertas, no draft, dirigidas a main y con ramas bajo el prefijo correspondiente:

| Lote | Prefijo obligatorio de ramas candidatas | PRs candidatas requeridas |
|---:|---|---:|
| 16 | `experiment-massive-16/` | 16 |
| 32 | `experiment-massive-32/` | 32 |
| 64 | `experiment-massive-64/` | 64 |
| 100 | `experiment-massive-100/` | 100 |

Cada despacho añade una ejecución de `main` como baseline en la misma matriz. Las candidatas se congelan por SHA, pasan por suite completa y benchmark externo, y se comparan por los mismos IDs. La concurrencia de pruebas unitarias se limita a 8 jobs y la del benchmark a 4 jobs para evitar lanzar 100 ejecuciones simultáneas sin control. El informe agregado se añade al resumen de Actions y, si se ha producido un ranking verificable, el job agregador lo incorpora al final de este documento mediante un commit de `github-actions[bot]` en main. El job agregador es el único que recibe permiso `contents: write`; los jobs que ejecutan candidatas no reciben ese permiso.

**Importante:** el workflow no genera código COBOL/Python aleatorio ni inventa candidatas. Cada una de las 212 PRs debe contener una mutación funcional, reproducible y revisable. Si no existe exactamente el número solicitado de PRs candidatas para un lote, el despacho falla de forma explícita en descubrimiento y no presenta un resultado parcial como torneo completo. La PR #315 contiene el protocolo y esta orquestación; todavía no contiene las 212 implementaciones candidatas ni activa los despachos hasta que se integre.


---

## 14. Reanudación 2026-11-04 — evaluación pareada obligatoria

### Estado inspeccionado

- `main` al iniciar esta iteración: `b63304e430ca45fa3d96910c2a867ef4aeb37a27`.
- Récord histórico persistente en `benchmarks/holdout_best.json`: **499/1.000 (49,9 %)**, primaria 249/500 y holdout 250/500, medido en el SHA `87eaba8043d6a7280db1902ad36ca41fb2a3885d` (run [#41602383991](https://github.com/orbitalronin94/cobol2py/actions/runs/41602383991)).
- No había ejecuciones activas al iniciar la revisión.
- El último intento del coordinador, [#41692990275](https://github.com/orbitalronin94/cobol2py/actions/runs/41692990275), falló en descubrimiento/salida antes de crear la matriz de pruebas o benchmark. El log muestra que `cohort_size` llegó vacío y que el JSON multilínea escrito directamente en `GITHUB_OUTPUT` fue rechazado (`Invalid format`). **Ese run no produjo puntuación.**

### Mejor resultado parcial encontrado

Los benchmarks individuales más altos de la cohorte masiva alcanzaron **251/500 (50,2 %) en holdout**, no un resultado combinado:

- PR #327, `STRING DELIMITED BY ZEROES`: [run #41703250168](https://github.com/orbitalronin94/cobol2py/actions/runs/41703250168).
- PR #332, estado 46 de `READ` después de EOF: [run #41701037354](https://github.com/orbitalronin94/cobol2py/actions/runs/41701037354).
- PR #326, modos mixtos de `OPEN`: [run #41700052067](https://github.com/orbitalronin94/cobol2py/actions/runs/41700052067).
- PR #328, offsets de modificación de referencia aritmética: [run #41697158085](https://github.com/orbitalronin94/cobol2py/actions/runs/41697158085).

Son mediciones completas de la mitad holdout sobre SHAs de candidata distintos. No se suman entre sí, no prueban cero regresiones y no actualizan el récord 499/1.000. Varias candidatas empatan en 251/500; la ganadora solo puede decidirse con comparación por ID contra el mismo baseline.

### Corrección del gate

El coordinador ahora debe:

1. Usar 16 como tamaño por defecto si un despacho no trae `cohort_size`, y rechazar tamaños fuera de 16/32/64/100.
2. Emitir el JSON de candidatas en una sola línea para que GitHub Actions lo acepte como output.
3. Descubrir también ramas `experiment-massive-N/` en los pushes de coordinación.
4. Ejecutar **primaria (skip=0, 500 casos) y holdout (skip=500, 500 casos)** para `main` y cada candidata, con el mismo archivo X-COBOL v2 y checksum.
5. Aceptar un resultado solo si ambos informes están completos, el SHA y la rama coinciden, la suite completa pasa y los 1.000 IDs coinciden con el baseline.
6. Calcular ganancias y regresiones por ID sobre las dos mitades. Una candidata solo queda cualificada para revisión humana si mejora el combinado y tiene cero regresiones en las 1.000 muestras.

El workflow no hace merge, no modifica `holdout_best.json` ni cambia corpus, selección, timeout o criterio exact-match. La prueba de contrato `tests/test_tournament_workflow.py` protege el default, el formato de output, las dos muestras y la puerta de cero regresiones.

**Pendiente de validación:** el siguiente run completo debe establecer primero el baseline pareado del `main` actual y comparar las 15 candidatas aún abiertas contra él. Hasta que los 32 shards (16 SHAs × 2 muestras) terminen, no se declara ganadora ni se promueve código.

## 16. PR #322 integrada antes de la evaluación pareada — 2026-11-04

PR #322 (`OPTIONAL sequential file OPEN`) fue fusionada por el propietario del repositorio a las 07:33:49Z, commit `725e32f8a55950727a8eb7def8d022ce2d77389e`. Su evidencia previa era **251/500 (50,2 %) solo en holdout**, sin comparación por ID contra main en el mismo run ni primaria pareada. Por tanto, esa cifra no es un nuevo récord combinado ni una validación de cero regresiones. No la atribuyo como mejora aceptada: el cambio queda dentro del nuevo baseline de main y se medirá allí.

El manifiesto conserva las 16 hipótesis originales, pero C001 (#322) queda marcado como integrada antes de la validación pareada. El torneo debe ejecutar main más las 15 candidatas aún abiertas. La prueba de contrato verifica esa composición; la puerta de resultados sigue exigiendo ambas mitades completas y cero regresiones en los 1.000 IDs. El registro histórico 499/1.000 permanece intacto hasta disponer de una nueva evaluación pareada completa y reproducible.