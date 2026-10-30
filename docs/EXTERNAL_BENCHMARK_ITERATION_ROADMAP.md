# Roadmap operativo de mejora del benchmark externo

**Fecha de corte:** 2026-10-29  
**Objetivo del proyecto:** mejorar la equivalencia real de COBOL → Python, sin alterar corpus, denominador ni criterio de aceptación. Este documento operacionaliza el roadmap de producto v1.0 del README; no lo sustituye.

## Métrica y referencias inmutables

La aprobación por caso exige coincidencia exacta de stdout y código de retorno frente a GnuCOBOL. El benchmark externo usa 500 programas en la muestra primaria y 500 en el holdout disjunto.

| Referencia | SHA corto | Primaria | Holdout | Total |
|---|---|---:|---:|---:|
| Mejor referencia conservadora | `2307c7b` | 178/500 (35,6 %) | 197/500 (39,4 %) | **375/1000 (37,5 %)** |
| Python #7 | `13d359c` | 165/500 (33,0 %) | 191/500 (38,2 %) | 356/1000 (35,6 %) |
| Python #12 | `8e5e2ec` | 168/500 (33,6 %) | 193/500 (38,6 %) | 361/1000 (36,1 %) |
| Python #14 | `9d81975` | 168/500 (33,6 %) | 194/500 (38,8 %) | 362/1000 (36,2 %) |
| Python #68 | `b807aae` | 188/500 (37,6 %) | 205/500 (41,0 %) | 393/1000 (39,3 %) |
| **Python #77 (PR #53)** | `402303b` | **192/500 (38,4 %)** | **208/500 (41,6 %)** | **400/1000 (40,0 %)** |

La #77 mejora en 7 casos (+0,70 puntos) respecto a la #68: +4 en primaria y +3 en holdout. El récord conservador histórico de 375/1000 queda superado por 25 casos. Para el objetivo aspiracional de 425/1000 (42,5 %) faltan 25 coincidencias. La #77 se midió en el SHA `402303b1e4c70b75c9c8931054de1b29ce50dae8` de la PR #53, todavía abierta: no atribuir esta puntuación a `main` hasta medir el SHA integrado. Confirmar siempre que las dos mitades corresponden al mismo SHA.

## Ingeniería inspirada en compiladores open source

La investigación comparativa y la propuesta de arquitectura incremental están en [`docs/OPEN_SOURCE_COMPILER_RESEARCH.md`](OPEN_SOURCE_COMPILER_RESEARCH.md). La primera aplicación será mejorar resolución de referencias y jerarquía de datos sin reescribir el parser ni mezclar varios cambios de semántica. La inspiración principal es la separación AST/ASG de ProLeap, el uso de GnuCOBOL como oráculo, el runtime de opensource COBOL 4J y la frontera AST→IR→codegen descrita por CobGo.

## Prioridad técnica

### P0 — Evitar regresiones de terminación y salida explosiva

Las comparaciones entre la referencia de 375/1000 y el último candidato muestran 21 regresiones y 8 ganancias: 14 regresiones en primaria y 7 en holdout. La categoría «programa traducido agotó el tiempo» subió de 56 a 80 casos; el límite de captura se alcanzó en 6 casos frente a 0 en la referencia.

Casos que dejaron de pasar y requieren reproducción antes de tocar reglas generales:

- Primaria: `fp201612-3-ae4424744f`, `p20161b-4871fdaff9`, `smp002-508ab1c516`, `conta-corrente-55f5a45a05`, `progr02t-ebdd706b74`, `colors-3cb74b9dc4`.
- Holdout: `smp001-ccd7110609`, `bds1003-12491860f2`, `gpa-calculator-bcfb8405ce`.

No desactivar timeouts ni aumentar límites para inflar puntuación. Determinar si el programa emitido tiene un bucle sin progreso, una condición alterada o salida infinita.

### P1 — Referencias, símbolos y estructuras de datos

El nombre generado/ausente `file_cobol_record_information_rec` sigue apareciendo en 41 informes de fallo (23 primaria, 18 holdout). Investigar el recorrido completo desde declaraciones/copybooks y jerarquía de datos hasta resolución de nombres. No crear variables globales ficticias ni valores por defecto solo para ocultar un `NameError`.

Los fallos de subíndices multidimensionales de `nc241a`, `nc2344-2` y `nc2414-2` muestran otro patrón concreto: el acceso a listas anidadas puede convertirse en acceso por clave de texto. Construir fixtures mínimos que separen declaración de tabla, dimensión, índices y referencia cualificada.

