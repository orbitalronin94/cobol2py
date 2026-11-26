# Estrategia de ingeniería para preservar la semántica COBOL

**Estado:** guía de diseño y priorización; no implica que todas las capacidades estén implementadas.  
**Ámbito:** traducción COBOL→Python y, cuando corresponda, análisis de modernización de sistemas empresariales.  
**Principio rector:** preservar el comportamiento observable y el modelo de datos del programa COBOL, no limitarse a producir Python sintácticamente válido.

Esta guía complementa [el análisis de fallos del benchmark externo](EXTERNAL_BENCHMARK_FAILURE_ANALYSIS.md), [el plan de recuperación](EXTERNAL_BENCHMARK_RECOVERY_PLAN.md), [la compatibilidad COBOL](compatibility.md) y el [agente de modernización](repo-modernization-agent.md). Las propuestas deben convertirse en cambios pequeños, pruebas diferenciales y evidencia medible. Una recomendación arquitectónica no es, por sí sola, una capacidad existente.

## 1. Reglas de diseño transversales

1. **La semántica COBOL es la referencia.** El comportamiento se contrasta con GnuCOBOL en el dialecto y configuración usados por el caso.
2. **La representación interna precede a la generación Python.** PIC, signo, escala, almacenamiento, codificación, overlays, límites de tabla y estados de E/S deben sobrevivir al análisis.
3. **No aplicar normalizaciones globales.** Una regla puede ser correcta para un campo o dialecto y errónea para otro. Las conversiones se aplican en los límites semánticos correspondientes.
4. **No ocultar comportamiento no soportado.** Si no puede preservarse con fidelidad, emitir un diagnóstico explícito en vez de generar una aproximación silenciosa.
5. **Cada cambio necesita una reproducción mínima.** Añadir primero una prueba que falle con la implementación anterior; después corregir y ejecutar regresiones.
6. **Separar traducción de modernización arquitectónica.** El traductor preserva el comportamiento del programa. La descomposición en servicios, APIs o adaptadores es una fase de modernización distinta y no debe alterar la equivalencia del traductor.

## 2. Aritmética decimal, punto fijo y redondeo

### Riesgo

Los `float` binarios no representan exactamente muchos decimales financieros. Además, el comportamiento COBOL depende de la definición PIC, las cláusulas de operación (por ejemplo, `ROUNDED` y `ON SIZE ERROR`), el dialecto y las opciones del compilador. Aplicar el redondeo por defecto de Python o imponer un único modo global puede cambiar resultados.

### Estrategia

- Modelar explícitamente **signo, escala, precisión y formato** de cada elemento numérico COBOL.
- Usar aritmética decimal exacta cuando corresponda; `decimal.Decimal` es la opción natural para valores decimales de punto fijo. No convertir indiscriminadamente todos los campos a `Decimal`: enteros, campos editados y representaciones de bytes tienen semánticas diferentes.
- Centralizar las operaciones en una capa de runtime (`cobol_math` o equivalente) que reciba metadatos del operando y destino.
- Implementar el redondeo como una propiedad de la operación COBOL que lo solicita. No imponer `ROUND_HALF_UP` a todas las operaciones sin comprobar dialecto y configuración.
- Aplicar truncamiento, redondeo, ajuste de escala y comprobación de tamaño en el punto correcto de transferencia al campo receptor, preservando también la precisión intermedia exigida por COBOL.
- Modelar explícitamente `ON SIZE ERROR` y el comportamiento de la operación cuando se produce desbordamiento.

### Ejemplo ilustrativo

```python
from decimal import Decimal, ROUND_HALF_UP

def quantize_cobol(
    value: Decimal,
    scale: int,
    rounding: str = ROUND_HALF_UP,
) -> Decimal:
    quantum = Decimal(1).scaleb(-scale)
    return value.quantize(quantum, rounding=rounding)
```

