# cobol2py

> Traductor mínimo de COBOL a Python. Un archivo. Cero dependencias. Solo stdlib.

`cobol2py` pela la capa dura del código legado y deja ver la lógica de negocio que llevaba décadas enterrada bajo una sintaxis que nadie recuerda. No es una herramienta de migración. No es un IDE. No es un producto. Es un script que entra un `.cbl` y sale un `.py` legible.

La traducción busca **leerse** y, para el subconjunto cubierto por regresiones diferenciales, también ejecutarse. No promete equivalencia completa de COBOL: las construcciones no soportadas quedan documentadas o señaladas explícitamente.

---

## Por qué existe

Hay miles de sistemas críticos corriendo COBOL en bancos, aseguradoras y administraciones. Y hay miles de desarrolladores que saben Python, TypeScript y Rust, pero nunca han tocado COBOL. El resultado es un muro: código que se mantiene porque no se entiende, y se entiende porque no se toca.

`cobol2py` no rompe el muro. Lo hace translúcido.

---

## Instalación

No hay.

Es Python 3.10+. Descarga el archivo `cobol2py.py`. Y ya está.

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
| `OCCURS n DEPENDING ON X` | `list[T]` dinámica |
| `DISPLAY` | `print()` |
| `ACCEPT` | `input()` |
| `MOVE` | asignación |
| `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE` | `+=`, `-=`, `*=`, `/=` |
| `COMPUTE` | expresión |
| `IF/THEN/ELSE/END-IF` | `if/else` anidados |
| `PERFORM párrafo` | llamada a función |
| `PERFORM párrafo N TIMES` | `for _ in range(N)` |
| `PERFORM párrafo UNTIL X` | `while not X` |
| `STOP RUN`, `GOBACK`, `EXIT PROGRAM` | `return` |
| `--lang java` | Backend Java básico que consume el mismo árbol de bloques; compila en el subset probado |

---

## Qué NO traduce

Y lo dice. No falla en silencio.

| COBOL | Estado |
|---|---|
| `EVALUATE/WHEN/WHEN OTHER` | Traducción básica a `if/elif/else`; rangos `THRU` y `EVALUATE TRUE` acotados. |
| `COPY` simple | Expansión recursiva desde el directorio fuente y rutas `--copybook-path`; ciclos y faltantes quedan como advertencias. `REPLACING` y bibliotecas siguen pendientes. |
| `CALL` a subprogramas | Pendiente. |
| `FILE SECTION`, I/O | Pendiente. |
| `SORT`, `SEARCH`, `MERGE` | Pendiente. |
| `REDEFINES` | Se genera como campos independientes. No hay `Union`. |
| `STRING`, `UNSTRING`, `INSPECT` | Pendiente. |
| `CICS`, `DB2`, `IMS` | Fuera de alcance. |
| COBOL antiguo con varias sentencias por línea | Puede fallar. |

Todo lo que no se traduce sale con un comentario `# COBOL no traducido: ...` en el Python. Nunca se pierde silenciosamente. Nunca se inventa.

---

## Limitaciones documentadas

Estas son las que quedan pendientes y que sabes que existen antes de encontrártelas:

**1. La semántica de datos solo está cubierta en un subconjunto.**
`MOVE` aplica relleno con espacios y truncamiento por la derecha de campos alfanuméricos `PIC X/A`; los valores iniciales de esos campos también respetan su ancho. Para `PIC 9(n)` entero sin signo, `MOVE` conserva los dígitos menos significativos si el valor de origen excede el ancho. Hay comparación diferencial con GnuCOBOL para estos casos. No se emulan aún los campos numéricos con signo, las escalas decimales, todos los valores figurativos ni toda la semántica de almacenamiento COBOL. La salida no debe considerarse equivalente ni lista para producción.

**2. `EVALUATE` cubre un subconjunto.**
`WHEN` escalar, `WHEN OTHER`, `EVALUATE TRUE/FALSE` y rangos `THRU` tienen traducción básica. `ALSO`, abreviaturas de selección y todas las reglas de dialecto siguen fuera de cobertura.

