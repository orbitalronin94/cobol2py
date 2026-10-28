# cobol2py

> Traductor mínimo de COBOL a Python. Un archivo. Cero dependencias. Solo stdlib.

`cobol2py` nació como un traductor pequeño y autónomo de un archivo COBOL a Python legible. Después, el proyecto se amplió con un **agente inicial de análisis y planificación para sistemas empresariales multiarchivo** que ayuda a entender programas relacionados, copybooks, JCL y SQL antes de planificar una modernización. Son dos herramientas relacionadas, pero independientes: puedes usar el traductor sin el agente, y ejecutar el agente sin traducir código. El agente todavía no es un migrador autónomo ni promete equivalencia completa.

La traducción busca **leerse** y, para el subconjunto cubierto por regresiones diferenciales, también ejecutarse. No promete equivalencia completa de COBOL: las construcciones no soportadas quedan documentadas o señaladas explícitamente.

## Roadmap: objetivo final v1.0

El hito 0.8 describe la madurez del flujo de trabajo, no una publicación oficial ni compatibilidad completa con COBOL. El objetivo de producto ahora es **alcanzar al menos un 75 % de equivalencia diferencial exacta en el benchmark externo de 500 programas**, partiendo de una línea base medida del 10,6 %. Esto equivale a **375 de 500 programas** con stdout y código de retorno idénticos a GnuCOBOL. No se declarará v1.0 por traducir más archivos o generar Python sintácticamente válido: el umbral debe verificarse con evidencia reproducible.

### Objetivo de salida para v1.0

- **Línea base externa:** 53/500 coincidencias exactas (10,60 %). El benchmark es una muestra de fuentes independientes que compilan y terminan bajo GnuCOBOL; no representa todos los dialectos ni todos los sistemas COBOL.
- **Meta mínima:** ≥375/500 (≥75,00 %) en la muestra primaria, con la misma metodología y denominador documentado.
- **Protección contra sobreajuste:** validar además una muestra disjunta de 500 programas seleccionados con el mismo procedimiento, sin usarla para elegir o ajustar las correcciones; meta ≥75 % también en esa muestra antes de declarar v1.0.
- **Calidad de traducción:** cada arreglo de una familia semántica debe incluir pruebas unitarias y, cuando sea viable, comparación diferencial contra GnuCOBOL. Los casos no soportados deben diagnosticarse, no convertirse silenciosamente en comentarios.
- **Integridad de la versión:** CI obligatorio verde, informe de ambos benchmarks publicado, README/roadmap y límites actualizados, y revisión de regresiones del corpus interno. La PR de trabajo no se fusiona automáticamente.

### Plan de ejecución hacia v1.0

1. **Hacer fiable la medición:** asegurar que cada ejecución externa conserva JSON/Markdown y artefactos incluso si el benchmark falla; registrar commit, checksum del dataset, selección, exclusiones y resultados.
2. **Clasificar los fallos:** separar error del traductor, Python inválido, excepción/timeout en ejecución, diferencias de salida y código de retorno; agrupar por causa raíz y frecuencia.
3. **Atacar las causas de mayor impacto:** priorizar familias que recuperen más programas con una corrección semántica sólida; añadir regresiones antes de cada cambio.
4. **Subir por etapas:** medir sobre los mismos 500 casos en cada iteración y publicar las tasas reales; no cambiar el denominador ni contar errores del compilador de referencia como fallos del traductor.
5. **Validar sin sobreajuste:** congelar los cambios candidatos y ejecutar una muestra externa disjunta; corregir regresiones y repetir la verificación.
6. **Candidatura v1.0:** exigir ≥75 % en ambas muestras, CI verde, diagnósticos honestos y documentación que describa exactamente qué se ha medido.

El 75 % es una **meta de aceptación pendiente**, no una capacidad actual ni una promesa de compatibilidad universal. Hasta alcanzar la evidencia anterior, no se anunciará que el proyecto está listo para v1.0.

| Área | Estado actual | Evidencia y límite |
|---|---|---|
| Traductor y benchmark | Base estable para el subconjunto medido | Corpus versionado de 105 casos con GnuCOBOL; no es una estimación de compatibilidad general |
| Inventario multiarchivo | Implementado con clasificación estática | Dependencias resueltas, sin resolver, ambiguas y CALL dinámicas; los nombres no prueban enlazado en ejecución |
| Piloto integrado | Informe de esquema v2 | Traducción, sintaxis, clasificación por código/categoría y enlaces exactos a fixtures candidatas; por defecto no ejecuta el código generado |
| Agente web | Demo heurística local | Selección de archivos, hallazgos y exportación; el análisis web no sustituye al CLI Python |
| Evidencia de CI | Integrada | CI valida el contrato del informe y publica el informe del piloto como artefacto para revisión |
| Revisión de los diagnósticos de samples | Triage automatizado: 35 archivos con limitaciones conocidas; 1 falso positivo corregido | El [baseline de triage](docs/pilot-diagnostics-baseline.md) enumera cada fuente. La revisión humana de los 35 casos sigue pendiente |
| Semántica de control y almacenamiento (objetivo v0.8.x) | Pendiente prioritario: `ALTER`, `GO TO ... DEPENDING ON` y `REDEFINES` | Caso de regresión LABERINTO-COBOL; exige preservar el flujo dinámico y las vistas de almacenamiento compartido, con comparación diferencial frente a GnuCOBOL |