El ejemplo muestra cómo hacer explícito el modo de redondeo; no establece que `ROUND_HALF_UP` sea correcto para todos los programas COBOL. El modo efectivo debe proceder de la semántica del caso.

### Pruebas necesarias

- Valores positivos, negativos, cero, empates exactos y valores próximos al límite de escala.
- Suma, resta, multiplicación y división con escalas distintas.
- Destinos con PIC de distinta precisión y signo.
- Operaciones con y sin `ROUNDED`, y con `ON SIZE ERROR`.
- Comparación exacta de valores y salida frente a GnuCOBOL.

## 3. COMP-3: decimal empaquetado

### Riesgo

`COMP-3` almacena dígitos decimales empaquetados en nibbles; el nibble final codifica el signo. Interpretarlo como entero binario mediante `int.from_bytes()` no reproduce su representación.

### Estrategia

- Implementar un codec de packed decimal consciente de PIC: número de dígitos, escala, signo y longitud física.
- Decodificar cada nibble como dígito decimal y validar el nibble de signo. Los valores de signo aceptados deben configurarse según el dialecto/entorno; no asumir que todos los productores usan exactamente el mismo conjunto.
- Implementar también la codificación inversa cuando el programa escriba registros.
- Rechazar o diagnosticar nibbles inválidos en lugar de reinterpretarlos silenciosamente.
- Mantener separados el valor numérico y su representación física para que `MOVE`, overlays y E/S puedan conservar el layout.
- Generar fixtures de datos con GnuCOBOL para positivos, negativos, cero, límites de PIC y escalas diferentes.

### Integraciones externas

Herramientas como `coboljsonifier` o `pycobol2csv` pueden evaluarse como referencias o utilidades de ingesta. No se convierten en dependencias ni sustituyen el codec del runtime sin comprobar compatibilidad, mantenimiento, licencia y fidelidad con los copybooks del proyecto.

## 4. REDEFINES y memoria compartida

### Riesgo

`REDEFINES` permite interpretar la misma región de almacenamiento mediante layouts alternativos. No equivale necesariamente a una unión discriminada: COBOL puede leer o escribir cualquiera de las vistas, incluso sin un tag explícito.

### Estrategia

- Representar la región subyacente como almacenamiento compartido con vistas tipadas superpuestas.
- Mantener offsets, longitudes, alineación y reglas de representación de cada campo.
- Propagar las escrituras entre vistas porque todas observan los mismos bytes.
- Usar una unión discriminada de alto nivel solo cuando el programa tenga un discriminante real y el análisis pueda demostrar que gobierna la selección de vista.
- No sustituir automáticamente overlays por jerarquías de dataclasses si eso rompe aliasing o mutaciones compartidas.
- Probar lecturas y escrituras cruzadas entre la definición original y cada redefinición, incluyendo campos numéricos y alfanuméricos.

Librerías de parsing pueden servir como referencia, pero cualquier integración debe demostrar que preserva memoria compartida y layouts COBOL, no solo que puede generar clases Python.

## 5. EBCDIC y codificación de registros

### Riesgo

Los archivos de mainframe pueden usar EBCDIC. Decodificar como UTF-8/ASCII sin conocer el CCSID puede corromper datos. Tampoco todos los archivos COBOL usan EBCDIC: la codificación depende del entorno y del contrato de archivo.

### Estrategia

- Tratar la codificación como metadato explícito del archivo o interfaz, nunca como una suposición global.
- Convertir en las fronteras de E/S: bytes externos → representación interna y representación interna → bytes de salida.
- Configurar el codec concreto (por ejemplo, `cp037` o `cp1141`) a partir de la especificación real del sistema.
- Mantener disponible la representación original de bytes cuando sea necesaria para overlays, comparaciones o campos no textuales.
- Probar ida y vuelta de lectura/escritura, caracteres nacionales, espacios, signos y bytes no asignados.
- No convertir campos binarios o packed decimal como si fueran texto.

