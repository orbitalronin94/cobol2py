# cobol2py

> Traductor COBOL a Python, con prototipos experimentales a C y Rust. El núcleo de análisis COBOL se comparte; los backends nativos tienen cobertura limitada y no prometen equivalencia general.

`cobol2py` nació como un traductor pequeño y autónomo de un archivo COBOL a Python legible. Después, el proyecto se amplió con un **agente inicial de análisis y planificación para sistemas empresariales multiarchivo** que ayuda a entender programas relacionados, copybooks, JCL y SQL antes de planificar una modernización. Son dos herramientas relacionadas, pero independientes: puedes usar el traductor sin el agente, y ejecutar el agente sin traducir código. El agente todavía no es un migrador autónomo ni promete equivalencia completa.

La traducción busca **leerse** y, para el subconjunto cubierto por regresiones diferenciales, también ejecutarse. No promete equivalencia completa de COBOL: las construcciones no soportadas quedan documentadas o señaladas explícitamente.

## Roadmap único de versiones hacia v1.0

Este es el roadmap de producto canónico: **el objetivo vigente es v1.0**. Los hitos anteriores, incluido v0.2, son contexto histórico y no planes alternativos ni versiones publicadas automáticamente. La v1.0 permanece bloqueada hasta cumplir las puertas de aceptación medibles que se indican aquí.

### Métrica de aceptación de v1.0

**Objetivo: al menos 375/500 (75 %) coincidencias exactas tanto en la muestra primaria como en un holdout disjunto de 500 programas.** Cada coincidencia exige que la traducción termine y que stdout y código de retorno sean idénticos a GnuCOBOL.

