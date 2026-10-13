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
    contador = "5"
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

**1. Los literales numéricos salen entrecomillados.**
`MOVE 123 TO WS-CODIGO` genera `ws_codigo = "123"`. El traductor no consulta el tipo del destino al emitir el literal. Requiere pasar la tabla de variables a `translate_statement`. Es el siguiente bug grande de la lista.

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
├── cobol2py.py          # el motor. un archivo. sin dependencias.
├── README.md            # este documento
├── LICENSE              # MIT
├── samples/
│   ├── hello.cbl        # ejemplo mínimo
│   └── realtest.cbl     # ejemplo con OCCURS, IFs, PERFORM
└── docs/
    
```

---

## Hoja de ruta

**v0.0.5 — Tipado de literales**
Pasar la tabla de variables a `translate_statement`. `MOVE 123 TO WS-CODIGO` genera `ws_codigo = 123`. Firma modificada.

**v0.0.6 — `EVALUATE`**
Mapear las ramas `WHEN` a `if/elif` en Python.

**v0.0.7 — Copybook resolver**
Preprocesador que localiza `COPY nombre.CPY.` en el directorio actual y expande su contenido antes del parseo.

**v0.0.8 — Grupos como dataclasses**
Los niveles `01` con hijos se convierten en `@dataclass` de Python, con los hijos como atributos tipados.

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