Las herramientas de ingesta basadas en copybooks pueden evaluarse, pero no eliminan la necesidad de verificar CCSID, layout y reglas de cada archivo.

## 6. PERFORM, THRU y semántica de párrafos

### Riesgo

`PERFORM A THRU B` ejecuta un rango de párrafos y está condicionado por el orden de los párrafos, el flujo de caída secuencial, transferencias `GO TO`, retornos de PERFORM y otras reglas de control. Convertirlo sin más en una función monolítica o dividir cada párrafo en funciones puede cambiar el comportamiento.

### Estrategia

- Construir una representación explícita de párrafos y secciones, con su orden y aristas de control.
- Modelar `PERFORM` y `PERFORM THRU` como ejecución de rangos con retorno correcto, preservando el flujo secuencial.
- Mantener la semántica de `GO TO`, `EXIT PARAGRAPH`, `EXIT PERFORM`, pruebas antes/después y anidamiento en los casos soportados.
- Extraer funciones Python por párrafo solo cuando el análisis de flujo demuestre que la extracción preserva entradas, salidas, retornos y efectos.
- Generar un mapa de trazabilidad párrafo COBOL → bloque o función Python como artefacto de diagnóstico, no como sustituto de la equivalencia.

### Pruebas necesarias

Rangos con párrafos intermedios, caída secuencial, PERFORM anidado, salida anticipada, GO TO dentro/fuera del rango y bucles con contadores. Validar tanto terminación como salida y código de retorno.

## 7. PIC: límites, truncamiento y desbordamiento

### Riesgo

Python permite que los enteros crezcan sin límite y no aplica automáticamente el tamaño declarado en PIC. Una asignación a un campo COBOL sí puede ajustar escala, truncar, rellenar o producir una condición de error según la operación y el dialecto.

### Estrategia

- Derivar límites, signo, escala y representación desde PIC y USAGE.
- Aplicar las reglas al almacenar en el campo receptor, no necesariamente después de cada operación intermedia.
- Diferenciar truncamiento de redondeo: no usar `ROUND_DOWN` como sustituto universal sin considerar signo y semántica exacta de la operación.
- Implementar condiciones de tamaño (`ON SIZE ERROR`) y el efecto sobre el destino.
- Preservar el formato de campos editados y el relleno/truncamiento de campos alfanuméricos.
- Añadir pruebas de frontera: mínimo, máximo, un valor por encima, negativos, decimales descartados y signos.

La validación debe estar en el runtime semántico y en la generación de asignaciones, no depender de decoradores Python genéricos que desconozcan PIC y contexto de operación.

## 8. OCCURS y OCCURS DEPENDING ON (ODO)

### Riesgo

`OCCURS` fijo define una tabla con capacidad conocida. `OCCURS DEPENDING ON` añade una longitud lógica variable acotada por un máximo. Confundir capacidad física y número de elementos activos puede procesar datos residuales o desplazar campos posteriores.

### Estrategia

- Conservar mínimo, máximo, contador DEPENDING ON, stride y layout físico.
- Separar capacidad reservada de ocurrencias lógicamente activas.
- Validar el contador contra los límites declarados y reproducir el comportamiento COBOL configurado cuando esté fuera de rango.
- Limitar iteraciones y referencias lógicas al número activo, manteniendo el almacenamiento y offsets necesarios para el registro.
- Al serializar, respetar la longitud variable del registro y las reglas de escritura del entorno; no asumir que basta con truncar una lista.
- Probar límites mínimo/máximo, cero cuando sea admisible, contador fuera de rango, tablas anidadas y campos que siguen a una tabla ODO.

Una lista Python puede ser una vista de alto nivel, pero no debe borrar el layout físico ni la diferencia entre capacidad y longitud activa.

## 9. FILE STATUS y archivos de ancho fijo

### Riesgo

En COBOL, las operaciones de E/S actualizan `FILE STATUS`; muchos estados son resultados que el propio programa inspecciona y no excepciones fatales. La lectura genérica por líneas tampoco preserva necesariamente registros de longitud fija, bytes ni formatos variables.

