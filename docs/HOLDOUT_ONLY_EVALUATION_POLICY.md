# Decisión de diseño: evaluación iterativa con una sola mitad del corpus

**Fecha:** 2026-10-31  
**Estado:** propuesta en PR; no cambiar `main` hasta revisar y validar los checks.

## Decisión

A partir de esta iteración, los workflows de evaluación de candidatos ejecutan únicamente los 500 programas de la segunda mitad determinista de X-COBOL v2 (`skip=500`, `target=500`). La mitad primaria (`skip=0`) deja de ejecutarse en el ciclo rutinario de optimización.

Motivos:
- reducir aproximadamente a la mitad el coste de ejecución del benchmark externo;
- evitar que el ciclo de trabajo siga optimizando contra dos subconjuntos del mismo corpus;
- mantener una selección de 500 casos y un criterio exacto reproducibles entre candidatos.

## Línea base y gate

- Referencia histórica completa de la PR #177: **480/1.000**, compuesta por 244/500 en la primaria y 236/500 en la segunda mitad.
- Línea base de evaluación iterativa: **236/500 (47,20 %)**.
- Un candidato solo supera el gate si obtiene **más de 236/500** en la mitad fija, con el checksum del archivo fuente verificado y los 500 casos ejecutables medidos.
- No se permite cambiar el corpus, el orden determinista, el denominador, las exclusiones, los límites de ejecución, ni el criterio de coincidencia (stdout byte a byte y código de retorno).

## Precisión metodológica: no llamarlo holdout intacto

El término *holdout* describe una muestra reservada que no se utiliza para ajustar decisiones. Si el equipo observa la puntuación de estos 500 programas en cada iteración y adapta el traductor a sus fallos, la muestra deja de ser independiente para medir generalización. En esta política se denomina **corpus fijo de evaluación**; conservar el nombre histórico de la mitad del dataset no la convierte en un holdout estadístico intacto.

Por tanto:
- la puntuación de 500 casos sirve para comparar candidatos en una evaluación fija;
- no debe presentarse como prueba de generalización a programas no observados;
- el objetivo de release histórico de 75 % en ambas mitades no puede declararse satisfecho a partir de esta evaluación única;
- cualquier anuncio debe identificar el tamaño de muestra y la limitación anterior.

## Coste y trade-off aceptado

La ejecución normal reduce de dos mitades de 500 a una mitad de 500. Se acepta perder la señal de regresión rutinaria en la primaria a cambio de menor coste; no se falsea el denominador ni se suman puntuaciones de ejecuciones distintas. Si una futura decisión de release necesita confirmar generalización, debe especificar por separado el presupuesto y la política de validación antes de ejecutar una muestra adicional.

## Evidencia exigida por PR

1. SHA exacto evaluado y artefacto JSON/Markdown del corpus fijo.
2. Verificación del checksum del archivo X-COBOL v2.
3. 500 casos medidos y conteo de coincidencias exactas.
4. Delta respecto a 236/500.
5. Tests unitarios/regresión del cambio.
6. Ninguna afirmación de mejora hasta que el artefacto de esa ejecución confirme la puntuación.
