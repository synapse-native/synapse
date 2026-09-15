# Expediente de alineación f31_deficiencias

base: HEAD
cambio_hash: 4436a54bab2dcd1e

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## axon/axon_rt.c
- manual: 8
  seccion: 4.3
  cita: "El comando `synapse init` crea la siguiente estructura:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: axon/axon_rt.c:17
  oraculo: tests/axon/test_workspace.py

- manual: 6
  seccion: 5
  cita: "El handshake entre nodos se realiza mediante Ed25519 (TweetNaCl) y es zero-trust: 1. El cliente envía un mensaje `HELLO` con su clave pública y una firma de un nonce aleatorio de 32 bytes. 2. El servidor verifica la firma usando la clave pública proporcionada. 3. Si es válida, el servidor responde con su propio `HELLO` firmado. 4. Se deriva una clave de sesión (usando `crypto_kx` de libsodium o similar) para cifrar el tráfico."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: axon/axon_rt.c:18
  oraculo: tests/axon/test_workspace.py

## axon/axon_rt.h
- manual: 6
  seccion: 5
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. El handshake entre nodos se realiza mediante Ed25519 (TweetNaCl) y es zero-trust."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: axon/axon_rt.h:1
  oraculo: tests/axon/test_workspace.py

## compilador/generator/emit_declarations.py
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios: Comentarios de línea: comienzan con `//` y se extienden hasta el final de la línea. Comentarios de bloque: comienzan con `/*` y terminan con `*/`, pueden abarcar múltiples líneas y anidarse."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:1
  oraculo: tests/nucleo/test_lint.py

- manual: 1
  seccion: 1
  cita: "Synapse es el lenguaje de programación nativo, compilado y de grado de sistemas que sirve como cimiento para sistemas operativos, motores de bases de datos, infraestructura de red y aplicaciones Edge AI."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:1
  oraculo: tests/nucleo/test_lint.py

## compilador/generator/emit_expressions.py
- manual: 2
  seccion: 12
  cita: "Lexer multi‑idioma: 100% pass, >95% cobertura. Parser EBNF: 100% pass, >95% cobertura. Contratos requiere/garantiza: 100% pass. Tipos algebraicos (match exhaustivo): Detección de ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:537
  oraculo: tests/nucleo/test_lint.py

- manual: 1
  seccion: 1
  cita: "Synapse es el lenguaje de programación nativo, compilado y de grado de sistemas que sirve como cimiento para sistemas operativos, motores de bases de datos, infraestructura de red y aplicaciones Edge AI."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:1
  oraculo: tests/nucleo/test_lint.py

## compilador/generator/generator.py
- manual: 2
  seccion: 5.1
  cita: "`requiere`: Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas. `garantiza`: Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:595
  oraculo: tests/nucleo/test_lint.py

- manual: 1
  seccion: 1
  cita: "Synapse es el lenguaje de programación nativo, compilado y de grado de sistemas que sirve como cimiento para sistemas operativos, motores de bases de datos, infraestructura de red y aplicaciones Edge AI."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:1
  oraculo: tests/nucleo/test_lint.py

## compilador/parser_control.py
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios: Comentarios de línea: comienzan con `//` y se extienden hasta el final de la línea. Comentarios de bloque: comienzan con `/*` y terminan con `*/`, pueden abarcar múltiples líneas y anidarse."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_control.py:1
  oraculo: tests/nucleo/test_lint.py

- manual: 1
  seccion: 1
  cita: "Synapse es el lenguaje de programación nativo, compilado y de grado de sistemas que sirve como cimiento para sistemas operativos, motores de bases de datos, infraestructura de red y aplicaciones Edge AI."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_control.py:1
  oraculo: tests/nucleo/test_lint.py

## compilador/puente_canonico.py
- manual: 3
  seccion: 11.1
  cita: "Syquex no tiene su propio backend. Cada nodo del AST de Syquex se traduce al `SemNodo[]` canónico de Synapse."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:69
  oraculo: tests/nucleo/test_lint.py