**3. El splitter por verbos sigue siendo heurístico.**
La pila de bloques ahora conserva ámbitos anidados de `IF`, `PERFORM` y `EVALUATE`, y marca cierres malformados; sentencias COBOL concatenadas de formas no habituales todavía pueden confundirlo.

**4. Copybooks: solo expansión básica.**
Se resuelve `COPY nombre.` o `COPY nombre.CPY.` buscando primero junto al archivo fuente y después en cada `--copybook-path`. Se expanden dependencias anidadas y se detectan ciclos; faltantes, errores de lectura y cláusulas no soportadas quedan en comentarios de advertencia. `COPY ... REPLACING`, bibliotecas y reglas avanzadas de reemplazo siguen pendientes.

**5. La jerarquía de grupos es una representación simplificada.**
Los grupos COBOL se emiten como diccionarios anidados y los campos se leen/escriben mediante nombres no cualificados o `OF/IN` básico. No se modelan `REDEFINES`, `RENAMES`, overlays de almacenamiento, todos los calificadores ni las reglas completas de inicialización de grupos.

---

## Estructura del repo

```
cobol2py/
├── cobol2py.py
├── README.md
├── LICENSE
├── samples/
│   ├── hello.cbl
│   ├── realtest.cbl
│   ├── move_semantics.cbl
│   └── bench_*.cbl     # 98 fixtures de benchmark COBOL
├── benchmarks/
│   ├── cases.json       # corpus versionado de comparación diferencial
│   └── run_benchmark.py
├── tests/
│   └── test_cobol2py.py
└── .github/workflows/
    ├── tests.yml
    └── differential-benchmark.yml
```

## Demo web local

Puedes pegar un programa COBOL en una página HTML y ver la traducción generada por el traductor real. La demo usa un servidor Python local, no un traductor JavaScript simulado.

```bash
python web_demo.py
```

