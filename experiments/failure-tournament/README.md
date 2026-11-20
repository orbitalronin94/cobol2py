# 30-seed failure-directed repair tournament

**Estado: bloqueado.** El baseline vigente de main ya se ha revalidado; la cohorte de 30 ramas aún no está lista para ejecutarse. La auditoría reproducible y sus enlaces se mantienen aquí y en [manifest.json](./manifest.json).

## Baseline vigente de main

- **263/500 (52,6%)** — [run 44599918790](https://github.com/orbitalronin94/cobol2py/actions/runs/44599918790), ejecutado sobre el SHA exacto `4238c8da8aec9d7a1a2de6fc1abcf04ddd6c3133`.
- Traductor: `4a7562627d161580470f1b0522cda0b094f635b0`; 500 IDs únicos, 500 fingerprints completos de GnuCOBOL.
- Corpus X-COBOL v2, MD5 esperado y verificado `cbd974caed72b0836777dc2305928ed3`.
- `skip=500`, `target=500`, comparación exacta de stdout bytes y código de retorno.
- Un único reporte completo de 500 casos; 263 aprobados y 237 fallidos.

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

## Siguiente hipótesis

Reabrir de forma aislada el caso `cbl0701v01statementinspect-31f6d501b1`: GnuCOBOL emite el byte CP850 `0xDA`, mientras el resultado Python observado fue `EF BF BD`. Main ya contiene `decode_cobol_source` y `apply_cobol_output_encoding`; por tanto, antes de añadir otro parche hay que inspeccionar el fuente binario exacto, el encoding detectado y el flujo de stdout del proceso generado. El nuevo reproducer debe comparar bytes, no texto Unicode. No crear una candidata hasta localizar el punto exacto de la conversión.

## 2026-11-20 current-main audit

- Main is `399b55e77d47cdd15367a9b17c3b116a962a39c7`. The merge since the last complete baseline changed only the manifest, this README and manifest tests; the translator blob is unchanged.
- The last complete exact baseline remains **263/500 (52.6%)**, run [44599918790](https://github.com/orbitalronin94/cobol2py/actions/runs/44599918790), frozen on `4238c8da8aec9d7a1a2de6fc1abcf04ddd6c3133`. Exact remeasurement on `399b55e` is running in [44730370716](https://github.com/orbitalronin94/cobol2py/actions/runs/44730370716); the paired evaluation also freezes this SHA in [44731467437](https://github.com/orbitalronin94/cobol2py/actions/runs/44731467437).
- [PR #400](https://github.com/orbitalronin94/cobol2py/pull/400) isolates digit-leading COBOL data names in `DIVIDE ... GIVING`. The fixed report identifies `nc203a-dc7f80e633` and `nc172a-3a5109e496` as generated-Python syntax failures because the shared data-reference pattern rejects names such as `25ANS` and `25REM`. Its complete unit suite passed in [44731467416](https://github.com/orbitalronin94/cobol2py/actions/runs/44731467416), and the deterministic COBOL smoke passed in [44731467364](https://github.com/orbitalronin94/cobol2py/actions/runs/44731467364). The paired 500-case result is pending; no gains or regressions are claimed yet.
- [PR #401](https://github.com/orbitalronin94/cobol2py/pull/401) makes scheduled/push tournament runs discover all open eligible PRs instead of defaulting to closed PR #371. It also refreshes this 30-seed audit. Its manifest check passed in [44732753441](https://github.com/orbitalronin94/cobol2py/actions/runs/44732753441); unit tests passed in [44732753365](https://github.com/orbitalronin94/cobol2py/actions/runs/44732753365). Smoke remains in progress.
- The 30 manifest branches were re-compared against main `399b55e`: **30/30 exist, 30 distinct head SHAs, 30/30 diverged, 0 ahead-only**. Seeds 11–15 have no translator/test changes; seeds 16–30 contain unrelated workflow/benchmark/documentation paths. The 30-seed workflow remains manual and blocked; no tournament was dispatched.
- The old 16-candidate workflow still has no valid full-holdout result. The recent [run 44730370627](https://github.com/orbitalronin94/cobol2py/actions/runs/44730370627) produced 105-case auxiliary reports, not a 500-case paired holdout, so it is not used as promotion evidence.

Historical main score 257/500 in run 42268813592 and the experimental 258/500 run 42266714599 remain separate from the current baseline record.
