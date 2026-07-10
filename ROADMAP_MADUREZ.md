# Roadmap de Madurez Industrial: Synapse
Este archivo es la Fuente Única de Verdad para el desarrollo del lenguaje. 
Cualquier cambio de estado debe ser registrado aquí por el agente de IA (OpenCode).

## Estatus General
| Fase | Pilar | Prioridad | Estado | Responsable |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Self-Hosting (Core) | Crítica | En Proceso | OpenCode |
| 2 | Memory Safety | Alta | Terminada | OpenCode |
| 3 | Error Handling (ADTs) | Alta | Terminada | OpenCode |
| 4 | Developer Experience (LSP) | Media | Terminada | OpenCode |
| TQC | Sanitización y Fuzzing | Alta | Pendiente | OpenCode |
| Pacto | El Pacto y Concurrencia | Alta | Pendiente | OpenCode |
| DX | DX y Telemetría | Media | Pendiente | OpenCode |
| Axon | Axon (Ecosistema) | Media | Pendiente de Inicio | OpenCode |

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
- [x] Diseño del sistema de tipos de posesión (Ownership).
- [x] Implementación del "Borrow Checker" en el analizador semántico.
- [x] Migración de `synapse_rt.c` a un modelo de memoria administrado por el compilador.

**Fase 2 completada:** [x]

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
- [x] Diagnósticos en tiempo real en el daemon.
- [x] Inyección del flag `--lsp` en `main.py`.
- [x] Cliente LSP oficial para VS Code (`editor/vscode/`).
- [ ] Publicación de extensión oficial en VS Code Marketplace.

**Fase 4 completada:** [x]

## Fase Nueva (TQC - Sanitización y Fuzzing)
*Objetivo: Integrar ASan/TSan en el generador C y crear banco de regresión.*
- [ ] Integrar ASan/TSan en el generador C.
- [ ] Crear banco de regresión.

## Fase Nueva (El Pacto y Concurrencia)
*Objetivo: Implementar Contratos Lógicos (requiere/garantiza), prohibir estado mutable en lanzar e implementar Canales.*
- [ ] Implementar Contratos Lógicos (requiere/garantiza).
- [ ] Prohibir estado mutable en lanzar.
- [ ] Implementar Canales.

## Fase Nueva (DX y Telemetría)
*Objetivo: Diagnósticos enriquecidos (LSP avanzado).*
- [ ] Diagnósticos enriquecidos (LSP avanzado).

## Fase Axon (Ecosistema)
*Objetivo: Integración con el sistema de módulos Axon y publicación del ecosistema. Queda desplazada hasta que las fases anteriores estén en verde.*
- [ ] Definición del formato de paquete Axon (`.axon`).
- [ ] Implementación del gestor de paquetes (`axon install`, `axon publish`).
- [ ] Repositorio público de paquetes (registro central).
- [ ] Documentación oficial y tutoriales.

**Fase Axon completada:** [ ]