### P2 — Sintaxis y tokens COBOL residuales

Compilar el Python generado y agrupar errores por regla de traducción antes de cambiarla. Dos regresiones producen `NameError` para `at` en `clie-ea6fe390da` y `clic-f5b1f6c97a`; revisar la fuente y los tokens circundantes antes de concluir que comparten causa. Los errores de sintaxis deben convertirse en fixtures reproducibles.

### P3 — Diferencias semánticas de salida y retorno

Es la categoría individual más grande. Clasificar por causa verificable: relleno/truncamiento PIC, formato numérico y escalas, MOVE de grupos, STRING/UNSTRING, inicialización, EOF/FILE STATUS y código de retorno. Corregir una familia semántica cada vez, sin normalizar stdout ni cambiar la métrica.

### P4 — C y Rust

Mantener estos backends como métricas independientes. Usar sus rechazos clasificados para priorizar soporte de verbos y estructuras COBOL compartidas; no inferir mejora del benchmark externo Python a partir de la suite interna de 105 casos.

## Bucle de iteración obligatorio

Cada vuelta es una unidad pequeña, verificable y con salida registrada:

1. **Congelar la base:** SHA, ejecuciones y artefactos de primaria/holdout; confirmar el benchmark de referencia.
2. **Elegir una familia:** seleccionar una causa respaldada por traceback/diff y con varios casos potencialmente recuperables.
3. **Reproducir:** crear un fixture mínimo COBOL y guardar stdout/código de retorno de GnuCOBOL.
4. **Cambiar una sola causa raíz:** no mezclar limpieza, refactors y varias familias de errores.
5. **Probar:** suite unitaria, compilación de salida generada, pruebas diferenciales e invariantes de regresión.
6. **Medir:** ejecutar benchmark rápido si existe y después las dos mitades completas sobre el mismo SHA.
7. **Comparar por ID:** ganancias, regresiones, no cambios y diferencias de categoría; repetir casos no deterministas.
8. **Aceptar o revertir:** conservar solo si la evidencia respalda la hipótesis y las regresiones son entendidas. Una mejora en primaria que perjudique el holdout no se declara generalizada.
9. **Documentar:** actualizar esta hoja, el análisis de fallos y el README solo con cifras confirmadas.
10. **Repetir:** seleccionar la siguiente familia prioritaria. No cerrar una iteración solo porque CI terminó en verde.

## Puertas de cierre

- [ ] Suite completa y benchmark diferencial verdes.
- [ ] Primaria y holdout completos para el mismo SHA.
- [ ] Comparación caso por caso con la mejor referencia conservadora.
- [ ] Regresiones explicadas y sin cambios del criterio de evaluación.
- [ ] Resultados reproducibles y no afectados por cancelaciones entre pushes.
- [ ] README e informe de fallos sincronizados con los artefactos.
- [ ] Para declarar recuperado el récord: al menos 375/1000.
- [ ] Para declarar logrado el objetivo de +5 puntos: al menos 425/1000, con ambas mitades completas.

## Disciplina de ejecución

No lanzar una nueva modificación mientras los benchmarks necesarios para evaluar la modificación anterior sigan ejecutándose, salvo que la ejecución anterior haya fallado por infraestructura y se documente. Agrupar cambios solo cuando compartan una causa raíz demostrada. Mantener un registro de hipótesis, SHA, resultado esperado, resultado real y decisión. El proceso puede continuar iterativamente mientras haya evidencia y herramientas disponibles; nunca afirmar que un trabajo sigue ejecutándose en segundo plano si no hay una ejecución activa confirmada.


## Estado actualizado — 2026-10-29

### Iteración A: referencias cualificadas anidadas (PR #40)

- El workflow dedicado #16 dio 363/1000 (36,3 %) frente a 362/1000 en #14; la única ganancia fue `rock-paper-scissors-ad6321acf1`, que usa `FUNCTION RANDOM` y hora actual. No hubo regresiones, pero el cambio de pass/fail no es atribuible con seguridad al código.
- La ejecución dedicada #17 sobre el SHA más reciente de la PR sigue en curso. No declarar mejora ni fusionar basándose en +1 caso hasta comprobar ese resultado y la estabilidad del caso aleatorio.
- El workflow multilenguaje #621 da 362/1000 en una selección distinta; no mezclarlo con la serie del workflow dedicado.

### Iteración B: OCCURS tridimensional + REDEFINES (PR #41)

