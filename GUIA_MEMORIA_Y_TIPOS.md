# Synapse: Guía de Gestión de Memoria y Tipos Algebraicos

## 1. Filosofía de Memoria (Zero-Cost Safety)
Synapse garantiza la seguridad de memoria estática sin depender de un recolector de basura (Garbage Collector). El compilador actúa como un auditor estricto en tiempo de compilación mediante el sistema de **Ownership (Posesión)**.

## 2. Reglas de Ownership
El `AnalizadorSemantico` impone tres reglas absolutas:
1. **Un solo dueño:** Cada valor en memoria tiene una única variable propietaria en todo momento.
2. **Ciclo de vida atado al scope:** Cuando el propietario sale de su bloque de indentación (scope), el compilador inserta automáticamente la directiva de liberación (`pool_free` o equivalente en C).
3. **Transferencia por defecto (Move Semantics):** Asignar una variable a otra o pasarla como argumento a una función transfiere la propiedad.

### 2.1. Infracción: Use-After-Move
Cualquier intento de acceder a un recurso después de haberlo transferido resultará en un fallo fatal de compilación.

**Ejemplo de código bloqueado:**
```synapse
funcion procesar(t: Tensor) -> nulo:
    // t es consumido aquí

funcion principal() -> nulo:
    t1 = crear_tensor(10)
    procesar(t1)       // Ownership transferido
    imprimir(t1)       // ERROR SEMÁNTICO: Use-after-move

3. Tipos Algebraicos (ADTs) y Uniones Etiquetadas
Synapse prohíbe los valores nulos invisibles. El estado de error o ausencia se modela a través de Tipos Algebraicos, representados en C como Tagged Unions (Uniones Etiquetadas).

3.1. Estructura Interna
Un ADT en Synapse se traduce en C agrupando los valores en un bloque union para ahorrar memoria, discriminados por un tag numérico.
El Generador resuelve estáticamente el tipo exacto para evitar "casteos" inseguros.

3.2. Desempaquetado Seguro (coincidir)
Es ilegal intentar acceder al valor interno de un Resultado u Opcion sin verificar primero su etiqueta. Esto se fuerza a través de la sintaxis coincidir.

Gramática estricta:

Fragmento de código
// Nótese la estricta indentación y la ausencia total de llaves {}
op = buscar_registro()
coincidir op:
    algun(valor) =>
        procesar(valor)
    ninguno =>
        registrar_error("No encontrado")
4. Bloques Inseguros (El escape de metal)
Para interactuar con llamadas al sistema o hardware crudo, Synapse permite el uso de punteros. Esto se debe encapsular en bloques que el equipo de QA auditará con sanitizadores externos (Valgrind, ASan). Todo lo que ocurre aquí es responsabilidad exclusiva del programador.


***

### Documento 3: `ESPECIFICACION_LSP_DX.md`

```markdown
# Synapse: Especificación del Language Server Protocol (LSP)

## 1. Arquitectura del Demonio
Para proveer experiencia de desarrollador (DX) de grado industrial, Synapse expone un demonio LSP nativo integrado en el mismo binario del compilador, invocable mediante la bandera `--lsp`.

* **Canal de comunicación:** Estrictamente a través de `stdio` (entrada y salida estándar).
* **Protocolo:** JSON-RPC 2.0.
* **Resiliencia:** El proceso LSP no debe ejecutar `sys.exit()` bajo ninguna circunstancia derivada de errores de código del usuario. Cualquier excepción del `Lexer`, `Parser` o `AnalizadorSemantico` debe ser capturada y transformada.

## 2. Lectura y Transporte (La Regla de los Bytes)
El servidor lee la cabecera HTTP-like byte a byte. 
**Advertencia Crítica de Implementación:** El valor de `Content-Length` dictamina el número exacto de *bytes* a leer, no de *caracteres*. En Python, esto obliga al uso de `len(cuerpo.encode("utf-8"))`. Usar conteo de caracteres corromperá el canal JSON-RPC al encontrar caracteres Unicode (ej. tildes).

## 3. Manejo de Coordenadas
El compilador de Synapse utiliza índices basados en 1 (1-based) para las líneas y 0 para las columnas. LSP exige índices estrictamente 0-based. 

**Algoritmo de traducción:**
* `lsp_line = synapse_line - 1`
* `lsp_character = synapse_columna`

## 4. Formato de Diagnóstico (`publishDiagnostics`)
Cuando el AST colapsa por un error, el servidor emite una notificación al editor.

**Estructura JSON estricta:**
```json
{
  "jsonrpc": "2.0",
  "method": "textDocument/publishDiagnostics",
  "params": {
    "uri": "file:///ruta/al/archivo.syn",
    "diagnostics": [
      {
        "range": {
          "start": { "line": 5, "character": 10 },
          "end": { "line": 5, "character": 11 }
        },
        "severity": 1,
        "source": "synapse",
        "message": "Error Semántico: Variable 'x' movida previamente."
      }
    ]
  }
}
Un array vacío de diagnostics indica que los errores previos han sido resueltos.


***

### Documento 4: `ESPECIFICACION_AXON.md`

```markdown
# Axon: Arquitectura del Ecosistema y Cadena de Suministro

## 1. El Problema a Resolver
Axon es el gestor de paquetes descentralizado y oficial de Synapse. Su diseño responde directamente a la crisis de seguridad de las cadenas de suministro modernas (ej. ataques en npm o pip). El objetivo es la inmutabilidad y la observabilidad de terceros.

## 2. Reglas de Hierro del Gestor de Paquetes
Para garantizar que un proyecto compile y se ejecute de la misma forma en cualquier máquina, Axon aplica tres restricciones innegociables:

1. **Cero Ejecución Arbitraria:** Axon prohíbe terminantemente la existencia de directivas tipo `preinstall` o `postinstall`. La descarga de una dependencia es una operación de pura transferencia de texto.
2. **Bloqueo Criptográfico por Defecto:** Todo paquete importado debe resolverse contra un hash SHA-256 declarado en el archivo de candado (`axon.lock`). Si un solo byte del repositorio de origen cambia silenciosamente, Axon rechazará la compilación de inmediato.
3. **Distribución de Código Fuente Crudo:** No se descargan binarios precompilados opacos. Todo se descarga en texto plano `.syn` y es compilado desde cero por el compilador local, garantizando la trazabilidad.

## 3. El Manifiesto (`axon.toml`)
Todo proyecto Synapse está regido por un archivo estricto en la raíz.

**Estructura esperada:**
```toml
[proyecto]
nombre = "servidor_core"
version = "1.0.0"
punto_entrada = "src/main.syn"

[dependencias]
# Las dependencias apuntan a URIs definitivas con commits o tags inmutables
cripto_lib = { git = "[https://github.com/usuario/cripto.git](https://github.com/usuario/cripto.git)", rev = "a1b2c3d" }
4. El Monolito Operativo
Para evitar la fragmentación del ecosistema, todas las herramientas de Axon están inyectadas dentro del propio binario de Synapse. Un desarrollador interactúa con el ciclo de vida completo mediante subcomandos:

synapse construir: Resuelve el árbol del .toml, compila y enlaza el ejecutable final.

synapse probar: Ejecuta la suite de testing integrando los sanitizadores de memoria en C (Valgrind, ASan).

synapse formatear: Aplica la guía de estilo oficial sobre el AST.