# 30-seed failure-directed repair tournament

**Estado: bloqueado.** El baseline vigente de main ya se ha revalidado; la cohorte de 30 ramas aún no está lista para ejecutarse. La auditoría reproducible y sus enlaces se mantienen aquí y en [manifest.json](./manifest.json).

## Baseline vigente de main

- **261/500 (52,2%)** — [run 42844666181](https://github.com/orbitalronin94/cobol2py/actions/runs/42844666181).
- SHA de main medido: \`17f219460fb7a3e75bd462cd3be73faa17a1a64b\`.
- Corpus X-COBOL v2, MD5 esperado y verificado \`cbd974caed72b0836777dc2305928ed3\`.
- Comparación exacta: bytes de stdout y código de retorno del proceso frente a GnuCOBOL.
- Cuatro shards completos de 125 casos (\`skip=500,625,750,875\`), 500 IDs únicos, sin duplicados. Recuento: 63 + 54 + 71 + 73 = 261.

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

## Candidato en curso: EVALUATE ALSO

- [PR #365](https://github.com/orbitalronin94/cobol2py/pull/365) reconstruye la hipótesis de la semilla 10 sobre el main actual.
- Reproductor externo: NIST \`NC225A.CBL\`, caso \`nc225a-a777e5ee71\`; seis sujetos y selecciones \`WHEN ... ALSO ...\` en varias líneas, con \`NOT\`, \`ANY\` y sujetos booleanos.
- La suite completa del PR terminó verde en Python 3.10–3.13, Java, navegador y referencias/trazas GnuCOBOL: [run 43013196680](https://github.com/orbitalronin94/cobol2py/actions/runs/43013196680).
- El smoke externo [run 43013196679](https://github.com/orbitalronin94/cobol2py/actions/runs/43013196679) y el holdout de 500 [run 43013196673](https://github.com/orbitalronin94/cobol2py/actions/runs/43013196673) estaban en curso al cerrar esta auditoría. No hay puntuación ni IDs de ganancia/regresión publicados todavía; no fusionar.

## Cohorte de 16 candidatos

El intento más reciente, [run 42844557468](https://github.com/orbitalronin94/cobol2py/actions/runs/42844557468), falló en descubrimiento: el manifiesto esperaba 15 PRs no fusionadas y encontró solo 10. No se ejecutaron candidatos ni se generaron artifacts de torneo. Hay resultados históricos de candidatos individuales en PRs previas, pero no constituyen una comparación pareada vigente; no se vuelve a lanzar esa cohorte sin reconciliar sus PRs y SHA.

## Auditoría de las 30 semillas

- [PR #349](https://github.com/orbitalronin94/cobol2py/pull/349) integró el arnés de torneo; el workflow de main sigue siendo manual (\`workflow_dispatch\`) y no se ha despachado.
- Las 30 referencias originales existen, pero sus cabezas no son válidas contra el main actual. La semilla 10 del manifiesto ahora apunta al candidato reconstruido de [PR #365](https://github.com/orbitalronin94/cobol2py/pull/365); las otras 29 ramas siguen divergidas del SHA actual.
- Las semillas 11–15 carecen de cambios de traductor y de tests/reproducers. Otras ramas requieren rebase y revisión de que el diff corresponda a la hipótesis declarada.
- La preparación continúa **bloqueada**. No hay ganador ni promoción automática.

[PR #366](https://github.com/orbitalronin94/cobol2py/pull/366) propone endurecer el workflow antes de usarlo: SHA de candidato único y verificado, identidad del baseline, validación explícita de stdout/return-code, 500 IDs y checksum; cualquier artifact incompleto hace fallar el torneo completo en vez de publicar una clasificación parcial. Esa corrección todavía no está en main.

No se ha lanzado el torneo de 30: además de la preparación bloqueada, las herramientas disponibles permiten leer runs y artifacts, pero no exponer un dispatch de Actions.

## Siguiente hipótesis

**INSPECT TALLYING FOR ALL CHARACTERS.** El caso \`cbl0701v01statementinspect-31f6d501b1\` falla con \`NameError: characters\`; el código generado cuenta \`str(characters)\` en vez de sumar la longitud de \`WS-STR\`. El fuente reproducible es [CBL0701v01StatementInspect.cbl](https://github.com/mainframe-projects/CICS-Cobol/blob/master/CBL0701v01StatementInspect.cbl): \`WS-STR PIC X(15)\` y \`INSPECT WS-STR TALLYING WS-N FOR ALL CHARACTERS\`. La hipótesis es que \`CHARACTERS\` debe contar los 15 caracteres inspeccionados y acumularlos en el tally, sin alterar los otros formatos \`INSPECT ... TALLYING\`.