### Estrategia

- Introducir una abstracción de archivo COBOL que conozca organización, acceso, longitud de registro, claves, encoding y estado.
- Actualizar la variable FILE STATUS después de cada operación conforme al resultado y al dialecto/runtime de referencia.
- Modelar estados habituales (por ejemplo, `00`, `10`, `22`, `23`) como códigos observables. No lanzar siempre una excepción: el programa COBOL puede continuar y tomar decisiones según el código.
- Preservar reglas de OPEN, READ, WRITE, REWRITE, DELETE, START, CLOSE, EOF y acceso secuencial/relativo/indexado dentro del subconjunto implementado.
- Leer registros por longitud y layout cuando el contrato sea de ancho fijo; no usar `readline()` como sustituto universal.
- Distinguir registros de longitud fija, variable, delimitados y organizaciones indexadas.
- Para estados o modalidades no soportados, emitir diagnóstico explícito y evitar bucles que no progresan.

### Pruebas necesarias

Archivo inexistente, EOF, clave duplicada, clave ausente, READ tras EOF, registros cortos/largos, espacios finales, bytes EBCDIC, REWRITE y estados posteriores a cada operación. Comparar los archivos producidos byte a byte cuando el formato lo requiera.

## 10. CICS, MQ, VSAM y transacciones externas

### Riesgo

Una transacción CICS puede abarcar actualizaciones y recursos externos con garantías que no se reproducen traduciendo sentencias a llamadas Python aisladas. `SYNCPOINT` y `SYNCPOINT ROLLBACK` expresan límites transaccionales observables.

### Estrategia de modernización

- Identificar límites transaccionales, recursos participantes, puntos de sincronización y efectos externos antes de proponer una arquitectura destino.
- Mapear `SYNCPOINT` y rollback a una unidad de trabajo transaccional solo cuando el gestor de destino ofrezca garantías equivalentes para todos los recursos involucrados.
- Usar adaptadores para CICS, MQ, VSAM u otros servicios cuando deban permanecer en la plataforma existente; documentar contratos, errores, reintentos e idempotencia.
- No sustituir una llamada CICS por HTTP ni una operación MQ por una llamada genérica sin definir protocolo, entrega, orden, correlación y recuperación.
- Si no existe equivalencia transaccional, documentar la brecha y requerir diseño explícito; no prometer ACID por el mero uso de `commit`/ `rollback`.

Esta área pertenece principalmente al agente/plan de modernización de sistemas. El traductor de un programa aislado debe diagnosticar estas dependencias y no simular que las ha migrado.

## 11. Pruebas de equivalencia como hilo conductor

### Principio

Que el Python generado compile o “funcione” no demuestra equivalencia. La referencia es la ejecución del COBOL original con el mismo entorno y los mismos datos de entrada.

### Arnés diferencial

- Ejecutar COBOL y Python con entradas idénticas, límites equivalentes y variables de entorno controladas.
- Comparar stdout byte a byte y código de retorno, que son los criterios del benchmark externo actual.
- Para pruebas de integración, comparar también archivos generados, registros, estados de archivo, mensajes y cambios persistentes cuando formen parte del contrato.
- Capturar fuente, Python generado, stderr, traceback y diffs por caso, respetando las restricciones de redistribución del corpus.
- Convertir cada discrepancia reproducible en un fixture mínimo y clasificarla por causa raíz.
- Ejecutar regresiones antes del benchmark; después medir exactamente la muestra, SHA y protocolo vigentes.

### Verificación formal y herramientas externas

Solvers SMT como Z3 y herramientas de verificación formal pueden ser útiles para subconjuntos acotados, invariantes o funciones aritméticas. No se debe afirmar equivalencia formal de un programa completo por verificar expresiones aisladas. Proyectos externos como IRONPROOF o `cobol-bridge-mcp` deben evaluarse mediante pruebas reproducibles, alcance real, mantenimiento y licencia antes de integrarlos o citarlos como soporte del proyecto.

