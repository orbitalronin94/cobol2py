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
| Python #14, último resultado completo analizado | `9d81975` | 168/500 (33,6 %) | 194/500 (38,8 %) | **362/1000 (36,2 %)** |

La última medición queda 13 programas por debajo del récord. El hito de recuperación es 375/1000; el objetivo aspiracional de la iteración concentrada sigue siendo 425/1000 (42,5 %), sin prometerlo antes de medirlo. Antes de atribuir cifras a `main`, registrar siempre el SHA exacto del workflow y confirmar que las dos mitades corresponden al mismo SHA.

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