El objetivo de cierre de v0.8.x incluye cerrar brechas semánticas de alto impacto antes de ampliar la cobertura: `ALTER` debe cambiar en ejecución el destino del salto asociado, `GO TO ... DEPENDING ON` debe conservar la selección ordinal COBOL (base 1 y comportamiento fuera de rango), y `REDEFINES` debe compartir almacenamiento físico en vez de generar diccionarios independientes. El caso `LABERINTO-COBOL` será una regresión diferencial end-to-end; no se marcará como soportado hasta que coincidan salida y código de retorno con GnuCOBOL y haya pruebas específicas de cada construcción.

El roadmap detallado, con los hitos de madurez v0.1–v0.8 y el siguiente ciclo hacia 0.9/1.0, está en [docs/roadmap-two-weeks.md](docs/roadmap-two-weeks.md). La clasificación automática ayuda a priorizar; no declara por sí sola que un hallazgo sea un falso positivo ni que un programa sea seguro para migrar.

---

## Por qué existe

Hay miles de sistemas críticos corriendo COBOL en bancos, aseguradoras y administraciones. Y hay miles de desarrolladores que saben Python, TypeScript y Rust, pero nunca han tocado COBOL. El resultado es un muro: código que se mantiene porque no se entiende, y se entiende porque no se toca.

`cobol2py` no rompe el muro. Lo hace translúcido.

---

## Dos componentes, dos usos

El proyecto ha evolucionado desde un traductor de COBOL a Python hacia un repositorio que también incluye planificación de modernizaciones a escala de sistema. Los componentes comparten repositorio y objetivo, pero **no dependen uno del otro para su uso básico**.