- El fixture reducido, inspirado en ProLeap NIST `NC234A.CBL`, fallaba antes del cambio: la escritura por la vista original no se veía en la vista `REDEFINES`.
- La implementación candidata calcula strides de cada dimensión y enruta ambas vistas a un buffer común. La suite de 292 pruebas pasa en Python 3.10–3.13; los workflows diferencial y multilenguaje interno han terminado correctamente.
- El workflow externo dedicado #21 está pendiente y el workflow de corpus externo #626 sigue en ejecución. **No hay todavía una puntuación externa que justifique conservar la modificación por el objetivo porcentual.**

### Disciplina de ejecución

Se inició la iteración B antes de que finalizara el workflow dedicado #17 de la iteración A, después de completar el corpus multilenguaje #621, que no mostró ningún cambio pass/fail para A. Esto es una desviación de la puerta de cierre original; no iniciar una tercera modificación hasta que los resultados oficiales de A y B estén completos y comparados por ID de caso.


## Estado actualizado — 2026-10-30 (PR #53)

### Iteración C: MOVE de grupos anidados, OCCURS y REDEFINES

- La PR [#53](https://github.com/orbitalronin94/cobol2py/pull/53) preserva grupos anidados en `MOVE`, evita contar dos veces almacenamiento compartido por `REDEFINES` y mantiene juntos los subíndices de referencias como `ENTRY (IDX-1, IDX-2)`. Añade regresiones para overlays anidados y `OCCURS` multidimensional, y mantiene sincronizados `cobol2py.py` y `web/index.html`.
- Benchmark externo Python [#77](https://github.com/orbitalronin94/cobol2py/actions/runs/41061218929), SHA `402303b1e4c70b75c9c8931054de1b29ce50dae8`: **192/500 primaria (38,40 %), 208/500 holdout (41,60 %), 400/1.000 combinado (40,00 %)**. Frente a #68: +4 primaria, +3 holdout, +7 total (+0,70 puntos). Ambas muestras terminaron completas en el mismo SHA.
- El workflow diferencial interno #1353 [pasó 105/105](https://github.com/orbitalronin94/cobol2py/actions/runs/41071645897) en el candidato final. Tras el merge, tests #1704, diferencial #1354 y multilenguaje #104 pasaron sobre `main` en el SHA `62d038bbe7bae7e212ff34e30c1f4c1fd020cd71`.
- La PR #53 se integró en `main` el 2026-10-30 mediante el merge `62d038bbe7bae7e212ff34e30c1f4c1fd020cd71`.
- Comparación por caso de #77 frente a #68: primaria 5 ganancias/1 regresión; holdout 4 ganancias/1 regresión. Las dos regresiones (`nc1404-2-20495d0582`, `nc140a-a1fdd01b63`) comparten una causa: los índices `S1`, `S21` y `S22` viven dentro de `GRP-SUB`, pero el generador emitía `s1`/`s21`/`s22` en lugar de `grp_sub['s1']` etc. La iteración D aborda esta resolución.
- Repetición #78, con el mismo código funcional, dio 399/1.000 (39,90 %) frente a 400/1.000 (40,00 %) en #77. El único cambio de caso fue `FunctionCall.cbl`, cuyo `WHEN-COMPILED` varía un segundo entre compilaciones. Registrar ambos resultados y no contar esa fluctuación como una regresión funcional del traductor.


## Estado actualizado — 2026-10-30 (Iteración D)

### Resolución de nombres de grupo usados como subíndices

- Evidencia: los artefactos de #77 muestran que `MOVE WRK1 TO ELEM1 (S1) ELEM2 (S21 S22)` genera `int(s1)`/`int(s21)`/`int(s22)`, aunque los campos COBOL están declarados dentro de `01 GRP-SUB` y se almacenan como `grp_sub['s1']`, etc. Resultado: `NameError` en `NC1404` y `NC140A`.
- Cambio propuesto en `normalize_data_reference.index_expression`: resolver un subíndice identificador con `normalize_data_reference(subscript, variable_map)` antes de convertirlo a entero. Aplicar la misma regla al camino de asignación overlay en `emit_assignment`; mantener sincronizados `cobol2py.py` y `web/index.html`.
- Añadir tests para `ELEM1(S1)` y para la tabla bidimensional `ELEM2(S21 S22)`. La rama de trabajo es `fix/nested-group-subscript-resolution`; no considerar la corrección validada hasta que la suite, el benchmark diferencial, browser smoke y el corpus externo completo terminen sobre el mismo SHA.