## 12. Modernización incremental: Strangler Fig y shadow mode

### Riesgo

Una reescritura completa (*big bang*) puede concentrar demasiado riesgo y hacer difícil localizar regresiones de negocio. Sin embargo, el patrón Strangler Fig no es una transformación automática que el traductor pueda aplicar por sí solo.

### Estrategia

1. Inventariar programas, copybooks, JCL, SQL, archivos, colas, transacciones y dependencias.
2. Identificar límites funcionales y contratos de entrada/salida; priorizar componentes de bajo riesgo y dependencias comprensibles.
3. Envolver el sistema existente mediante fachadas o adaptadores sin cambiar inicialmente su comportamiento.
4. Migrar una capacidad cada vez, manteniendo el COBOL para las rutas aún no migradas.
5. Cuando sea seguro, ejecutar el nuevo componente en *shadow mode* con entradas equivalentes y comparar efectos observables sin duplicar efectos irreversibles.
6. Desviar tráfico gradualmente solo después de validar equivalencia, observabilidad, recuperación y operación.
7. Retirar el componente COBOL únicamente cuando existan evidencias, plan de rollback y aceptación operativa.

El agente de modernización puede ayudar con inventario, mapas de dependencias, riesgos y planes. No debe presentar una recomendación como una migración ya ejecutada.

## 13. Priorización para cobol2py

La secuencia concreta debe decidirse a partir de fallos reproducidos y no de una lista fija de tecnologías:

| Área | Evidencia que debe reunirse | Entregable técnico esperado |
|---|---|---|
| Aritmética / PIC | Diffs numéricos y asignaciones de frontera | Runtime decimal y asignación tipada |
| COMP-3 | Copybooks, bytes y valores generados por GnuCOBOL | Codec empaquetado con pruebas ida/vuelta |
| REDEFINES | Layouts y lecturas/escrituras cruzadas | Almacenamiento compartido con vistas |
| EBCDIC | Contrato de archivo y CCSID real | Codec configurable en fronteras de E/S |
| PERFORM THRU | Trazas de párrafos y aristas de control | Modelo de flujo con retorno preservado |
| OCCURS / ODO | Layout, contador y offsets de campos posteriores | Tabla con capacidad y longitud lógica |
| FILE STATUS | Estado tras cada operación | Runtime de E/S con códigos observables |
| CICS / MQ / VSAM | Inventario de recursos y límites de transacción | Diagnósticos y plan de adaptadores |
| Equivalencia | Casos diferenciales reproducibles | Regresiones y scorecard por SHA |

### Puertas de aceptación para cada mejora

1. Caso mínimo reproducible antes del cambio.
2. Prueba unitaria de análisis/layout/runtime.
3. Comparación diferencial con GnuCOBOL que cubra salida, retorno y efectos relevantes.
4. Suite de regresión completa verde.
5. Ninguna relajación del corpus, timeout, selección de casos, checksum o criterio exacto del benchmark.
6. Resultado externo registrado para el SHA exacto; no atribuir mejoras al cambio si se mezclan varias hipótesis.
7. Documentación actualizada con la diferencia entre implementado, parcial, experimental y no soportado.

## 14. Límites y honestidad técnica

- Esta guía define una estrategia; no afirma que todas las áreas estén implementadas en el traductor.
- No todas las sugerencias de arquitectura empresarial pertenecen al generador Python: CICS, MQ, VSAM y Strangler Fig requieren análisis del sistema y decisiones operativas.
- Las bibliotecas citadas son referencias para evaluar, no dependencias aprobadas.
- Una traducción sintácticamente válida puede seguir siendo semánticamente incorrecta.
- La única evidencia de mejora en el ranking es el benchmark externo ejecutado con el protocolo vigente y asociado al SHA exacto.
