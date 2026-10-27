# Agente de modernización de repositorios

## Estado

La primera iteración es un **planificador estático y determinista**, no un agente LLM autónomo. No instala dependencias, no ejecuta código del sistema analizado y no modifica fuentes COBOL. Genera inventario, referencias de dependencias por nombre y una propuesta de fases que una persona puede revisar.

Esta frontera es deliberada: antes de permitir que un agente cambie un sistema legado, debe poder explicar qué archivos ha encontrado, qué referencias ha resuelto y qué evidencias validan cada modificación.

## Uso

Desde la raíz del repositorio:

```bash
python cobol2py_agent.py /ruta/al/sistema \
  --out reports/migration-plan.md \
  --json-out reports/migration-plan.json
```

La ruta puede ser `.` para analizar el repositorio actual. Para recibir JSON por stdout:

```bash
python cobol2py_agent.py /ruta/al/sistema --stdout-json --json-out reports/plan.json
```

El análisis omite directorios de control y salida comunes (`.git`, entornos virtuales, `build`, `dist`, etc.). Busca archivos COBOL, copybooks, JCL y SQL con extensiones conocidas, además de archivos sin extensión cuyo contenido parezca COBOL. El informe Markdown y el JSON incluyen inventario, dependencias detectadas, referencias no resueltas, construcciones que requieren revisión y una secuencia recomendada de migración.

## Modelo de datos

El JSON usa `schema_version: 1` y contiene:

- `summary`: contadores del inventario.
- `files`: ruta relativa, tipo, `PROGRAM-ID`, referencias encontradas, indicadores de riesgo y número de líneas.
- `dependencies`: aristas `source -> target` con relación y símbolo.
- `unresolved_references`: referencias para las que no se encontró un destino local.
- `ambiguous_references`: referencias con más de un destino local posible, incluyendo la lista de rutas candidatas.
- `recommended_sequence`: etapas y criterios de salida.
- `review_first`: módulos con construcciones que merecen análisis adicional.
- `limitations`: límites conocidos de este análisis.

Las relaciones se resuelven por nombres de archivo y `PROGRAM-ID`; no son un análisis completo de enlazado. Si un símbolo tiene varios destinos posibles, el informe lo conserva como dependencia y lo señala también en `ambiguous_references` para que no se trate como resuelto de forma unívoca. Los comentarios COBOL, JCL y SQL reconocidos se excluyen del escaneo; la extracción sigue basada en expresiones regulares, así que literales y construcciones poco habituales aún pueden producir falsos positivos. Las llamadas dinámicas, convenciones de nombres propias, bibliotecas externas y artefactos generados pueden quedar sin resolver. Revisa el informe antes de usarlo como plan de trabajo.

## Flujo previsto para una modernización de empresa

1. **Descubrir** el inventario y guardar el informe como baseline versionado.
2. **Completar el contexto**: dialecto/compilador, parámetros de build, copybooks externos, JCL, SQL, CICS/IMS, archivos, colas y servicios.
3. **Cerrar dependencias**: revisar aristas y clasificar cada referencia sin resolver como externa, dinámica, ausente o falso positivo.
4. **Agrupar por componentes**: programas que comparten copybooks, llamadas o cadenas JCL.
5. **Elegir un piloto representativo** y registrar entradas, salidas, códigos de retorno, archivos y efectos externos observables.
6. **Traducir con el motor existente** y ampliar las pruebas diferenciales contra el entorno COBOL de referencia.
7. **Revisar y aceptar por oleadas**: ningún cambio se acepta solo porque el código destino compile.

## Arquitectura objetivo

El planificador es el primer bloque de una arquitectura de agente, con límites explícitos:

- **Repository analyzer**: inventario y grafo estático.
- **Migration planner**: orden de trabajo, criterios de salida y riesgos.
- **Translator adapter**: invoca el traductor determinista actual y captura diagnósticos.
- **Verification engine**: compila el destino y compara comportamiento con la referencia COBOL, incluidos efectos observables que el proyecto pueda reproducir.
- **Divergence analyzer**: agrupa fallos por caso, salida, estado y dependencia.
- **Repair loop** (futuro): propone un parche aislado, vuelve a ejecutar pruebas y requiere revisión cuando la evidencia no es concluyente.

El modelo de lenguaje, si se añade, debe proponer explicaciones o cambios acotados; no sustituye al parser, las reglas semánticas ni las pruebas. Las escrituras deben limitarse a un workspace/branch aislado, con diff revisable y sin acceso a credenciales de producción. No se integra ni se ejecuta automáticamente ninguna acción de GitHub.

## Pruebas

```bash
python -m unittest discover -s tests -p 'test_modernize_agent.py' -v
python -m unittest discover -s tests -v
```

Las pruebas de este módulo usan repositorios temporales sintéticos y no requieren GnuCOBOL. La validación semántica de traducciones sigue requiriendo las pruebas unitarias del traductor y, cuando esté disponible, el benchmark diferencial documentado en [architecture.md](architecture.md).

## Límites y seguridad

- El escaneo es heurístico; no interpreta toda la gramática COBOL ni dialectos de proveedor.
- La resolución por nombre no prueba que una dependencia se use en ejecución.
- No se ejecutan los programas encontrados ni se invocan comandos externos.
- No se cambian archivos fuente del sistema analizado.
- Un informe sin riesgos detectados no significa que el sistema sea de bajo riesgo.
- No se afirma equivalencia semántica. Cada oleada necesita revisión humana y evidencia de pruebas.


## Flujo piloto integrado

`tools/modernize_pilot.py` conecta el inventario estático con la traducción del subconjunto COBOL y una comprobación de sintaxis del Python generado. Escribe inventario Markdown/JSON, fuentes traducidos y un informe por programa; no ejecuta los programas generados y declara expresamente que la equivalencia semántica no se ha probado. El directorio de salida debe quedar fuera del árbol analizado para no contaminar el inventario en ejecuciones repetidas.

Ejemplo reproducible desde la raíz del repositorio:

```bash
python tools/modernize_pilot.py samples --out-dir /tmp/cobol2py-pilot
python -m unittest discover -s tests -p 'test_modernize_pilot.py' -v
```

El piloto falla si una traducción no puede generarse o si el Python generado no pasa `compile()`; los diagnósticos de compatibilidad se conservan en `translation-report.json`. En la ejecución CI del commit `1fb78c6`, el árbol `samples` produjo 108 traducciones, cero errores de sintaxis y cero errores de traducción; 36 fuentes tienen diagnósticos que requieren revisión. Para demostrar equivalencia de comportamiento, ejecutar además el benchmark diferencial con GnuCOBOL.
