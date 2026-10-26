# cobol2py

> Traductor mínimo de COBOL a Python. Un archivo. Cero dependencias. Solo stdlib.

`cobol2py` pela la capa dura del código legado y deja ver la lógica de negocio que llevaba décadas enterrada bajo una sintaxis que nadie recuerda. No es una herramienta de migración. No es un IDE. No es un producto. Es un script que entra un `.cbl` y sale un `.py` legible.

La traducción no busca ejecutarse. Busca **leerse**. Entender qué hacía el COBOL sin pelearse con él.

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
| `WORKING-STORAGE SECTION` | variables con tipo inferido del `PIC` |
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

---

## Qué NO traduce

Y lo dice. No falla en silencio.

| COBOL | Estado |
|---|---|
| `EVALUATE` | Comentado. Pendiente v0.0.5. |
| `COPY` (copybooks) | Ignorado. Degradación elegante. |
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

**2. `EVALUATE` no se traduce.**
Se marca con un comentario y se deja para v0.0.5.

**3. IF anidados a más de 2 niveles pueden fallar.**
La heurística del splitter por verbos no es perfecta. Detecta sentencias concatenadas por el verbo que las abre, pero puede confundirse si un identificador coincide con un verbo (raro, pero posible).

**4. Copybooks no se resuelven.**
Si el programa usa `COPY CUSTMAST.CPY.`, las variables del copybook no aparecen. El traductor no falla, pero el Python está incompleto.

**5. Los grupos (nivel 01 con hijos 05) no se expanden.**
Salen como comentario. `# Grupo nivel 01: WS-REGISTRO`. No se genera un dataclass ni un modelo.

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
│   └── bench_*.cbl     # 48 casos COBOL independientes
├── benchmarks/
│   ├── cases.json       # corpus versionado de comparación diferencial
│   └── run_benchmark.py
├── tests/
│   └── test_cobol2py.py
└── .github/workflows/
    ├── tests.yml
    └── differential-benchmark.yml
```

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
```

`--format auto` es el valor predeterminado; como las columnas de secuencia en blanco pueden aparecer tanto en formato fijo como en fuentes libres indentadas, no siempre es posible inferir el formato con certeza.

GitHub Actions ejecuta las pruebas con Python 3.10–3.13 y compara, mediante el benchmark diferencial, 50 programas COBOL independientes contra GnuCOBOL. Los casos cubren `DISPLAY`, campos `PIC X/9`, `MOVE`, operaciones aritméticas, condiciones simples y compuestas, `IF` anidados, `PERFORM TIMES`, párrafos y tablas/subíndices. La suite de unittest mantiene además sus regresiones de runtime. La cobertura sigue limitada al corpus versionado y al subconjunto probado; no demuestra equivalencia semántica general ni certifica una migración. La compilación sintáctica de la salida, por sí sola, tampoco prueba equivalencia.

---

## Benchmark diferencial y evolución objetiva

El workflow `differential-benchmark.yml` compara cada programa del corpus con dos ejecuciones: el programa compilado por GnuCOBOL y el Python generado por el traductor. En cada push a `main`, pull request o ejecución manual, publica un informe Markdown en el resumen de GitHub Actions y conserva los informes JSON/Markdown como artefactos durante 90 días.

- **Métrica principal:** porcentaje de programas cuyo `stdout` y código de salida coinciden exactamente con GnuCOBOL.
- **Comparación entre versiones:** cuando existe una revisión base, ejecuta tanto el traductor anterior como el candidato sobre el mismo corpus de la revisión evaluada y muestra el cambio en puntos porcentuales.
- **Fallos visibles:** errores de compilación COBOL, traducción, ejecución Python y diferencias de salida cuentan como fallos del caso y aparecen en el detalle.
- **Corpus versionado:** `benchmarks/cases.json` define los 50 programas y las capacidades cubiertas. El corpus inicial contiene 2 fixtures previos y 48 programas independientes pequeños, cada uno enfocado en una o varias construcciones COBOL. Para añadir un caso, incorpora un programa COBOL autónomo en `samples/` y una entrada al manifiesto; no elimines casos difíciles solo para subir la puntuación.
- **Interpretación prudente:** la métrica mide únicamente estos fixtures; no equivale al porcentaje de COBOL del mundo real que se traduce correctamente. Los casos deben crecer en variedad y complejidad, no solo en cantidad.

Para ejecutar el benchmark localmente (requiere Python y GnuCOBOL):

```bash
python benchmarks/run_benchmark.py --translator cobol2py.py
```

---

## Hoja de ruta

**v0.0.5 — Semántica de datos y regresiones**
- Ampliar `VALUE` más allá de literales simples y cubrir valores figurativos y casos límite.
- Ampliar `MOVE` para campos numéricos con signo y escala decimal, manteniendo comparaciones diferenciales con GnuCOBOL.
- Añadir pruebas de semántica para campos alfanuméricos, precisión numérica, arrays y condiciones.

**v0.0.6 — Control de flujo**
- Implementar `EVALUATE/WHEN` con pruebas para `WHEN`, `WHEN OTHER` y anidamiento.
- Sustituir el estado global del árbol por una pila de bloques coherente; cubrir IF anidados y cierres malformados.

**v0.0.7 — Copybook resolver**
Localizar `COPY nombre.CPY.` en rutas explícitas y expandirlo antes del parseo. Detectar ciclos y dejar constancia de los archivos no resueltos.

**v0.0.8 — Jerarquía de datos**
Modelar los grupos COBOL y sus campos hijos sin aplanarlos ni simular una equivalencia que todavía no existe.

**v0.1.0 — Salida Java**
Reactivar el backend de Java con el mismo AST. `--lang java`.

**v0.2.0 — Ejecución con GnuCOBOL**
Compilar el COBOL con GnuCOBOL y ejecutarlo con trace. Mostrar el valor de cada variable por línea.

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