- **Traductor (`cobol2py.py`)**: recibe un programa COBOL y emite Python o Java. Puede descargarse y utilizarse por sí solo; no necesita `cobol2py_agent.py`.
- **Agente (`cobol2py_agent.py`)**: inspecciona un repositorio con múltiples programas y artefactos relacionados, y genera un inventario y un plan de migración en Markdown/JSON. No modifica los fuentes.
- **Piloto integrado (`tools/modernize_pilot.py`)**: conecta inventario y traducción del subconjunto a Python, comprueba sintaxis y crea un informe por archivo. Por defecto no ejecuta el código generado; el flag explícito `--differential` ejecuta únicamente fixtures de ruta exacta y compara stdout/código de retorno con GnuCOBOL.
- **Evidencia medida**: el piloto traduce 108/108 fuentes de `samples` sin errores de sintaxis ni de traducción. En el modo diferencial opt-in, 105/105 fixtures versionadas coinciden con GnuCOBOL en stdout y código de retorno. Esto no demuestra equivalencia para entradas no medidas ni efectos externos.
- **Corpus externo amplio (muestras primaria y holdout)**: el workflow [`external-cobol-corpus`](.github/workflows/external-cobol-corpus.yml) toma dos muestras deterministas disjuntas de 500 fuentes cada una del dataset público [X-COBOL v2](https://zenodo.org/records/14269462), las compara con GnuCOBOL en un contenedor sin red y publica solo hashes y resultados. La línea base externa inicial fue 53/500 coincidencias exactas (10,60 %). La medición completa más reciente confirmada es **109/500 (21,80 %) en la muestra primaria y 114/500 (22,80 %) en el holdout disjunto**, ambas en el commit `699dd7b0` ([workflow e informes](https://github.com/orbitalronin94/cobol2py/actions/runs/40666810511)). Son mejoras de 18 casos sobre la última medición primaria anterior (91/500) y 26 sobre el holdout anterior (88/500), pero ninguna muestra se acerca todavía al umbral de 375/500. La siguiente iteración corrige el orden de traducción de comparaciones compuestas como `GREATER OR EQUAL`; su benchmark externo está en curso y no se contabiliza hasta publicarse el informe. El CI de tests de `699dd7b0` está verde ([tests](https://github.com/orbitalronin94/cobol2py/actions/runs/40666810459), [diferencial](https://github.com/orbitalronin94/cobol2py/actions/runs/40666810518)). Véase [metodología y límites](benchmarks/EXTERNAL_CORPUS.md).

### Usar solo el traductor

No hay instalación ni dependencias externas: requiere Python 3.10+ y basta con `cobol2py.py`.

### Usar solo el agente

Requiere Python 3.10+ y el archivo `cobol2py_agent.py`; genera un plan de análisis, no una traducción ejecutable.



```bash
curl -O https://raw.githubusercontent.com/orbitalronin94/cobol2py/main/cobol2py.py
```

Si prefieres clonar el repo:

```bash
git clone https://github.com/orbitalronin94/cobol2py.git
cd cobol2py
```

---

## Uso

```bash
python cobol2py.py programa.cbl
```

Eso imprime la traducción por stdout. Si quieres guardarla en un archivo:

```bash
python cobol2py.py programa.cbl --out programa.py
python cobol2py.py programa.cbl --lang java --out Cobol2PyProgram.java
javac Cobol2PyProgram.java
python tools/gnucobol_trace.py programa.cbl --format auto
```

Y si quieres comprobar que la salida es Python válido:

```bash
python -m py_compile programa.py && echo "OK"
python -m unittest discover -s tests -v
```

To exercise the standalone HTML in a real browser (requires Chromium and internet access for the Pyodide CDN):

```bash
python -m pip install playwright==1.56.0
python -m playwright install chromium
python tests/browser_smoke.py
```


## Agente de modernización de repositorios

¿Tu sistema tiene cientos de programas COBOL, copybooks compartidos, llamadas entre módulos, JCL y SQL? Ejecuta el agente de forma independiente del traductor: analiza un repositorio completo y produce un inventario y un plan de migración revisable. Es determinista, no instala dependencias externas y **no modifica ni ejecuta los programas analizados**. No necesitas ejecutar `cobol2py.py` para generar este informe.

```bash
python cobol2py_agent.py /ruta/al/sistema \
  --out reports/migration-plan.md \
  --json-out reports/migration-plan.json
```

El informe incluye:
- Inventario de programas COBOL, copybooks, ficheros JCL y SQL.
- Referencias detectadas mediante `COPY`, `CALL`, `EXEC PGM`, inclusiones SQL y datasets JCL.
- Dependencias resueltas por nombre, referencias sin resolver y referencias ambiguas con varias rutas candidatas.
- El análisis excluye comentarios reconocidos y enmascara literales antes de detectar dependencias; sigue siendo heurístico y no sustituye un parser completo.
- Construcciones que necesitan revisión y etapas sugeridas para una migración por oleadas.

Este es el **primer bloque**, no el agente autónomo completo: el análisis usa heurísticas de texto, puede pasar por alto referencias dinámicas y no demuestra equivalencia semántica. El siguiente paso es integrar el traductor existente y la verificación diferencial como un flujo por módulo. Consulta la [guía del agente](docs/repo-modernization-agent.md) y la [arquitectura](docs/architecture.md).

Pruebas del componente:

```bash
python -m unittest discover -s tests -p 'test_modernize_agent.py' -v
```

---

## Ejemplo mínimo

Entra esto (`hello.cbl`):

```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. HOLA.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 MENSAJE        PIC X(20) VALUE "HOLA MUNDO".
       01 CONTADOR       PIC 9(3)  VALUE 0.
       PROCEDURE DIVISION.
       PRINCIPAL.
           DISPLAY MENSAJE.
           MOVE 5 TO CONTADOR.
           COMPUTE CONTADOR = CONTADOR + 10.
           IF CONTADOR > 10 THEN
               DISPLAY "GRANDE"
           ELSE
               DISPLAY "PEQUENO"
           END-IF.
           STOP RUN.
```

Sale esto:

```python
# VARIABLES (WORKING-STORAGE)
mensaje: str = ""  # COBOL: 01 MENSAJE PIC X(20) VALUE "HOLA MUNDO"
contador: int = 0  # COBOL: 01 CONTADOR PIC 9(3) VALUE 0

# PÁRRAFO: PRINCIPAL
def principal():
    print("HOLA MUNDO")
    contador = 5
    contador = contador + 10
    if contador > 10:
        print("GRANDE")
    else:
        print("PEQUENO")
    return

if __name__ == "__main__":
    principal()
```

No es Python perfecto. Es Python **legible**. Y eso es lo que importa.

---

## Qué traduce

| COBOL | Python |
|---|---|
| `IDENTIFICATION DIVISION` | (cabecera) |
| `PROGRAM-ID. X.` | nombre del módulo |
| `WORKING-STORAGE SECTION` | variables con tipo inferido del `PIC`; grupos de datos como diccionarios anidados |
| `PIC X(n)` | `str` |
| `PIC 9(n)` | `int` |
| `PIC 9(n)V9(m)` | `float` |
| `OCCURS n TIMES` | `list[T]` con tamaño fijo |
| `OCCURS n DEPENDING ON X` | Lista con tamaño máximo; la longitud activa dinámica no está implementada y se advierte en `--strict` |
| `DISPLAY` | `print()` |
| `ACCEPT` | Conversión numérica básica o recorte/relleno al ancho de PIC X/A |
| `MOVE` | asignación |
| `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE` | `+=`, `-=`, `*=`, `/=` |
| `COMPUTE` | expresión |
| `IF/THEN/ELSE/END-IF` | `if/else` anidados |
| `PERFORM párrafo` | llamada a función |
| `PERFORM párrafo N TIMES` | `for _ in range(N)` |
| `PERFORM párrafo UNTIL X` | `while not X` |
| `STOP RUN` | Termina el programa; señal propagada en Python y `System.exit(0)` en Java |
| `GOBACK`, `EXIT PROGRAM` | `return` local |
| `--lang java` | Backend Java básico que consume el mismo árbol de bloques; compila en el subset probado |

---

## Qué NO traduce

Y lo dice. No falla en silencio.

| COBOL | Estado |
|---|---|
| `EVALUATE/WHEN/WHEN OTHER` | Traducción básica a `if/elif/else`; rangos `THRU` y `EVALUATE TRUE` acotados. |
| `COPY` / copybooks | Expansión recursiva desde el directorio fuente y rutas `--copybook-path`; ciclos y faltantes quedan como advertencias. También admite pares de pseudo-texto `==texto== BY ==texto==` en `REPLACING`; bibliotecas y reglas avanzadas siguen pendientes. |
| `CALL` a subprogramas | Pendiente. |
| `FILE SECTION`, I/O | Pendiente. |
| `SORT`, `SEARCH`, `MERGE` | Pendiente. |
| `REDEFINES` | Se genera como campos independientes. No hay `Union`. |
| `STRING`, `UNSTRING`, `INSPECT` | Pendiente. |
| `CICS`, `DB2`, `IMS` | Fuera de alcance. |
| COBOL antiguo con varias sentencias por línea | Puede fallar. |

Las sentencias de procedimiento que no se traducen suelen quedar como comentarios `# COBOL no traducido: ...`; las declaraciones de datos omitidas o aproximadas se señalan mediante diagnósticos cuando se usa `--strict` o `--diagnostics-json`. El modo normal no detecta todas las construcciones no soportadas, por lo que no debe asumirse que la ausencia de comentarios garantiza una traducción completa.

---

## Limitaciones documentadas

Estas son las que quedan pendientes y que sabes que existen antes de encontrártelas:

**1. La semántica de datos solo está cubierta en un subconjunto.**
`MOVE` aplica relleno con espacios y truncamiento por la derecha de campos alfanuméricos `PIC X/A`; los valores iniciales de esos campos también respetan su ancho. Para `PIC 9(n)` entero sin signo, `MOVE` conserva los dígitos menos significativos si el valor de origen excede el ancho. Hay comparación diferencial con GnuCOBOL para estos casos. No se emulan aún los campos numéricos con signo, las escalas decimales, todos los valores figurativos ni toda la semántica de almacenamiento COBOL. La salida no debe considerarse equivalente ni lista para producción.

**2. `EVALUATE` cubre un subconjunto.**
`WHEN` escalar, `WHEN OTHER`, `EVALUATE TRUE/FALSE` y rangos `THRU` tienen traducción básica. `ALSO`, abreviaturas de selección y todas las reglas de dialecto siguen fuera de cobertura.

**3. Literales con comillas duplicadas.** Los literales completos con comillas simples o dobles se decodifican según la regla COBOL de duplicar la comilla delimitadora, tanto en operandos como en expresiones y cláusulas `VALUE`. El analizador sigue siendo heurístico y esto no implica soporte para todas las formas de literal, prefijos o extensiones de dialecto.

**4. El splitter por verbos sigue siendo heurístico.**
La pila de bloques ahora conserva ámbitos anidados de `IF`, `PERFORM` y `EVALUATE`, y marca cierres malformados; sentencias COBOL concatenadas de formas no habituales todavía pueden confundirlo.

**5. Copybooks: expansión recursiva y `REPLACING` acotado.**
Se resuelve `COPY nombre.` o `COPY nombre.CPY.` buscando primero junto al archivo fuente, después en cada `--copybook-path` y finalmente en el directorio de trabajo. Se expanden dependencias anidadas y se detectan ciclos. Se admite una o más parejas de pseudo-texto con la forma `==texto-anterior== BY ==texto-nuevo==`; la sustitución es literal, sin interpretación de expresiones regulares y sin distinguir mayúsculas/minúsculas. No es un preprocesador COBOL completo: bibliotecas calificadas, otras formas de `REPLACING` y reglas avanzadas siguen sin soporte. Faltantes, ciclos, errores de lectura y cláusulas no soportadas quedan en advertencias.

**6. La jerarquía de grupos es una representación simplificada.**
Los grupos COBOL se emiten como diccionarios anidados y los campos se leen/escriben mediante nombres no cualificados o `OF/IN` básico. No se modelan `REDEFINES`, `RENAMES`, nombres de condición de nivel 88, la longitud activa de `OCCURS DEPENDING ON`, overlays de almacenamiento, todos los calificadores ni las reglas completas de inicialización de grupos.

---

## Estructura del repo

```
cobol2py/
├── cobol2py.py                 # traductor COBOL → Python/Java
├── cobol2py_agent.py           # inventario y plan de modernización multiarchivo
├── web_demo.py                 # servidor local opcional para la demo
├── README.md
├── LICENSE
├── samples/                    # fuentes COBOL y fixtures
│   ├── hello.cbl
│   ├── realtest.cbl
│   ├── move_semantics.cbl
│   └── bench_*.cbl             # fixtures de benchmark COBOL
├── benchmarks/
│   ├── cases.json              # corpus versionado de comparación diferencial
│   └── run_benchmark.py
├── tests/
│   ├── test_cobol2py.py        # pruebas del traductor
│   ├── test_modernize_agent.py # pruebas del agente de repositorio
│   └── browser_smoke.py        # smoke test de la demo HTML
├── tools/
│   └── gnucobol_trace.py       # trazas y snapshots con GnuCOBOL
├── docs/
│   ├── README.md               # índice de documentación
│   ├── architecture.md         # arquitectura
│   ├── decisions.md            # decisiones de diseño
│   └── repo-modernization-agent.md # alcance y uso del agente
├── web/
│   └── index.html              # demo autónoma en navegador
└── .github/workflows/
    ├── tests.yml
    └── differential-benchmark.yml
```

El árbol anterior resume los componentes principales, no enumera todas las fixtures ni los archivos auxiliares. El agente de modernización está separado del traductor de un solo archivo: primero inventaría COBOL, copybooks, JCL, SQL y dependencias para generar un plan revisable; no modifica los programas analizados.

## Demo HTML autónoma

Abre directamente [`web/index.html`](web/index.html) en un navegador moderno. El archivo incluye embebido el código fuente completo de `cobol2py.py` y ejecuta ese traductor real en el navegador mediante Pyodide; no utiliza un traductor JavaScript simplificado ni necesita ejecutar `web_demo.py`.

La primera traducción requiere conexión a Internet para descargar el runtime de Python desde el CDN de Pyodide. Después, el runtime permanece cargado en esa pestaña. El código COBOL y el código del traductor se ejecutan localmente; el programa COBOL no se envía a una API ni a un servidor de traducción. El HTML contiene la lógica del traductor, pero no incluye los binarios del runtime de Python.

La demo admite formatos `auto`, `fixed` y `free`, limita la entrada a 1 MB y permite copiar el Python generado. Las limitaciones semánticas de `cobol2py.py` siguen aplicándose: una traducción generada no implica equivalencia completa ni aptitud para producción.

El servidor local opcional sigue disponible para desarrollo:
```bash
python web_demo.py
```

La interfaz es una herramienta de prueba; no valida la equivalencia semántica ni convierte la salida en apta para producción.


## Agente de modernización de repositorios

Además del traductor de un solo archivo, el repositorio incluye un primer planificador estático para analizar aplicaciones COBOL con copybooks, JCL y SQL. No requiere dependencias externas ni modifica los programas analizados.

```bash
python cobol2py_agent.py /ruta/al/sistema \
  --out reports/migration-plan.md \
  --json-out reports/migration-plan.json
python -m unittest discover -s tests -p 'test_modernize_agent.py' -v
```

El informe enumera los artefactos detectados, las dependencias que logra resolver por nombre, las referencias pendientes y las construcciones que conviene revisar primero. Es una ayuda para planificar, no un parser completo, un migrador autónomo ni una prueba de equivalencia. Consulta [la guía del agente](docs/repo-modernization-agent.md) y [la arquitectura](docs/architecture.md) para conocer el alcance y el diseño previsto.


### Piloto de modernización integrado

Ejecuta inventario, traducción del subconjunto y comprobación sintáctica sin ejecutar los programas generados:

```bash
python tools/modernize_pilot.py samples --out-dir /tmp/cobol2py-pilot
```

Genera inventario Markdown/JSON, archivos Python traducidos y un informe por programa. El directorio de salida debe estar fuera del árbol de fuentes. El piloto no prueba equivalencia semántica; usa el benchmark diferencial con GnuCOBOL para los casos ejecutables.

## Documentación de ingeniería

La documentación de arquitectura, decisiones de diseño, alcance de compatibilidad, proceso de cambios y ejecución por fases está en [`docs/`](docs/README.md). Consulta el [roadmap de modernización de dos semanas](docs/roadmap-two-weeks.md) para el calendario, los criterios de aceptación y el registro de progreso. Los cambios semánticos deben incluir pruebas y, cuando sea posible, una comparación diferencial con GnuCOBOL. El porcentaje del benchmark mide únicamente los casos versionados; no demuestra equivalencia general.

## Pruebas

No requiere instalar dependencias:

```bash
python -m unittest discover -s tests -v
python -m py_compile cobol2py.py
```

El formato de origen puede indicarse explícitamente cuando la detección automática sea ambigua:

```bash
python cobol2py.py programa.cbl --format fixed
python cobol2py.py programa.cbl --format free
python cobol2py.py programa.cbl --copybook-path ./copybooks
```

Para convertir advertencias conocidas —sentencias no soportadas, copybooks sin resolver, bloques malformados, `REDEFINES`, ciertas cláusulas `PIC` numéricas y aritmética sin semántica completa de tamaño— en un error y evitar usar una salida incompleta por accidente:

```bash
python cobol2py.py programa.cbl --strict
python cobol2py.py programa.cbl --diagnostics-json
```

`--format auto` es el valor predeterminado; como las columnas de secuencia en blanco pueden aparecer tanto en formato fijo como en fuentes libres indentadas, no siempre es posible inferir el formato con certeza.

GitHub Actions ejecuta las pruebas con Python 3.10–3.13 y compara, mediante el benchmark diferencial, 102 programas COBOL contra GnuCOBOL. Los casos cubren `DISPLAY`, campos `PIC X/9`, `MOVE`, operaciones aritméticas, condiciones simples y compuestas, `IF` anidados, `PERFORM TIMES`, párrafos y tablas/subíndices. La suite de unittest mantiene además sus regresiones de runtime. La cobertura sigue limitada al corpus versionado y al subconjunto probado; no demuestra equivalencia semántica general ni certifica una migración. La compilación sintáctica de la salida, por sí sola, tampoco prueba equivalencia.

---

## Benchmark diferencial y evolución objetiva

El workflow `differential-benchmark.yml` falla si cualquier caso del candidato no coincide exactamente con GnuCOBOL; usa `--report-only` solo para análisis exploratorio. Compara el snapshot inicial del traductor (`02fde4b`) y el traductor actual contra el mismo corpus versionado; ambos se contrastan con el programa compilado por GnuCOBOL. En cada push a `main`, pull request o ejecución manual, publica un informe Markdown en el resumen de GitHub Actions y conserva los informes JSON/Markdown como artefactos durante 90 días.

- **Métrica principal:** porcentaje de programas cuyo `stdout` y código de salida coinciden exactamente con GnuCOBOL.
- **Comparación entre versiones:** ejecuta el snapshot inicial fijado en `02fde4b` y el candidato actual sobre el mismo corpus de la revisión evaluada, y muestra el cambio en puntos porcentuales.
- **Fallos visibles:** errores de compilación COBOL, traducción, ejecución Python y diferencias de salida cuentan como fallos del caso y aparecen en el detalle.
- **Corpus versionado:** `benchmarks/cases.json` define 102 programas y las capacidades cubiertas, incluidos casos de `COPY ... REPLACING` y overflow aritmético del campo receptor contrastados con GnuCOBOL. La revisión histórica del PR #9 obtuvo 100/100 coincidencias en el corpus de 100 casos que existía entonces; el snapshot inicial obtuvo 16/100 sobre aquel mismo corpus. En el commit [`9364ba6`](https://github.com/orbitalronin94/cobol2py/commit/9364ba6f8fd28e0f089409e91f826068d87c1502), el candidato obtuvo 101/101 coincidencias exactas (100 %) en el corpus de entonces, incluido un caso con dos parejas `COPY REPLACING`. En el commit [`1fb78c6`](https://github.com/orbitalronin94/cobol2py/commit/1fb78c6c606260451ca255227645586b0a39cfec), el corpus de 102 casos obtuvo **102/102 coincidencias exactas (100 %)**, incluida la nueva fixture `arithmetic-receiving-pic`. El benchmark volvió a pasar con las cinco operaciones aritméticas en la fixture ampliada en el commit [`4280bff`](https://github.com/orbitalronin94/cobol2py/commit/4280bff92d45ee6fd8e960227a6db5ddcb48e9) —102/102— en el [workflow diferencial](https://github.com/orbitalronin94/cobol2py/actions/runs/40496463428); esto solo acredita los casos versionados. El resultado mide solo los casos versionados, no la equivalencia general de COBOL. Para añadir un caso, incorpora un programa COBOL autónomo en `samples/` y una entrada al manifiesto; no elimines casos difíciles solo para subir la puntuación.
- **Interpretación prudente:** la métrica mide únicamente estos fixtures; no equivale al porcentaje de COBOL del mundo real que se traduce correctamente. Los casos deben crecer en variedad y complejidad, no solo en cantidad.

El runner compila cada referencia con el directorio del fuente como ruta de búsqueda de copybooks, para que los casos con `COPY` puedan compilarse desde la raíz del repositorio. Para ejecutar el benchmark localmente (requiere Python y GnuCOBOL):

```bash
python benchmarks/run_benchmark.py --translator cobol2py.py
```

---

## Hoja de ruta: de v0.2.0 a v1.0.0

Este roadmap distingue lo ya implementado de lo que sigue pendiente. Los números de versión son **hitos de desarrollo previstos**, no implican que cada versión se haya publicado como release. El criterio de salida de v1.0 es la evidencia diferencial externa descrita arriba: **≥75 % de coincidencia exacta en dos muestras disjuntas de 500 programas**.

**v0.2.0 — Trazabilidad con GnuCOBOL** · **Completado**
- [x] Añadir `tools/gnucobol_trace.py` para compilar y ejecutar con trazas.
- [x] Capturar snapshots `TRACE_VAR|nombre|valor` de campos escalares, grupos y elementos `OCCURS`.
- [x] Informar de nombres duplicados y tablas por encima del límite de captura.

**v0.3.0 — Diagnósticos y modo estricto** · **Implementado; cobertura por ampliar**
- [x] Emitir diagnósticos JSON y advertencias para construcciones conocidas no soportadas o aproximadas.
- [x] Añadir `--strict` para poder fallar ante diagnósticos relevantes en vez de aceptar silenciosamente una traducción incompleta.
- [ ] Auditar las familias de diagnósticos contra ejemplos COBOL reales y reducir falsos positivos/negativos.
- [ ] Asegurar que cada limitación de alto impacto tenga una prueba de regresión reproducible.

**v0.4.0 — Inventario de sistemas multiarchivo** · **Implementado como primer bloque**
- [x] Inventariar programas, copybooks, JCL, SQL y referencias entre artefactos.
- [x] Diferenciar referencias resueltas, no resueltas, ambiguas y llamadas dinámicas.
- [ ] Mejorar resolución de dependencias y documentar los casos dinámicos o específicos de dialecto que no se pueden resolver estáticamente.

**v0.5.0 — Piloto integrado de modernización** · **Implementado; no es migración autónoma**
- [x] Conectar inventario, traducción del subconjunto y comprobación sintáctica en un informe por archivo.
- [x] Mantener la ejecución diferencial opt-in y limitada a fixtures explícitas.
- [ ] Mejorar trazabilidad entre diagnóstico, línea fuente, código generado y prueba que respalda la compatibilidad.
- [ ] No presentar sintaxis válida ni análisis estático como prueba de equivalencia semántica.

**v0.6.0 — Cerrar brechas semánticas prioritarias** · **Implementación inicial completada; ampliar cobertura**
- [x] Implementar el cambio dinámico de destino de `ALTER` en el subconjunto probado.
- [x] Implementar `GO TO ... DEPENDING ON` con selección ordinal COBOL (base 1) y sin transferencia fuera de rango.
- [x] Modelar `REDEFINES` simples mediante almacenamiento compartido y offsets para los layouts compatibles.
- [x] Añadir las regresiones diferenciales `samples/control_flow_redefines.cbl` y `samples/laberinto_cobol.cbl`; ambas coinciden con GnuCOBOL en stdout/código de retorno en el corpus interno.
- [ ] Ampliar la cobertura a overlays con signo, escala implícita, packed decimal, arrays y layouts complejos; mantener diagnósticos explícitos mientras no estén validados.
- [ ] Verificar las mismas familias semánticas en programas del corpus externo y corregir discrepancias observadas.

**v0.7.0 — Cobertura diferencial y errores accionables** · **En curso**
- [x] Mantener el corpus diferencial versionado y ejecutar las referencias contra GnuCOBOL.
- [x] Hacer visibles las diferencias de salida y código de retorno en CI.
- [ ] Ampliar el corpus con casos representativos de las construcciones prioritarias y de errores observados en proyectos reales.
- [ ] Clasificar cada fallo por causa raíz: traducción, sintaxis Python, excepción/timeout, stdout distinto o código de retorno distinto.
- [ ] Añadir cada corrección al conjunto de regresiones para evitar que la puntuación suba a costa de romper casos existentes.

**v0.8.0 — Flujo reproducible de benchmark y diagnóstico** · **En curso**
- [x] Añadir benchmark externo determinista sobre X-COBOL v2, con checksum fijado, contenedor aislado y límites de recursos.
- [x] Publicar metodología, denominador, exclusiones y límites del conjunto evaluado.
- [ ] Garantizar que el informe JSON/Markdown y los artefactos se conserven incluso cuando una ejecución falla.
- [ ] Validar que la infraestructura de CI puede escribir, subir y recuperar los informes; no confundir una ejecución de medición completada con un traductor correcto.
- [ ] Registrar commit evaluado, checksum del dataset, selección, exclusiones, causas de fallo y tasa exacta en cada iteración.

**v0.9.0 — Candidato hacia el umbral v1.0** · **Pendiente**
- [ ] Usar la muestra primaria fija de 500 programas para cada iteración y publicar la puntuación real, sin alterar el denominador para mejorar resultados.
- [ ] Corregir primero las causas raíz que permitan recuperar más casos con cambios semánticos generales, respaldados por regresiones.
- [ ] Alcanzar y verificar ≥375/500 coincidencias exactas (≥75 %) en la muestra primaria.
- [ ] Congelar un candidato y evaluar una segunda muestra disjunta de 500 programas, no utilizada para decidir los cambios.
- [ ] Corregir regresiones y repetir las mediciones; si el umbral no se cumple, v1.0 sigue bloqueada.

**v1.0.0 — Primera versión con umbral de equivalencia verificado** · **No alcanzada**
- [ ] ≥75 % de equivalencia exacta en la muestra primaria de 500 programas y ≥75 % en la muestra disjunta de validación.
- [ ] CI obligatorio verde: pruebas unitarias, regresiones diferenciales y validación del formato de los informes.
- [ ] Informes reproducibles disponibles con revisión de fallos, exclusiones y limitaciones.
- [ ] Documentación de soporte y diagnósticos alineada con el comportamiento medido; no declarar compatibilidad universal con COBOL.
- [ ] Revisión final de regresiones y publicación explícita de los resultados. No se declara v1.0 hasta satisfacer todos los criterios anteriores.

### Indicadores que gobiernan el avance

| Indicador | Línea base | Criterio para v1.0 |
|---|---:|---:|
| Línea base inicial de la muestra primaria | 53/500 (10,60 %) | Referencia histórica |
| Última medición externa confirmada (`b59be7e8`) | 91/500 (18,20 %) | ≥375/500 (≥75 %) en la revisión candidata |
| Equivalencia exacta en muestra disjunta | Pendiente de medir | ≥375/500 (≥75 %) |
| Definición de coincidencia | stdout y código de retorno idénticos a GnuCOBOL | Sin cambios en la métrica |
| Informes reproducibles | En validación de infraestructura | Disponibles para ambas muestras |
| Compatibilidad general con COBOL | No demostrada | No se afirma; se documenta el alcance real |

El 75 % es una **meta de aceptación pendiente**, no la capacidad actual del traductor. La muestra externa solo incluye fuentes que compilan y terminan con GnuCOBOL y no representa todos los dialectos, entradas, ficheros, bases de datos ni efectos externos. El roadmap detallado de ejecución y seguimiento está en [`docs/roadmap-two-weeks.md`](docs/roadmap-two-weeks.md).
---

## Filosofía

- **Un archivo.** Si necesitas instalar algo, ya no es este proyecto.
- **Cero telemetría.** Nada sale de tu máquina.
- **Degradación elegante.** Lo que no se traduce, se comenta. Nunca se rompe.
- **Lectura sobre ejecución.** El objetivo no es correr el Python. Es entender el COBOL.
- **Auditable.** Cada línea del output se puede rastrear hasta la línea del COBOL original.

---

## Licencia

MIT.

Puedes copiarlo, modificarlo, venderlo, meterlo en tu producto. La única condición es mantener el aviso de copyright.

Esto no es un producto. Es una herramienta. Y las herramientas se comparten.

---

## Firma

**Agencia RONIN** — 2026
`#1310 — El conocimiento que no se ejecuta es decoración.`


Los nombres de datos o párrafos que coinciden con palabras reservadas de Python/Java se generan con el prefijo `cobol_`; esto evita conflictos sintácticos, aunque los identificadores de salida ya no coinciden literalmente con los nombres COBOL.

## Interfaz web del agente

Además del traductor web de [`web/index.html`](web/index.html), hay una interfaz independiente para inventariar sistemas en [`web/agent.html`](web/agent.html). Permite seleccionar múltiples archivos COBOL, copybooks, JCL y SQL, revisar dependencias detectadas, referencias sin resolver o ambiguas y exportar informes Markdown/JSON. La demo analiza los archivos localmente en el navegador y no los sube a un servidor.

La interfaz del navegador es una ayuda rápida con heurísticas reducidas, no un reemplazo del agente Python. Para análisis reproducibles y más completos, usa `python cobol2py_agent.py /ruta/al/sistema --out reports/plan.md --json-out reports/plan.json`; para enlazar inventario, traducción y comprobación sintáctica, consulta `tools/modernize_pilot.py`. Ninguno de estos informes prueba por sí solo equivalencia semántica.