- manual: 6
  seccion: 5
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. El handshake entre nodos se realiza mediante Ed25519 (TweetNaCl) y es zero-trust."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:70
  oraculo: tests/nucleo/test_lint.py

- manual: 2
  seccion: 12
  cita: "Lexer multi‑idioma: 100% pass, >95% cobertura. Parser EBNF: 100% pass, >95% cobertura. Contratos requiere/garantiza: 100% pass. Tipos algebraicos (match exhaustivo): Detección de ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:71
  oraculo: tests/nucleo/test_lint.py

- manual: 1
  seccion: 1
  cita: "Synapse es el lenguaje de programación nativo, compilado y de grado de sistemas que sirve como cimiento para sistemas operativos, motores de bases de datos, infraestructura de red y aplicaciones Edge AI."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/puente_canonico.py:1
  oraculo: tests/nucleo/test_lint.py

## nucleo/parser_sentencias.syn
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios: Comentarios de línea: comienzan con `//` y se extienden hasta el final de la línea. Comentarios de bloque: comienzan con `/*` y terminan con `*/`, pueden abarcar múltiples líneas y anidarse."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/parser_sentencias.syn:2
  oraculo: tests/nucleo/test_fmt.py

## nucleo/principal.syn
- manual: 3
  seccion: 12.1
  cita: "Syquex incluye una biblioteca estándar modular ubicada en `lib/`, con archivos `.syq` que proporcionan funcionalidad de alto nivel. Módulo IO: `lib/io.syq` — Entrada/salida (consola, archivos). Módulo Web: `lib/web.syq` — Servidor HTTP basado en fibras (no bloqueante)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:695
  oraculo: tests/nucleo/test_fmt.py

- manual: 5
  seccion: 6.2
  cita: "Un canal remoto se comporta como un canal local, pero los mensajes se transmiten a través de TCP/IP con un handshake Ed25519 y cifrado de sesión. Handshake (zero-trust): 1. El cliente envía un mensaje `HELLO` con su clave pública y una firma de un nonce. 2. El servidor verifica la firma y responde con su propio `HELLO`. 3. Se deriva una clave de sesión (usando `crypto_kx` de libsodium o similar) para cifrar el tráfico."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:698
  oraculo: tests/nucleo/test_fmt.py

- manual: 9
  seccion: 6.2
  cita: "El pipeline de CI/CD ejecuta automáticamente: La suite de tests completa en cada target. La verificación del bootstrap (diff 0 bytes). El fuzzing destructivo (500+ iteraciones). Los sanitizadores (ASan, UBSan, TSan). `synapse lint --check` sobre el código fuente del compilador."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:723
  oraculo: tests/nucleo/test_fmt.py

## runtime/core/axon.c
- manual: 8
  seccion: 4.3
  cita: "El comando `synapse init` crea la siguiente estructura:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/axon.c:6
  oraculo: tests/test_auditoria_alineacion.py

- manual: 6
  seccion: 5
  cita: "El handshake entre nodos se realiza mediante Ed25519 (TweetNaCl) y es zero-trust: 1. El cliente envía un mensaje `HELLO` con su clave pública y una firma de un nonce aleatorio de 32 bytes. 2. El servidor verifica la firma usando la clave pública proporcionada. 3. Si es válida, el servidor responde con su propio `HELLO` firmado. 4. Se deriva una clave de sesión (usando `crypto_kx` de libsodium o similar) para cifrar el tráfico."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/axon.c:9
  oraculo: tests/test_auditoria_alineacion.py

## runtime/core/concurrency.c
- manual: 5
  seccion: 2
  cita: "Una fibra es un hilo de usuario ultraligero que se ejecuta sobre un pool de hilos del sistema operativo (M:N scheduling). Cada fibra tiene: Pila propia (tamaño configurable, por defecto 64 KB). Contexto de ejecución (registros, program counter). Identificador único."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/concurrency.c:1
  oraculo: tests/test_auditoria_alineacion.py

