Synapse: Manual de Arquitectura y Filosofía Base (v3.0)
1. Visión General
Synapse es un lenguaje de programación de propósito general, nativo, compilado y de alto rendimiento. Su objetivo principal es superar los cuellos de botella estructurales de Python (lentitud de ejecución, ausencia de concurrencia real por el GIL, tipado dinámico frágil y recolector de basura), ofreciendo una sintaxis limpia y amigable pero con la potencia, velocidad de ejecución y seguridad de un lenguaje de grado de sistemas.

No es un lenguaje de scripting interpretado; es un motor de control de calidad estricto. La filosofía rectora de Synapse se denomina "El Pacto": el compilador es un auditor implacable que prefiere detener la compilación ante la más mínima ambigüedad antes que permitir la generación de código inseguro o comportamiento indefinido.

2. El Ecosistema de Compilación
El compilador de Synapse es Auto-Alojado (Self-Hosted). Está escrito íntegramente en Synapse y compila su propio Árbol de Sintaxis Abstracta (AST Canónico).

El flujo del pipeline es estrictamente lineal:

Lexer (lexer.syn): Transforma el texto crudo en tokens.

Parser (parser.syn): Descenso recursivo puro. Convierte tokens en el AST canónico (ast_nodes.syn).

Analizador Semántico (analizador_semantico.syn): El corazón de la seguridad. Aplica resolución de tipos, verifica el ciclo de vida de las variables y garantiza el "Ownership".

Generador C (generator.syn): Traduce el AST validado a código C nativo optimizado con -O2 y aceleración SIMD (sin inferencia auto delegada a GCC).

Backend (GCC/Clang): Genera el binario final de alto rendimiento inyectando sanitizadores (-fsanitize) durante los tests.

3. Reglas Sintácticas de Hierro
Para minimizar la deuda técnica y la fricción visual, Synapse elimina la redundancia heredando la legibilidad visual de Python pero con tipado estricto:

Indentación Estricta: El alcance (scope) se define exclusivamente por la indentación (múltiplos de 4 espacios).

Cero Llaves: El uso de { } está estrictamente prohibido en la sintaxis de control. Los bloques se abren con dos puntos (:).

Firma de Archivo: Todo archivo válido debe iniciar declarando el idioma del compilador (ej. #lang: es).

4. Los Pilares de Seguridad (El Pacto)
4.1. Memory Safety (Ownership & Borrowing)
Synapse no utiliza Recolector de Basura (Garbage Collector) ni permite malloc/free manual. Implementa un modelo de Posesión Única.

Un valor tiene un único dueño.

Cuando el dueño sale de scope, el compilador inyecta la liberación de memoria de forma determinista.

Las transferencias a funciones ejecutan un move por defecto. Intentar usar una variable movida genera un error semántico estático (Use-After-Move).

4.2. Manejo de Errores Determinista (ADTs)
No existen los retornos nulos ni los códigos de error enteros (-1). Los errores se manejan mediante Tipos Algebraicos (Uniones Etiquetadas).

Tipos principales: Resultado<T, E> y Opcion<T>.

El desempaquetado es obligatorio mediante la instrucción coincidir.

Ejemplo de sintaxis esperada:

Fragmento de código
resultado = leer_archivo("config.txt")
coincidir resultado:
    ok(datos) =>
        escribir_linea(datos)
    err(motivo) =>
        escribir_linea(motivo)
4.3. Concurrencia Aislada (Adiós al GIL)
El estado mutable compartido entre hilos está estrictamente prohibido a nivel de compilación.

La instrucción lanzar transfiere el ownership de las variables capturadas al nuevo hilo.

La comunicación inter-hilos se realiza exclusivamente mediante paso de mensajes seguros (Canal<T> de std.concurrencia), permitiendo paralelismo masivo en múltiples núcleos de CPU sin deadlocks.

4.4. Diseño por Contrato (Design by Contract)
Para auditar código de alta fiabilidad (incluso aquel asistido por IA), las funciones implementarán contratos lógicos que el generador traduce a aserciones de metal:

requiere: para precondiciones.

garantiza: para postcondiciones.

5. Developer Experience (DX), OpenSyn y Axon
Synapse LSP y OpenSyn: El lenguaje cuenta con un demonio LSP nativo (synapse_lsp) integrado con OpenSyn, un motor cognitivo local impulsado por llama.cpp que corre 100% privado en el hardware del usuario. OpenSyn opera con un pipeline RAG quirúrgico basado en el AST y negociación dinámica de contexto (n_ctx), ofreciendo asistencia en tiempo real, refactorización y traducción asistida de código legacy (como proyectos completos de Python) a Synapse.

Axon (Gestor de Paquetes Inmutable): Un sistema diseñado para la seguridad de la cadena de suministro de software. Axon prohíbe la ejecución de scripts arbitrarios en la máquina del desarrollador (preinstall/postinstall). Solo clona código fuente validado criptográficamente mediante firmas Ed25519 y bloqueos deterministas (axon.lock).