- **Línea base externa inicial:** 53/500 (10,60 %).
- **Mejor resultado externo validado hasta ahora:** **478/1.000 (47,80 %)** en el SHA exacto de la PR [#74](https://github.com/orbitalronin94/cobol2py/pull/74), con puerta estricta de aceptación superada: primaria **243/500 (48,60 %)** y holdout **235/500 (47,00 %)**. La muestra es 500 + 500, con checksum del corpus verificado y coincidencia exacta de stdout/código de retorno. Es +64 aciertos frente a la referencia congelada de 414/1.000.
- **Estado del `main` integrado:** el 47,80 % corresponde al SHA de la PR #74 que pasó el benchmark antes del merge. No atribuir automáticamente esa cifra al SHA integrado posterior; ejecutar el benchmark dedicado sobre el SHA actual de `main` para registrar su puntuación consolidada.
- **Integrado en `main`:** PR [#74](https://github.com/orbitalronin94/cobol2py/pull/74) incorpora correcciones de I/O y control de flujo. En su SHA previo al merge, tests, benchmark diferencial, multilenguaje, smoke, corpus externo y benchmark Python terminaron correctamente; la scorecard estricta registró 478/1.000.
- **Candidato retenido:** PR [#126](https://github.com/orbitalronin94/cobol2py/pull/126), `INSPECT CONVERTING`, obtuvo **413/1.000 (41,30 %)** en su SHA probado y además tiene conflicto con `main`. No se integra ese SHA: incumple la puerta estricta y requiere resolver el conflicto, revisar la implementación y repetir el benchmark completo.
- **Objetivo v1.0 y brecha:** la puerta de release sigue siendo ≥375/500 (75 %) en primaria y ≥375/500 (75 %) en holdout, con muestras disjuntas. La v1.0 sigue bloqueada hasta cumplir ambas metas y la validación completa.
- **Siguiente iteración:** seguir el [roadmap operativo del benchmark externo](docs/EXTERNAL_BENCHMARK_ITERATION_ROADMAP.md), el [análisis actualizado de fallos](docs/EXTERNAL_BENCHMARK_FAILURE_ANALYSIS.md) y la [investigación de arquitecturas open source](docs/OPEN_SOURCE_COMPILER_RESEARCH.md). No atribuir una puntuación a un SHA distinto del medido.
- **Límites:** la métrica mide stdout y código de retorno de programas ejecutables del dataset, no equivalencia de archivos, bases de datos, transacciones, interacciones ni todos los dialectos.

### Hitos de versión

| Versión | Objetivo | Estado y criterio de salida |
|---|---|---|
| **v0.2.0 — trazabilidad con GnuCOBOL** | Capturar trazas y snapshots de variables | Hito histórico completado; no representa el objetivo actual del proyecto |
| **v0.3.0 — diagnósticos y modo estricto** | Señalar construcciones no soportadas o aproximadas | Implementado inicialmente; falta auditar diagnósticos contra casos reales y reducir falsos positivos/negativos |
| **v0.4.0 — inventario multiarchivo** | Inventariar COBOL, copybooks, JCL, SQL y dependencias | Primer bloque implementado; falta mejorar resolución estática y documentar casos dinámicos |
| **v0.5.0 — piloto integrado** | Conectar inventario, traducción del subconjunto y comprobación sintáctica | Implementado como piloto; no es migración autónoma ni prueba de equivalencia |
| **v0.6.0 — brechas semánticas prioritarias** | Corregir control de flujo y layouts de datos, con regresiones | Base implementada; ampliar overlays, signos, escalas decimales, packed decimal y layouts complejos |
| **v0.7.0 — cobertura diferencial** | Clasificar discrepancias y añadir regresiones | En curso; priorizar causas raíz que afectan a múltiples programas |
| **v0.8.0 — medición reproducible** | Benchmark externo determinista, aislamiento, informes y checksums | Infraestructura implementada; mantener informes recuperables y resultados comparables por commit |
| **v0.9.0 — candidato de release** | Aumentar coincidencias exactas sin cambiar la muestra ni el denominador | Pendiente: alcanzar ≥375/500 en primaria, congelar candidato y validar la muestra disjunta |
| **v1.0.0 — equivalencia verificada** | Publicar un traductor con resultados reproducibles y límites claros | **No alcanzada.** Requiere ≥75 % en ambas muestras, CI verde, informes publicados y revisión final de regresiones |

### Plan de ejecución para llegar a v1.0

1. **Medir y clasificar:** conservar SHA, checksum, selección, exclusiones y resultado por caso; separar errores del traductor de fallos de referencia.
2. **Priorizar por impacto:** agrupar fallos por causa raíz (traducción, sintaxis Python, excepción/timeout, stdout o código de retorno) y corregir primero familias frecuentes con soluciones semánticas generales.
3. **Probar cada corrección:** añadir regresiones mínimas y comparación con GnuCOBOL cuando sea viable; mantener `cobol2py.py` y `web/index.html` sincronizados.
4. **Repetir la misma medición:** publicar solo ganancias confirmadas, conservar el denominador y registrar también cualquier regresión.
5. **Validar generalización:** congelar un candidato y comprobar el umbral en la muestra disjunta sin usarla para ajustar las correcciones.
6. **Autorizar v1.0:** exigir ambas metas, CI completa verde, informes reproducibles, limitaciones documentadas y revisión final de release.

El 75 % es una **puerta de aceptación pendiente**, no una capacidad actual ni una promesa de compatibilidad universal. El análisis técnico de los fallos y las prioridades de la siguiente iteración se mantiene en [`docs/EXTERNAL_BENCHMARK_FAILURE_ANALYSIS.md`](docs/EXTERNAL_BENCHMARK_FAILURE_ANALYSIS.md).
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
- **Corpus externo amplio (muestras primaria y holdout)**: el workflow [`external-cobol-corpus`](.github/workflows/external-cobol-corpus.yml) compara dos muestras deterministas disjuntas de 500 fuentes de [X-COBOL v2](https://zenodo.org/records/14269462) con GnuCOBOL en un contenedor sin red. El mejor resultado externo validado de Python ha alcanzado **415/1.000 (41,50 %)** en dos candidatos (PR #128: 197/500 primaria y 218/500 holdout; PR #44: 198/500 y 217/500), siempre con la muestra fija de 500 + 500 y coincidencia exacta de stdout/código de retorno. El SHA integrado actual de `main` debe medirse de nuevo para atribuirle formalmente esa puntuación; los benchmarks de PR #74 y otros candidatos siguen en ejecución y no se contabilizan hasta completar ambas muestras sobre el SHA exacto. Los backends C/Rust siguen teniendo cobertura experimental mucho menor. Véase [metodología y límites](benchmarks/EXTERNAL_CORPUS.md). Véase [metodología y límites](benchmarks/EXTERNAL_CORPUS.md).

### Prototipos experimentales C y Rust

El repositorio incluye ahora `cobol2native.py`, que reutiliza el parser y el modelo de datos de `cobol2py.py` y emite C o Rust para un subconjunto explícito de COBOL. **No es todavía un backend de cobertura general ni tiene una puntuación del corpus externo.** Las construcciones fuera del subconjunto se rechazan en lugar de producir una traducción que parezca correcta.

```bash
python cobol2native.py programa.cbl --lang c --out programa.c
cc -std=c11 -Wall -Wextra programa.c -o programa
./programa

python cobol2native.py programa.cbl --lang rust --out programa.rs
rustc programa.rs -o programa-rust
./programa-rust
```

La cobertura inicial se limita a almacenamiento elemental de nivel superior con PIC alfanumérico o entero simple, DISPLAY, MOVE literal/referencia simple, ADD básico y terminación. Grupos, OCCURS, REDEFINES, control de flujo estructurado, decimales y muchas otras construcciones todavía no están soportadas. Consulta [alcance y arquitectura prevista](docs/native-backends.md).

#### Benchmark pareado de Python, C y Rust

El workflow [multilang-benchmark](.github/workflows/multilang-benchmark.yml) compila y ejecuta las salidas C y Rust y las compara, junto con Python, contra la misma referencia GnuCOBOL en las fixtures de `benchmarks/cases.json`. Una coincidencia exige stdout idéntico byte a byte y el mismo código de retorno. Las construcciones no soportadas, errores de traducción/compilación y diferencias de salida cuentan como fallos; los casos cuya referencia GnuCOBOL no compile o no termine se identifican aparte y no entran en el denominador. Los informes Markdown y JSON se publican como artefacto de CI.

Ejecuta localmente con Python, GnuCOBOL, un compilador C y Rust instalados:

```bash
python3 benchmarks/run_multilang_benchmark.py --output-dir /tmp/cobol2py-multilang
```

La primera medición pareada terminó en el workflow [#40860402652](https://github.com/orbitalronin94/cobol2py/actions/runs/40860402652): Python **105/105 (100,00 %)**, C **40/105 (38,10 %)** y Rust **40/105 (38,10 %)**. Los tres usaron las mismas 105 fixtures y GnuCOBOL como oráculo; el criterio es stdout byte a byte y código de retorno idénticos. El 100 % de Python solo describe este corpus pequeño y no contradice el benchmark externo, mucho más difícil.

El workflow [external-cobol-corpus](.github/workflows/external-cobol-corpus.yml) se ha ampliado para medir los tres backends sobre la misma selección determinista de X-COBOL v2 (muestra primaria y holdout de 500 programas cada una). Consulta las decisiones [D-042 a D-045](docs/decisions.md) para la motivación de los dos backends nuevos y el método para convertir discrepancias en regresiones de Python.

Los resultados de C, Rust y Python deberán medirse contra GnuCOBOL con las mismas muestras congeladas, sin comparar porcentajes de corpus distintos ni asumir que un lenguaje es más fiel por diseño.

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
| `MOVE` | asignación con ajuste básico al `PIC` receptor; admite varios receptores (`MOVE A TO B C`) y movimientos de grupo dentro del subconjunto probado |
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

La documentación de arquitectura, decisiones de diseño, compatibilidad y proceso de cambios está en [`docs/`](docs/README.md). El README contiene el único roadmap de producto hacia v1.0; el [análisis del benchmark externo](docs/EXTERNAL_BENCHMARK_FAILURE_ANALYSIS.md) mantiene el diagnóstico técnico y las prioridades de corrección. Los cambios semánticos deben incluir pruebas y, cuando sea posible, una comparación diferencial con GnuCOBOL. El porcentaje del benchmark mide únicamente los casos versionados; no demuestra equivalencia general.

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

GitHub Actions ejecuta las pruebas con Python 3.10–3.13 y compara, mediante el benchmark diferencial, 105 programas COBOL contra GnuCOBOL. Los casos cubren `DISPLAY`, campos `PIC X/9`, `MOVE`, operaciones aritméticas, condiciones simples y compuestas, `IF` anidados, `PERFORM TIMES`, párrafos y tablas/subíndices. La suite de unittest mantiene además sus regresiones de runtime. La cobertura sigue limitada al corpus versionado y al subconjunto probado; no demuestra equivalencia semántica general ni certifica una migración. La compilación sintáctica de la salida, por sí sola, tampoco prueba equivalencia.

---

## Benchmark diferencial y evolución objetiva

El workflow `differential-benchmark.yml` falla si cualquier caso del candidato no coincide exactamente con GnuCOBOL; usa `--report-only` solo para análisis exploratorio. Compara el snapshot inicial del traductor (`02fde4b`) y el traductor actual contra el mismo corpus versionado; ambos se contrastan con el programa compilado por GnuCOBOL. En cada push a `main`, pull request o ejecución manual, publica un informe Markdown en el resumen de GitHub Actions y conserva los informes JSON/Markdown como artefactos durante 90 días.

- **Métrica principal:** porcentaje de programas cuyo `stdout` y código de salida coinciden exactamente con GnuCOBOL.
- **Comparación entre versiones:** ejecuta el snapshot inicial fijado en `02fde4b` y el candidato actual sobre el mismo corpus de la revisión evaluada, y muestra el cambio en puntos porcentuales.
- **Fallos visibles:** errores de compilación COBOL, traducción, ejecución Python y diferencias de salida cuentan como fallos del caso y aparecen en el detalle.
- **Corpus versionado:** `benchmarks/cases.json` define actualmente 105 programas y las capacidades cubiertas, incluidos casos de `COPY ... REPLACING` y overflow aritmético del campo receptor contrastados con GnuCOBOL. La revisión histórica del PR #9 obtuvo 100/100 coincidencias en el corpus de 100 casos que existía entonces; el snapshot inicial obtuvo 16/100 sobre aquel mismo corpus. En el commit [`9364ba6`](https://github.com/orbitalronin94/cobol2py/commit/9364ba6f8fd28e0f089409e91f826068d87c1502), el candidato obtuvo 101/101 coincidencias exactas (100 %) en el corpus de entonces, incluido un caso con dos parejas `COPY REPLACING`. En el commit [`1fb78c6`](https://github.com/orbitalronin94/cobol2py/commit/1fb78c6c606260451ca255227645586b0a39cfec), el corpus de 102 casos obtuvo **102/102 coincidencias exactas (100 %)**, incluida la nueva fixture `arithmetic-receiving-pic`. El benchmark volvió a pasar con las cinco operaciones aritméticas en la fixture ampliada en el commit [`4280bff`](https://github.com/orbitalronin94/cobol2py/commit/4280bff92d45ee6fd8e960227a6db5ddcb48e9) —102/102— en el [workflow diferencial](https://github.com/orbitalronin94/cobol2py/actions/runs/40496463428); esto solo acredita los casos versionados. El resultado mide solo los casos versionados, no la equivalencia general de COBOL. Para añadir un caso, incorpora un programa COBOL autónomo en `samples/` y una entrada al manifiesto; no elimines casos difíciles solo para subir la puntuación.
- **Interpretación prudente:** la métrica mide únicamente estos fixtures; no equivale al porcentaje de COBOL del mundo real que se traduce correctamente. Los casos deben crecer en variedad y complejidad, no solo en cantidad.

El runner compila cada referencia con el directorio del fuente como ruta de búsqueda de copybooks, para que los casos con `COPY` puedan compilarse desde la raíz del repositorio. Para ejecutar el benchmark localmente (requiere Python y GnuCOBOL):

```bash
python benchmarks/run_benchmark.py --translator cobol2py.py
```

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


## Benchmark externo de tres backends (2026-10-29)

La última ejecución **completa y verificada** del benchmark pareado disponible antes de los cambios de `SCREEN SECTION` fue la [#40879506626](https://github.com/orbitalronin94/cobol2py/actions/runs/40879506626), sobre el commit medido `9c3af0310073a7c3c753d9779f22a12c247b1351`. Usó X-COBOL v2 con GnuCOBOL como oráculo. Cada backend se evaluó sobre los mismos 500 programas elegibles por muestra; un acierto requiere coincidencia exacta de stdout y código de retorno. Los fuentes externos no se publican en los artefactos.

| Muestra | Python | C experimental | Rust experimental |
|---|---:|---:|---:|
| Principal (500) | 179/500 (35,80 %) | 17/500 (3,40 %) | 16/500 (3,20 %) |
| Holdout (500) | 198/500 (39,60 %) | 20/500 (4,00 %) | 19/500 (3,80 %) |
| **Combinado (1.000)** | **377/1.000 (37,70 %)** | **37/1.000 (3,70 %)** | **35/1.000 (3,50 %)** |

En primaria se cribaron 1.244 candidatos, con 731 fallos de compilación de referencia y 13 exclusiones de ejecución; en holdout se cribaron 2.434, con 1.403 fallos de compilación y 31 exclusiones. Los denominadores de cada backend son los 500 programas elegibles de su muestra. Python supera ampliamente a los backends nativos experimentales; estos resultados son una línea base, no una estimación de compatibilidad universal ni una comparación de rendimiento. Los backends C/Rust soportan un subconjunto mucho menor y rechazan muchas construcciones.

**Medición posterior pendiente:** los cambios de análisis de `SCREEN SECTION` están en validación en [workflow #40883496209](https://github.com/orbitalronin94/cobol2py/actions/runs/40883496209). No se atribuirá ninguna mejora al código nuevo hasta que ese benchmark termine y se comparen los resultados con la misma selección.