## runtime/core/sistema.c
- manual: 2
  seccion: 9.1
  cita: "Semántica de Movimiento (Move Semantics): Al asignar una variable propietaria a otra o pasarla como argumento de función por valor, la posesión se transfiere (move). La variable original queda invalidada en el ámbito origen."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:31
  oraculo: tests/test_auditoria_alineacion.py

- manual: 5
  seccion: 1
  cita: "El ecosistema Synapse/Syquex adopta la filosofía de compartir memoria mediante comunicación. El estado mutable compartido entre hilos está prohibido a nivel de compilación. La comunicación entre fibras se realiza exclusivamente a través de canales tipados (`Canal<T>`), que transfieren la propiedad de los datos."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:108
  oraculo: tests/test_auditoria_alineacion.py

## synapse_rt_types.h
- manual: 2
  seccion: 4.1
  cita: "Tipo Sintáctico `texto` / `cadena` / `string`: Cadena UTF-8 segura (longitud + buffer). Tamaño (ABI): 16 bytes. No termina en `\0` internamente, se convierte para FFI. Tipo `entero` / `int`: Entero con signo de 64 bits, tamaño 8 bytes, alias de `int64_t`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_rt_types.h:14
  oraculo: tests/test_auditoria_alineacion.py

- manual: 2
  seccion: 12
  cita: "Lexer multi‑idioma: 100% pass, >95% cobertura. Parser EBNF: 100% pass, >95% cobertura. Contratos requiere/garantiza: 100% pass. Ownership (move): Detección de ERR_MEM_USE_AFTER_MOVE. Borrowing checker: 100% pass."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_rt_types.h:42
  oraculo: tests/test_auditoria_alineacion.py

- manual: 1
  seccion: 1
  cita: "Synapse es el lenguaje de programación nativo, compilado y de grado de sistemas que sirve como cimiento para sistemas operativos, motores de bases de datos, infraestructura de red y aplicaciones Edge AI."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: synapse_rt_types.h:1
  oraculo: tests/test_auditoria_alineacion.py

## syquex/expr.syn
- manual: 2
  seccion: 1.3
  cita: "Synapse soporta dos estilos de comentarios: Comentarios de línea: comienzan con `//` y se extienden hasta el final de la línea. Comentarios de bloque: comienzan con `/*` y terminan con `*/`, pueden abarcar múltiples líneas y anidarse."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/expr.syn:2
  oraculo: tests/auditoria/test_gate_mts_oraculos.py

- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/expr.syn:1
  oraculo: tests/auditoria/test_gate_mts_oraculos.py

## syquex/parser.syn
- manual: 1
  seccion: 1
  cita: "El ecosistema Synapse es una plataforma de desarrollo de software completa y unificada que abarca desde el metal desnudo hasta la capa de aplicación, integrando tres componentes fundamentales que funcionan en perfecta armonía."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/parser.syn:2
  oraculo: tests/auditoria/test_gate_mts_oraculos.py

- manual: 2
  seccion: 12
  cita: "Lexer multi‑idioma: 100% pass, >95% cobertura. Parser EBNF: 100% pass, >95% cobertura. Contratos requiere/garantiza: 100% pass. Tipos algebraicos (match exhaustivo): Detección de ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/parser.syn:98
  oraculo: tests/auditoria/test_gate_mts_oraculos.py

- manual: 3
  seccion: 3
  cita: "La gramática de Syquex es más expresiva que la de Synapse, incorporando elementos de programación orientada a objetos (estructuras con métodos y constructores) y manejo de errores algebraico integrado."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: syquex/parser.syn:1031
  oraculo: tests/auditoria/test_gate_mts_oraculos.py