Abre [http://127.0.0.1:8765](http://127.0.0.1:8765). El servidor solo escucha en `localhost`, acepta entradas de hasta 1 MB y no envía el código a servicios externos. Permite elegir formato `auto`, `fixed` o `free`. Detén el servidor con Ctrl+C.

La interfaz es una herramienta de prueba; no valida la equivalencia semántica ni convierte la salida en apta para producción.

## Documentación de ingeniería

La documentación de arquitectura, decisiones de diseño, alcance de compatibilidad y proceso de cambios está en [`docs/`](docs/README.md). Los cambios semánticos deben incluir pruebas y, cuando sea posible, una comparación diferencial con GnuCOBOL. El porcentaje del benchmark mide únicamente los casos versionados; no demuestra equivalencia general.

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

`--format auto` es el valor predeterminado; como las columnas de secuencia en blanco pueden aparecer tanto en formato fijo como en fuentes libres indentadas, no siempre es posible inferir el formato con certeza.

GitHub Actions ejecuta las pruebas con Python 3.10–3.13 y compara, mediante el benchmark diferencial, 100 programas COBOL contra GnuCOBOL. Los casos cubren `DISPLAY`, campos `PIC X/9`, `MOVE`, operaciones aritméticas, condiciones simples y compuestas, `IF` anidados, `PERFORM TIMES`, párrafos y tablas/subíndices. La suite de unittest mantiene además sus regresiones de runtime. La cobertura sigue limitada al corpus versionado y al subconjunto probado; no demuestra equivalencia semántica general ni certifica una migración. La compilación sintáctica de la salida, por sí sola, tampoco prueba equivalencia.

---

## Benchmark diferencial y evolución objetiva

El workflow `differential-benchmark.yml` falla si cualquier caso del candidato no coincide exactamente con GnuCOBOL; usa `--report-only` solo para análisis exploratorio. Compara el snapshot inicial del traductor (`02fde4b`) y el traductor actual contra el mismo corpus versionado; ambos se contrastan con el programa compilado por GnuCOBOL. En cada push a `main`, pull request o ejecución manual, publica un informe Markdown en el resumen de GitHub Actions y conserva los informes JSON/Markdown como artefactos durante 90 días.

- **Métrica principal:** porcentaje de programas cuyo `stdout` y código de salida coinciden exactamente con GnuCOBOL.
- **Comparación entre versiones:** ejecuta el snapshot inicial fijado en `02fde4b` y el candidato actual sobre el mismo corpus de la revisión evaluada, y muestra el cambio en puntos porcentuales.
- **Fallos visibles:** errores de compilación COBOL, traducción, ejecución Python y diferencias de salida cuentan como fallos del caso y aparecen en el detalle.
- **Corpus versionado:** `benchmarks/cases.json` define 100 programas y las capacidades cubiertas: 2 fixtures de referencia previos y 98 fixtures de benchmark. La revisión del PR #9 obtuvo 100/100 coincidencias exactas de salida y código de retorno contra GnuCOBOL; el snapshot inicial obtuvo 16/100 sobre el mismo corpus. Este resultado mide solo estos casos versionados, no la equivalencia general de COBOL. Para añadir un caso, incorpora un programa COBOL autónomo en `samples/` y una entrada al manifiesto; no elimines casos difíciles solo para subir la puntuación.
- **Interpretación prudente:** la métrica mide únicamente estos fixtures; no equivale al porcentaje de COBOL del mundo real que se traduce correctamente. Los casos deben crecer en variedad y complejidad, no solo en cantidad.

Para ejecutar el benchmark localmente (requiere Python y GnuCOBOL):

```bash
python benchmarks/run_benchmark.py --translator cobol2py.py
```

---

## Hoja de ruta

**v0.0.5 — Semántica de datos y regresiones**
- [x] Ampliar `VALUE` para literales numéricos con signo/decimales y valores figurativos básicos (`SPACE(S)`, `ZERO(ES)`, `HIGH-VALUES`, `LOW-VALUES`, `QUOTE(S)`).
- [x] Ampliar `MOVE` para campos numéricos con signo y escala decimal, con una fixture diferencial ejecutada contra GnuCOBOL en CI.
- [x] Añadir pruebas de semántica para campos alfanuméricos, precisión numérica y condiciones; la cobertura de arrays continúa creciendo con el corpus existente.

**v0.0.6 — Control de flujo**
- [x] Implementar `EVALUATE/WHEN` con pruebas para `WHEN`, `WHEN OTHER` y anidamiento.
- [x] Sustituir el estado global del árbol por una pila de bloques coherente; cubrir IF anidados y cierres malformados.

**v0.0.7 — Copybook resolver**
- [x] Localizar `COPY nombre.CPY.` junto al fuente y en rutas explícitas; expandir antes del parseo.
- [x] Detectar ciclos y dejar constancia de copybooks no resueltos.
Alcance no cubierto: `COPY ... REPLACING` y bibliotecas calificadas.

**v0.0.8 — Jerarquía de datos**
- [x] Modelar grupos COBOL y campos hijos como diccionarios anidados, preservando la relación padre/hijo.
- [x] Traducir referencias básicas a campos anidados y cualificación `OF/IN`.
Alcance no cubierto: `REDEFINES`, `RENAMES`, overlays y grupos `OCCURS` complejos.

**v0.1.0 — Salida Java**
- [x] Reactivar el backend Java sobre el mismo AST y exponer `--lang java`.
- [x] Añadir fixture y CI que compila el Java generado y compara su salida con GnuCOBOL.
Alcance no cubierto: el backend Java sigue siendo un subconjunto; construcciones no soportadas se dejan explícitas como comentarios.

**v0.2.0 — Ejecución con GnuCOBOL**
- [x] Añadir `tools/gnucobol_trace.py`: compila con GnuCOBOL (`-ftraceall`) y ejecuta con trace habilitado.
- [x] Inyectar snapshots `TRACE_VAR|nombre|valor` para campos escalares, grupos y elementos `OCCURS` (hasta `--max-table-items`, por defecto 1000); los valores los formatea GnuCOBOL.
- [x] Reportar nombres duplicados y tablas sobre el límite en lugar de omitirlos silenciosamente.

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
