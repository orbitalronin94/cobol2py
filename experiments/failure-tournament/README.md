# 30-seed failure-directed repair tournament

**Estado: bloqueado.** Main vigente: `b26cc0335708dab99737cc902c1d96186fec9f94`. El último baseline exacto completo es **262/500 (52,4%)** en [run 45283644192](https://github.com/orbitalronin94/cobol2py/actions/runs/45283644192), ejecutado sobre ese SHA. La cohorte de 30 ramas sigue sin estar preparada y no se ha despachado.

## Baseline vigente de main

- **262/500 (52,4%)** — [run 45283644192](https://github.com/orbitalronin94/cobol2py/actions/runs/45283644192), SHA exacto `b26cc0335708dab99737cc902c1d96186fec9f94`.
- Corpus X-COBOL v2, MD5 `cbd974caed72b0836777dc2305928ed3` verificado; `skip=500`, `target=500`; 500 IDs únicos, 500 hashes de fuente y 500 fingerprints GnuCOBOL completos; comparación exacta de stdout bytes y código de retorno.
- El baseline anterior sobre el mismo SHA, [run 45056162017](https://github.com/orbitalronin94/cobol2py/cobol2py/actions/runs/45056162017), obtuvo 263/500. Los 500 IDs y hashes de fuente coinciden. El único cambio de estado es `exec84-2-03eae98697`: pasó en 14,349943 s y falló por timeout de traducción a 20,003706 s en la ejecución nueva. Es variación de tiempo alrededor del límite de 20 s, no una regresión de candidato. Se conserva 263/500 como medición anterior; **262/500 es la última medición exacta vigente**.
- Doce fingerprints stdout de GnuCOBOL cambiaron entre ambas ejecuciones independientes: `cob-simpleinventory-6af451140a`, `collatz-6e335e6eda`, `date1-f31ce2734d`, `intrdate-0517c3d81c`, `pgm-f2e440bd10`, `progcob03-dd6c82c5dc`, `progcob17-6100f77c6a`, `progcobtempodecasaestruturado-930b4ab770`, `pullydis-9e45af6c84`, `randombingo-e50339cc12`, `randomnumbers-d8fc7ee85b`, `rolldice-08e3de1a0e`. El comparador debe seguir congelando el oráculo de main dentro de cada ejecución y no mezclar referencias de distintas corridas.
- La referencia histórica de main **257/500 (51,4%)** permanece en [run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592). El **258/500** de [run 42266714599](https://github.com/orbitalronin94/cobol2py/actions/runs/42266714599) pertenece a una rama experimental y no es main.
- [Run diario 45283644192](https://github.com/orbitalronin94/cobol2py/actions/runs/45283644192) completó baseline y ranking. La cola de candidatos estaba vacía: no hubo candidatos, ganancias, regresiones ni ganador.

## Readiness del torneo de 30 semillas

- Las 30 referencias del manifiesto existen y tienen 30 SHA distintos; las 30 están divergidas respecto a main `b26cc0335708dab99737cc902c1d96186fec9f94`, ninguna es ahead-only.
- Semillas 1–10: cambios de traductor/tests, pero ramas obsoletas.
- Semillas 11–15: sin cambios de traductor ni tests/reproducers.
- Semillas 16–30: cambios mezclados con workflows, benchmarks o documentación.
- [PR #349](https://github.com/orbitalronin94/cobol2py/pull/349) añadió el arnés de torneo, no 30 implementaciones listas.
- `.github/workflows/failure-directed-30-seed-tournament.yml` solo permite `workflow_dispatch`, exige `readiness.status == "ready"`, verifica SHA únicos, ancestry ahead-only, cambios aislados de traductor/tests y artifacts completos. La readiness sigue bloqueada; **no se ha iniciado el torneo**.
- La cohorte histórica de 16 candidatos no se duplica: sus artifacts ya cubren UNSTRING TALLYING IN, WRITE FROM literal, READ-after-EOF, OPEN mixto, INSPECT REPLACING, reference modification aritmética y STRING ZEROES.

## Última candidata emparejada — PR #371

- [PR #371](https://github.com/orbitalronin94/cobol2py/pull/371), lectura de registros `ORGANIZATION SEQUENTIAL` de ancho fijo; head `1a9424f6b59d18ec93b9dc1b38a32afde8f00dbc`, merge ref evaluada `ebba3a79baf6d03f7d5fe5c16282f723ac3f6005`.
- [Torneo emparejado 44599918790](https://github.com/orbitalronin94/cobol2py/actions/runs/44599918790): main **263/500**, candidata **262/500**, 500 IDs comparables.
- Ganancias: ninguna. Regresión: `exec84-2-03eae98697`.
- Deriva diagnóstica del oráculo en nueve IDs: `cob-simpleinventory-6af451140a`, `collatz-6e335e6eda`, `date1-f31ce2734d`, `intrdate-0517c3d81c`, `pullydis-9e45af6c84`, `randombingo-e50339cc12`, `randomnumbers-d8fc7ee85b`, `rock-paper-scissors-ad6321acf1`, `rolldice-08e3de1a0e`.
- La ejecución anterior [44527688670](https://github.com/orbitalronin94/cobol2py/actions/runs/44527688670) mostró una ganancia aparente de timeout que no se reprodujo en la nueva comparación. PR #371 cerrada sin merge; no hay ganador.

## Récord histórico separado

- **257/500 (51,4%)** sigue siendo la referencia histórica de main: [run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592), SHA \`393b6f5d98eb0a0f2f1af41eb5d937e6bb274d28\`.
- **258/500 (51,6%)** en [run 42272058313](https://github.com/orbitalronin94/cobol2py/actions/runs/42272058313) fue una re-medición posterior de main con una variación de timeout en un caso; no sustituye el récord histórico.
- **258/500** en [run 42266714599](https://github.com/orbitalronin94/cobol2py/actions/runs/42266714599) fue una rama experimental, no main.

## Candidatos comparados contra el holdout vigente

| PR | Hipótesis | Resultado | Ganancias | Regresiones | Decisión |
|---|---|---:|---:|---:|---|
| [#359](https://github.com/orbitalronin94/cobol2py/pull/359) | UNSTRING TALLYING IN acumulativo | 260/500 | 0 | 1 | No elegible |
| [#362](https://github.com/orbitalronin94/cobol2py/pull/362) | READ SEQUENTIAL de ancho fijo | 261/500 | 0 | 0 | No elegible: no añade casos |

La regresión de #359 es \`exec84-2-03eae98697\`. #362 conserva el mismo conjunto de aprobados, pero no aporta una ganancia nueva. Runs de candidato: [42839228540](https://github.com/orbitalronin94/cobol2py/actions/runs/42839228540) y [42839464387](https://github.com/orbitalronin94/cobol2py/actions/runs/42839464387). Ambos se compararon por los mismos 500 IDs, checksum, selección y definición de pase que el baseline actual; ninguno cumple el gate de promoción.

## Candidato EVALUATE ALSO — cerrado sin merge

- [PR #365](https://github.com/orbitalronin94/cobol2py/pull/365) pasó suite, smoke y holdout: [tests 43013196680](https://github.com/orbitalronin94/cobol2py/actions/runs/43013196680), [smoke 43013196679](https://github.com/orbitalronin94/cobol2py/actions/runs/43013196679), [holdout 43013196673](https://github.com/orbitalronin94/cobol2py/actions/runs/43013196673).
- Puntuación bruta: 262/500 frente a 261/500. Ganancia aparente: `rock-paper-scissors-ad6321acf1`; regresiones brutas: ninguna.
- No es una mejora válida: 12 casos cambiaron su oráculo GnuCOBOL entre ejecuciones (hash de stdout o código de retorno). El único pase aparente pertenece a uno de esos casos. Por tanto, no hay ganancia estable ni candidato elegible.
- El reproductor motivador `nc225a-a777e5ee71` continúa fallando con la condición generada inválida. [PR #365](https://github.com/orbitalronin94/cobol2py/pull/365) se cerró sin merge.

## Candidato INSPECT CHARACTERS — sin ganancia exacta

- [PR #367](https://github.com/orbitalronin94/cobol2py/pull/367) pasó suite [43022570224](https://github.com/orbitalronin94/cobol2py/actions/runs/43022570224), smoke [43022570165](https://github.com/orbitalronin94/cobol2py/actions/runs/43022570165) y holdout completo [43022570154](https://github.com/orbitalronin94/cobol2py/actions/runs/43022570154).
- Resultado: **261/500**, 0 ganancias y 0 regresiones por los mismos 500 IDs y hashes de fuente; no supera el gate de +1.
- El caso motivador `cbl0701v01statementinspect-31f6d501b1` ya no lanza `NameError`: el tally de caracteres da 15 y el código de retorno coincide. Aun así falla por bytes de salida: GnuCOBOL emite el byte CP850 `0xDA` en «NÚMERO», mientras Python produce `EF BF BD` por reemplazar el byte de origen no UTF-8. La diferencia es de codificación del fuente/salida, no del tally.
- También aparecen 12 IDs con deriva del oráculo entre baseline y candidata (la misma cohorte observada en #365). No se promueve; #367 queda abierto sin merge mientras se separa y prueba la hipótesis de codificación.

## Cohorte de 16 candidatos

El intento más reciente, [run 42844557468](https://github.com/orbitalronin94/cobol2py/actions/runs/42844557468), falló en descubrimiento: el manifiesto esperaba 15 PRs no fusionadas y encontró solo 10. No se ejecutaron candidatos ni se generaron artifacts de torneo. Hay resultados históricos de candidatos individuales en PRs previas, pero no constituyen una comparación pareada vigente; no se vuelve a lanzar esa cohorte sin reconciliar sus PRs y SHA.

## Auditoría de las 30 semillas — 20 de noviembre de 2026

- Las 30 referencias declaradas existen y las 30 comparaciones contra main `4238c8da8aec9d7a1a2de6fc1abcf04ddd6c3133` están divergidas; ninguna es ahead-only.
- Semillas 1–10: traductor y tests aislados, pero entre 17 y 213 commits por detrás.
- Semillas 11–15: solo cambios de workflow/documentación; sin implementación del traductor ni tests/reproducer.
- Semillas 16–30: cambios de traductor/tests mezclados con workflows, benchmarks o documentación; entre 253 y 593 commits por detrás.
- El workflow [failure-directed-30-seed-tournament.yml](https://github.com/orbitalronin94/cobol2py/blob/main/.github/workflows/failure-directed-30-seed-tournament.yml) sigue siendo manual (`workflow_dispatch`) y bloquea mientras `readiness.status != ready`. No se ha iniciado ningún torneo de 30 semillas.
- La discovery vuelve a comprobar 30 SHA únicos, ramas ahead-only, tests/reproducers, aislamiento de archivos y artifacts completos antes de ejecutar.

La cohorte antigua de 16 candidatos no se repite: sus artifacts ya cubren UNSTRING TALLYING IN, WRITE FROM literal, READ después de EOF, OPEN mixto, INSPECT REPLACING, reference modification aritmética y STRING ZEROES. Sus resultados históricos no son ganadores y no justifican volver a gastar 500 casos en las mismas hipótesis.

## Hipótesis pendiente separada: codificación CP850

El caso `cbl0701v01statementinspect-31f6d501b1` sigue siendo una hipótesis independiente: GnuCOBOL emite el byte CP850 `0xDA` y la salida Python observada fue `EF BF BD`. No se duplica con la candidata actual. La prioridad inmediata tras el descarte de PR #400 pasa a ser `DIVIDE ... ON SIZE ERROR` / `NOT ON SIZE ERROR`.

## 2026-11-20 current-main audit — actualización final

- Main exacto: `399b55e77d47cdd15367a9b17c3b116a962a39c7`. Baseline completo [44800200895](https://github.com/orbitalronin94/cobol2py/actions/runs/44800200895): **263/500 (52,6%)**, X-COBOL v2 MD5 `cbd974caed72b0836777dc2305928ed3`, `skip=500`, `target=500`, 500 IDs y 500 fingerprints GnuCOBOL completos. El blob del traductor es `4a7562627d161580470f1b0522cda0b094f635b0`.
- PR #400 se cerró sin merge. El torneo emparejado oficial [44731467437](https://github.com/orbitalronin94/cobol2py/actions/runs/44731467437) congeló ese SHA de main y completó 500/500 casos: **main 263/500, candidata 261/500**, 0 ganancias y 2 regresiones exactas: `exec84-2-03eae98697` y `nc243a-04e83cd675`. El comparador verificó 500 IDs y 500 hashes de fuente idénticos, con el oráculo GnuCOBOL congelado de main.
- La ejecución independiente en cuatro shards [44731467420](https://github.com/orbitalronin94/cobol2py/actions/runs/44731467420) produjo un pase aparente de `exec84-2-03eae98697`; no se reprodujo en el holdout oficial completo. No se cuenta como ganancia. El resultado oficial tiene 9 fingerprints GnuCOBOL variables en la ejecución candidata: `cob-simpleinventory-6af451140a`, `collatz-6e335e6eda`, `date1-f31ce2734d`, `intrdate-0517c3d81c`, `pullydis-9e45af6c84`, `randombingo-e50339cc12`, `randomnumbers-d8fc7ee85b`, `rock-paper-scissors-ad6321acf1`, `rolldice-08e3de1a0e`. La puntuación se calculó contra los fingerprints congelados de main.
- Los motivadores `nc203a-dc7f80e633` y `nc172a-3a5109e496` continúan fallando. El problema no es el patrón de nombres numéricos: el sufijo `ON SIZE ERROR` / `NOT ON SIZE ERROR` hace que no encaje el parser de `DIVIDE ... GIVING`, que cae al camino de receptores `INTO` y genera asignaciones inválidas como `100 = ...` y `100.50 = ...`. PR #400 no se fusiona.
- PR #401 actualiza la competición diaria/push para descubrir únicamente las PRs aprobadas en `current_main_pr_tournament.candidate_queue`. No barre todas las PRs abiertas: así evita duplicar hipótesis ya cubiertas por los artifacts de la cohorte antigua de 16 y por ramas históricas. La cola está vacía tras cerrar #400, por lo que el siguiente ciclo será baseline-only hasta que se encole una candidata aislada. La PR solo toca workflow, manifiesto, README y tests de infraestructura; no cambia el traductor.
- Auditoría renovada el 2026-11-21 de las 30 semillas contra main `399b55e`: **30/30 referencias existentes, 30 SHA distintos, 30/30 divergidas, 0 ahead-only**. Semillas 11–15 carecen de cambios de traductor y tests; semillas 16–30 incluyen archivos ajenos de workflow/benchmark/documentación. Readiness sigue bloqueada; no se ha iniciado el torneo de 30 semillas.
- La cohorte antigua de 16 no se repite: sus artefactos históricos ya cubren UNSTRING TALLYING IN, WRITE FROM literal, READ tras EOF, OPEN mixto, INSPECT REPLACING, reference modification aritmética y STRING ZEROES. No hay un torneo completo de 16 con ganador verificable.
- **PR #402 — DIVIDE SIZE ERROR:** evaluación oficial terminada en [run 44901501025](https://github.com/orbitalronin94/cobol2py/actions/runs/44901501025). Main 263/500, candidata 263/500, 500 IDs y hashes de fuente comparables, 0 ganancias y 0 regresiones. No elegible por falta de +1; cerrada sin merge. Los motivadores `nc203a-dc7f80e633` y `nc172a-3a5109e496` siguen fallando: `UnboundLocalError` en el receptor `giving` y `ZeroDivisionError` respectivamente. Siete derivas de oráculo fueron diagnósticas, no ganancias.


## 2026-11-22 — remeasurement and PR #402 decision

- Main sigue en `399b55e77d47cdd15367a9b17c3b116a962a39c7`. La repetición baseline-only [run 44933960078](https://github.com/orbitalronin94/cobol2py/actions/runs/44933960078) terminó correctamente: **263/500 (52,6%)**, X-COBOL v2 MD5 `cbd974caed72b0836777dc2305928ed3`, `skip=500`, `target=500`, 500 IDs únicos y 500 fingerprints GnuCOBOL completos. El traductor mantiene blob `4a7562627d161580470f1b0522cda0b094f635b0`.
- La evaluación emparejada oficial de [PR #402](https://github.com/orbitalronin94/cobol2py/pull/402) terminó en [run 44901501025](https://github.com/orbitalronin94/cobol2py/actions/runs/44901501025): main **263/500**, candidata **263/500**, 500/500 IDs comparables y hashes de fuente coincidentes, **0 nuevas aprobaciones y 0 regresiones**. No es elegible: el gate exige al menos +1 caso. No se fusiona; PR #402 se cerró sin merge.
- Siete fingerprints GnuCOBOL cambiaron en la ejecución de la candidata: `cob-simpleinventory-6af451140a`, `collatz-6e335e6eda`, `date1-f31ce2734d`, `intrdate-0517c3d81c`, `pullydis-9e45af6c84`, `randombingo-e50339cc12` y `randomnumbers-d8fc7ee85b`. Son deriva diagnóstica; la puntuación se calculó contra el oráculo congelado de main, no contra esas nuevas referencias.
- El artifact de candidata confirma que los dos motivadores no se arreglaron: `nc203a-dc7f80e633` termina con `UnboundLocalError` en la línea generada 740 (`giving = int(float(giving) / float(_cobol_divide_divisor))`); `nc172a-3a5109e496` termina con `ZeroDivisionError` en la línea 1374. La siguiente revisión debe corregir la resolución del receptor/variable de `DIVIDE ... GIVING` y el control del divisor cero antes de reabrir esta familia.
- La cola `current_main_pr_tournament.candidate_queue` permanece vacía. La ejecución programada [44933960078](https://github.com/orbitalronin94/cobol2py/actions/runs/44933960078) fue correctamente baseline-only; no se barrió ni duplicó la cohorte histórica de 16.
- El torneo de 30 semillas sigue bloqueado: 30 referencias existentes y distintas, pero 30 ramas divergidas, ninguna ahead-only; semillas 11–15 carecen de cambios de traductor/tests y 16–30 contienen rutas ajenas. No se ha iniciado.


## Legacy 105-case PR screen — diagnostic only

`.github/workflows/pending-pr-main-competition.yml` was an older push-triggered matrix over a fixed list of ten historical PRs (241, 242, 243, 259–265), using `benchmarks/cases.json` and 105 cases. It is not the external X-COBOL v2 holdout, does not compare the required fixed 500 IDs/fingerprints, and must never be used for candidate promotion. The merge of infrastructure PR #401 triggered [run 45018142264](https://github.com/orbitalronin94/cobol2py/actions/runs/45018142264); this already-started legacy run is diagnostic only. PR #403 has merged and changed the workflow to manual `workflow_dispatch`; future main pushes no longer repeat the stale 10-PR screen. Its PR checks (manifest, tests, and 50-case smoke) all passed. The authoritative path remains `current-main-pr-tournament.yml` with the manifest queue and exact 500-case casewise gate.


## Main al inicio de auditoría y re-medición exacta pendiente — 2026-11-22

- Main al abrir esta auditoría: `9fb72b514c74cef4b5fb10d01b4d0110e9e985fc`; PR #403 se fusionó para retirar el disparo automático del screening legado de 105 casos. No tocó el traductor. PR #404 tiene este SHA como base y, al fusionarse, creará un nuevo SHA de main.
- Los checks del PR #403 terminaron correctamente: [manifiesto 45018537217](https://github.com/orbitalronin94/cobol2py/actions/runs/45018537217), [tests 45018537273](https://github.com/orbitalronin94/cobol2py/actions/runs/45018537273), [smoke COBOL 45018537218](https://github.com/orbitalronin94/cobol2py/actions/runs/45018537218). Los checks post-merge también pasaron: [manifiesto 45019320370](https://github.com/orbitalronin94/cobol2py/actions/runs/45019320370), [tests 45019320352](https://github.com/orbitalronin94/cobol2py/actions/runs/45019320352).
- El screening legado [45018142264](https://github.com/orbitalronin94/cobol2py/actions/runs/45018142264) fue un smoke diagnóstico de 105 casos, no una comparación promocionable. Desde PR #403 solo se ejecutará manualmente.
- La última puntuación completa sigue siendo 263/500 en `399b55e77d47cdd15367a9b17c3b116a962a39c7`. El blob del traductor es idéntico en `9fb72b514c74cef4b5fb10d01b4d0110e9e985fc`, pero la cifra no se etiqueta como exacta para ese SHA. PR #404 dejará en cola un baseline-only para el SHA que produzca su merge.

## Auditoría actualizada de las 30 semillas — 2026-11-22

- Comparación contra `9fb72b514c74cef4b5fb10d01b4d0110e9e985fc`: 30/30 ramas existen, 30 heads distintos, 30 divergidas, 0 ahead-only. No se ha iniciado el torneo.
- Semillas 1–10: contienen traductor, pruebas y sincronización web, pero están obsoletas (20–216 commits por detrás). Deben reconstruirse desde main antes de competir.
- Semillas 11–15: solo cambios de workflow/documentación; no tienen cambios de traductor ni pruebas.
- Semillas 16–30: contienen cambios de traductor/pruebas, pero mezclados con workflows, benchmarks o documentación no permitidos.
- Existe una referencia adicional fuera del manifiesto: `experiment-failure-seed/10-syntax-evaluate-also`.
- La cohorte de 16 no se repite; sus artifacts ya cubren UNSTRING TALLYING IN, WRITE FROM literal, READ tras EOF, OPEN mixto, INSPECT REPLACING, reference modification aritmética y STRING ZEROES.

## Siguiente hipótesis: SEARCH ALL sobre tablas anidadas

El baseline 44933960078 contiene fallos nuevos no cubiertos por la cohorte antigua de 16:

- `nc233a-933ce1010e` y `nc2334-2-4c65f37e93`: `KeyError` al generar la clave de búsqueda de una tabla multidimensional.
- `nc233a-aed140c18a`: misma familia de acceso a tabla anidada.
- `nc235a-51f79a11be`: fallo de tipo en la condición generada de SEARCH ALL.
- `nc238a-715c9f78af` y `nc238a-64f4610536`: `UnboundLocalError` de índice de búsqueda.

La implementación actual de SEARCH ALL asume una referencia de clave de una sola dimensión y construye el acceso como `table[index][key]`. La próxima candidata debe preservar todos los subíndices anidados y sustituir solo el índice controlado por SEARCH; se añadirá primero un reproducer NIST fijo y se evaluará como candidata aislada.


## Re-medición exacta de main — run 45018142254

- Main medido: `585bb618373189c657fd5cec43671b6ebb3c9e0e`; [run 45018142254](https://github.com/orbitalronin94/cobol2py/actions/runs/45018142254) completó el job **Current main — 500 holdout cases** y el ranking final. El artifact `pr-tournament-baseline-45018142254` contiene 500 resultados, 500 IDs únicos, 500 fingerprints GnuCOBOL completos, MD5 `cbd974caed72b0836777dc2305928ed3`, 263 aprobados y 237 fallidos. El resumen final registra `baseline_sha=585bb618373189c657fd5cec43671b6ebb3c9e0e`, 500 probados, sin candidatos y sin ganador.
- Main al inicio de esta auditoría: `9fb72b514c74cef4b5fb10d01b4d0110e9e985fc`. Su blob de traductor coincide exactamente con el medido (`4a7562627d161580470f1b0522cda0b094f635b0`); PR #403 solo cambió el workflow legado y documentación. Por ello 263/500 es code-equivalent para ese main, pero no se etiqueta como una ejecución exacta sobre `9fb72b514c74cef4b5fb10d01b4d0110e9e985fc`.
- Comparando las dos mediciones completas 44933960078 y 45018142254: mismos 500 IDs, mismos 500 hashes de fuente y misma puntuación 263/500. Hubo 13 fingerprints stdout de GnuCOBOL distintos entre ejecuciones independientes; dos salidas del traductor también variaron en programas terminados por timeout. No hubo cambios de estado aprobado/fallido. Son derivas inter-ejecución, no ganancias ni regresiones de una candidata. El torneo debe seguir congelando el oráculo de main dentro de cada ejecución.

## 2026-11-23 — exact main baseline and SEARCH ALL candidate decision

- Exact main SHA: `b26cc0335708dab99737cc902c1d96186fec9f94`.
- [Run 45056162017](https://github.com/orbitalronin94/cobol2py/actions/runs/45056162017) completed successfully on that exact SHA. Its baseline artifact contains 500/500 unique IDs and complete GnuCOBOL fingerprints; X-COBOL v2 MD5 `cbd974caed72b0836777dc2305928ed3` verified, `skip=500`, `target=500`, exact stdout bytes and process return code: **263/500 (52.6%)**. The historical main reference remains 257/500 in [run 42268813592](https://github.com/orbitalronin94/cobol2py/actions/runs/42268813592); 258/500 in [run 42266714599](https://github.com/orbitalronin94/cobol2py/actions/runs/42266714599) remains experimental only.
- PR #405 ([SEARCH ALL nested OCCURS](https://github.com/orbitalronin94/cobol2py/pull/405)) passed its unit suite and completed paired 500-case run [45022022053](https://github.com/orbitalronin94/cobol2py/actions/runs/45022022053). The original frozen comparison reported main 263/500, candidate 264/500, 500 comparable IDs/source hashes, one apparent new pass (`exec84-2-03eae98697`) and zero regressions; the candidate artifact itself reported 263/500 because its own GnuCOBOL references drifted on nine IDs.
- The apparent +1 is not reproducible. A second exact-main run on the same SHA, [45056162017](https://github.com/orbitalronin94/cobol2py/actions/runs/45056162017), passes `exec84-2-03eae98697` on main (14.349943 s, no translator timeout); the earlier paired baseline had timed out at 20.004698 s. Re-scoring the candidate output against the later exact-main oracle gives 263/500, **0 gains and 0 regressions**. The only apparent gain was timeout-boundary variance, not a SEARCH ALL improvement.
- All six motivating SEARCH ALL cases still fail in the candidate artifact with return code 1 and stdout length 0: `nc233a-933ce1010e`, `nc2334-2-4c65f37e93`, `nc233a-aed140c18a`, `nc235a-51f79a11be`, `nc238a-715c9f78af`, `nc238a-64f4610536`. The report does not include stderr or exception-class fields, so no Python exception type is asserted. PR #405 was closed without merge; no translator winner.
- Fresh 2026-11-23 audit against `b26cc0335708dab99737cc902c1d96186fec9f94`: all 30 manifest branches exist, have 30 distinct heads, all 30 are diverged, and 0 are ahead-only. Seeds 1–10 have translator/tests but are stale; seeds 11–15 have no translator/tests (workflow/docs only); seeds 16–30 mix translator/tests with unrelated workflow, benchmark or documentation paths. An extra unmanifested `10-syntax-evaluate-also` ref remains. Readiness stays blocked; the 30-seed workflow is manual-only and has not been dispatched. PR #349 added the harness, not 30 completed implementations.
- The old 16-candidate artifacts are not repeated; they already cover the known UNSTRING, WRITE FROM, READ-after-EOF, OPEN, INSPECT, reference-modification and STRING ZEROES families. The next SEARCH ALL revision must preserve the full nested storage path and resolve the key field path separately from the searched dimension; it must first fix the six reproducer exceptions before another 500-case competition.
