# Roadmap de Madurez Industrial: Synapse
Este archivo es la Fuente Única de Verdad para el desarrollo del lenguaje. 
Cualquier cambio de estado debe ser registrado aquí por el agente de IA (OpenCode).

## Estatus General
| Fase | Pilar | Prioridad | Estado | Responsable |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Self-Hosting (Core) | Crítica | En Proceso | OpenCode |
| 2 | Memory Safety | Alta | Pendiente | OpenCode |
| 3 | Error Handling (ADTs) | Alta | Pendiente | OpenCode |
| 4 | Developer Experience (LSP) | Media | Sin Iniciar | OpenCode |

---

## Fase 1: Self-Hosting (El rito de iniciación)
*Objetivo: Reescribir el Front-end (Lexer/Parser) en Synapse para eliminar Python.*
- [x] Auditoría de tokens actuales en `lexer.py`.
- [x] Definición de gramática en `lexer.syn` (migración del stub).
- [ ] Implementación de parser recursivo descendente en `parser.syn`.
- [ ] Validación: Compilación del parser utilizando el binario actual.

## Fase 2: Memory Safety (Ownership & Borrowing)
*Objetivo: Eliminar fugas y eliminar dependencia de `malloc`/`free` manual.*
- [ ] Diseño del sistema de tipos de posesión (Ownership).
- [ ] Implementación del "Borrow Checker" en el analizador semántico.
- [ ] Migración de `synapse_rt.c` a un modelo de memoria administrado por el compilador.

## Fase 3: Error Handling (Tipado Algebraico)
*Objetivo: Eliminar códigos de retorno enteros (`-1`, `0`).*
- [ ] Definición de `Result<T, E>` y `Option<T>` nativos.
- [ ] Implementación de `unwrap` y `match` en el generador de código.
- [ ] Refactorización de la librería estándar (`std.io`) para usar `Result`.

## Fase 4: Developer Experience (LSP)
*Objetivo: Integración profunda en editores.*
- [ ] Creación del servidor `synapse-lsp` en Synapse.
- [ ] Implementación de autocompletado y diagnósticos en tiempo real.
- [ ] Publicación de extensión oficial en VS Code Marketplace.