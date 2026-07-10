# Synapse: Manual de Arquitectura y Filosofía Base

## 1. Visión General
Synapse es un lenguaje de programación nativo, compilado y de grado de sistemas. Su objetivo principal es servir como los cimientos para un sistema operativo enfocado en la seguridad, el cifrado local y la resiliencia. 

No es un lenguaje de scripting; es un motor de control de calidad estricto. La filosofía rectora de Synapse se denomina **"El Pacto"**: el compilador es un auditor implacable que prefiere detener la compilación ante la más mínima ambigüedad antes que permitir la generación de código inseguro o comportamiento indefinido.

## 2. El Ecosistema de Compilación
El compilador de Synapse es **Auto-Alojado (Self-Hosted)**. Está escrito íntegramente en Synapse y compila su propio Árbol de Sintaxis Abstracta (AST).

El flujo del *pipeline* es estrictamente lineal:
1. **Lexer (`lexer.syn`):** Transforma el texto crudo en tokens.
2. **Parser (`parser.syn`):** Descenso recursivo puro. Convierte tokens en el AST (`ast_nodes.syn`).
3. **Analizador Semántico (`analizador_semantico.syn`):** El corazón de la seguridad. Aplica resolución de tipos, verifica el ciclo de vida de las variables y garantiza el "Ownership".
4. **Generador C (`generator.syn`):** Traduce el AST validado a código C nativo (usando el estándar más estricto, sin inferencia `auto` delegada a GCC).
5. **Backend (GCC/Clang):** Genera el binario final (ej. `.exe` o ELF) inyectando sanitizadores (`-fsanitize`) durante los tests.

## 3. Reglas Sintácticas de Hierro
Para minimizar la deuda técnica y la fricción visual, Synapse elimina la redundancia:
* **Indentación Estricta:** El alcance (scope) se define exclusivamente por la indentación (múltiplos de 4 espacios), al estilo Python.
* **Cero Llaves:** El uso de `{ }` está estrictamente prohibido en la sintaxis de control. Los bloques se abren con dos puntos (`:`).
* **Firma de Archivo:** Todo archivo válido debe iniciar declarando el idioma del compilador (ej. `#lang: es`).

## 4. Los Pilares de Seguridad (El Pacto)

### 4.1. Memory Safety (Ownership & Borrowing)
Synapse no utiliza Recolector de Basura (Garbage Collector) ni permite `malloc`/`free` manual. Implementa un modelo de **Posesión Única**.
* Un valor tiene un único dueño.
* Cuando el dueño sale de *scope*, el compilador inyecta la liberación de memoria.
* Las transferencias a funciones ejecutan un *move* por defecto. Intentar usar una variable movida genera un error semántico estático (*Use-After-Move*).

### 4.2. Manejo de Errores Determinista (ADTs)
No existen los retornos nulos ni los códigos de error enteros (`-1`). Los errores se manejan mediante Tipos Algebraicos (Uniones Etiquetadas en C).
* Tipos principales: `Resultado<T, E>` y `Opcion<T>`.
* El desempaquetado es obligatorio mediante la instrucción `coincidir`.

**Ejemplo de sintaxis esperada:**
```synapse
resultado = leer_archivo("config.txt")
coincidir resultado:
    ok(datos) =>
        escribir_linea(datos)
    err(motivo) =>
        escribir_linea(motivo)

4.3. Concurrencia Aislada
El estado mutable compartido entre hilos está prohibido.

La instrucción lanzar transfiere el ownership de las variables capturadas al nuevo hilo.

La comunicación inter-hilos se realiza exclusivamente mediante paso de mensajes (Canales de std.concurrencia).

4.4. Diseño por Contrato (Design by Contract)
Para auditar código (incluso aquel generado por IA), las funciones implementarán contratos lógicos que el generador traduce a aserciones de metal.

requiere: para pre-condiciones.

garantiza: para post-condiciones.

5. Developer Experience (DX) y Axon
Synapse LSP: El lenguaje cuenta con un demonio LSP nativo (synapse_lsp) que se comunica mediante stdio (JSON-RPC 2.0). Emite diagnósticos en tiempo real y rechaza fallos sintácticos sin colapsar.

Axon (Gestor de Paquetes): Un sistema inmutable. Axon prohíbe la ejecución de scripts arbitrarios en la máquina del desarrollador (preinstall/postinstall). Solo clona código fuente validado criptográficamente.

