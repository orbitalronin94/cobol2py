# 30-seed failure-directed repair tournament

**Estado: bloqueado.** El baseline vigente de main ya se ha revalidado; la cohorte de 30 ramas aún no está lista para ejecutarse. La auditoría reproducible y sus enlaces se mantienen aquí y en [manifest.json](./manifest.json).

## Baseline vigente de main

- **261/500 (52,2%)** — [run 42844666181](https://github.com/orbitalronin94/cobol2py/actions/runs/42844666181).
- SHA medido: \`17f219460fb7a3e75bd462cd3be73faa17a1a64b\`. Main actual: \`4d89d51b658c2f721afe0affdeb1a5ad61c9b65f\` tras mergear #366; el blob del traductor sigue idéntico (\`b2b7605281141cb7c9df50611dfce18b52322c2c\`), por lo que 261/500 continúa siendo el baseline de código.
- Corpus X-COBOL v2, MD5 esperado y verificado \`cbd974caed72b0836777dc2305928ed3\`.
- Comparación exacta: bytes de stdout y código de retorno del proceso frente a GnuCOBOL.
- Cuatro shards completos de 125 casos (\`skip=500,625,750,875\`), 500 IDs únicos, sin duplicados. Recuento: 63 + 54 + 71 + 73 = 261.
- El artifact histórico 42844666181 no contiene fingerprints del oráculo en 28 filas donde el traductor termina en timeout/error de sintaxis: el runner ejecuta GnuCOBOL primero, pero antes solo copiaba hash/longitud/código de retorno cuando la traducción llegaba a ejecutar Python. La rama #368 corrige esto y exige fingerprints completos para los 500 IDs; el baseline debe regenerarse desde main después de integrar el arreglo.

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

## Auditoría de las 30 semillas

- [PR #349](https://github.com/orbitalronin94/cobol2py/pull/349) integró el arnés de torneo. [PR #366](https://github.com/orbitalronin94/cobol2py/pull/366) ya está mergeada en main ([commit 4d89d51](https://github.com/orbitalronin94/cobol2py/commit/4d89d51b658c2f721afe0affdeb1a5ad61c9b65f)): verifica SHA únicos, identidad real del checkout, tests y evidencia completa por caso, y rechaza artifacts parciales.
- Las 30 ramas existen, pero las 30 están divergidas del main actual `4d89d51b658c2f721afe0affdeb1a5ad61c9b65f`. La semilla 10 también está divergida: su rama reconstruida conserva como merge-base el SHA anterior `17f219460fb7a3e75bd462cd3be73faa17a1a64b`.
- Las semillas 11–15 carecen de cambios de traductor y tests/reproducers. Las demás necesitan reconstrucción aislada desde el main actual y auditoría de que el diff implementa la hipótesis declarada.
- El workflow continúa manual (`workflow_dispatch`); no se ha lanzado un torneo de 30 semillas. La integración disponible permite inspeccionar Actions, pero no despachar el workflow directamente.
- La comparación por estado de pase no basta: el oráculo GnuCOBOL también puede variar entre ejecuciones. [PR #368](https://github.com/orbitalronin94/cobol2py/pull/368) exige `reference_stdout_sha256`, longitud de stdout y `reference_returncode` por cada ID; cualquier deriva invalida la elegibilidad aunque la puntuación bruta suba. Además, el workflow de main volverá a medir cuando cambie el runner o su imagen Docker.

No se ha promovido ningún candidato de la cohorte de 30. La preparación sigue **bloqueada** hasta reconstruir las 30 ramas y ejecutar suite + holdout completo con oráculo estable.

## Siguiente hipótesis

Separar la codificación del fuente COBOL de la codificación de stdout. El caso `cbl0701v01statementinspect-31f6d501b1` contiene un literal con byte CP850 `0xDA`; el lector UTF-8 actual lo convierte en U+FFFD y Python emite tres bytes UTF-8 en lugar del byte original. Crear un candidato aislado de detección/preservación de codificación (sin mezclarlo con INSPECT), añadir un reproducer binario CP850 y exigir el holdout completo con oráculo estable.
