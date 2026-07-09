# Roadmap de Madurez Industrial: Synapse
Este archivo es la Fuente Única de Verdad para el desarrollo del lenguaje. 
Cualquier cambio de estado debe ser registrado aquí por el agente de IA (OpenCode).

## Estatus General
| Fase | Pilar | Prioridad | Estado | Responsable |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Self-Hosting (Core) | Crítica | En Proceso | OpenCode |
| 2 | Memory Safety | Alta | Terminada | OpenCode |
| 3 | Error Handling (ADTs) | Alta | Terminada | OpenCode |
| 4 | Developer Experience (LSP) | Media | En Proceso | OpenCode |

---

## Fase 1: Self-Hosting (El rito de iniciación)
*Objetivo: Reescribir el Front-end (Lexer/Parser) en Synapse para eliminar Python.*
- [x] Auditoría de tokens actuales en `lexer.py`.
- [x] Definición de gramática en `lexer.syn` (migración del stub).
- [x] Implementación de parser recursivo descendente en `parser.syn`.
- [x] Validación: Compilación del parser utilizando el binario actual.

**Fase 1 completada:** [x]

## Fase 2: Memory Safety (Ownership & Borrowing)
*Objetivo: Eliminar fugas y eliminar dependencia de `malloc`/`free` manual.*
- [ ] Diseño del sistema de tipos de posesión (Ownership).
- [ ] Implementación del "Borrow Checker" en el analizador semántico. [En Proceso]
- [ ] Migración de `synapse_rt.c` a un modelo de memoria administrado por el compilador.

## Fase 3: Error Handling (Tipado Algebraico)
*Objetivo: Eliminar códigos de retorno enteros (`-1`, `0`).*
- [x] Definición de `Result<T, E>` y `Option<T>` nativos.
- [x] Implementación de `unwrap` y `match` en el generador de código.
- [x] Refactorización de la librería estándar (`std.io`) para usar `Result`.

**Fase 3 completada:** [x]

## Fase 4: Developer Experience (LSP)
*Objetivo: Integración profunda en editores.*
- [x] Diseño del contrato LSP (mapeo de errores, conversión línea/columna).
- [x] Construcción del daemon: bucle JSON-RPC, lectura raw de Content-Length.
- [ ] Implementación de autocompletado y diagnósticos en tiempo real.
- [x] Inyección del flag `--lsp` en `main.py`.
- [ ] Publicación de extensión oficial en VS Code Marketplace.