# MANUAL DE TESTS OBLIGATORIOS (MTO) — v1

**Fuente de verdad:** Manuales M1–M9 del ecosistema Synapse/Syquex/OpenSyn.
**Propósito:** enumerar, por capítulo funcional, los oráculos mínimos obligatorios que toda fase
debe dejar en verde. Toda prueba (`test_*.py`) debe mapear a una entrada `OBL-*` y citar el
`Manual §` correspondiente (gobernanza regla 5, hoy operativa mediante este manual).

**Formato de entrada:**
`OBL-Mx-NN | Manual §Y | comportamiento esperado | tipo (unit/integración/TDD) | estado (RED/GREEN/TDD)`

- `GREEN` = oráculo existe y pasa.
- `RED` = oráculo existe y falla (pendiente implementación de código).
- `TDD` = oráculo a crear como test TDD real (fallará hasta la implementación).

---

## M1 — Fundamentos del lenguaje
- OBL-M1-01 | Manual 1 §2 | Estructura de directorios de tests conforme a M1 §2 | integración | GREEN
- OBL-M1-02 | Manual 1 §4 | Sintaxis core (tipos, funciones) parsea y compila | unit | GREEN

## M2 — Tipos, contratos e inferencia HM
- OBL-M2-01 | Manual 2 §4.2 | Inferencia HM identidad `identidad(x: T) -> T` | unit | GREEN
- OBL-M2-02 | Manual 2 §12 | Contratos `requiere`/`garantiza` observables en runtime | unit | GREEN
- OBL-M2-03 | Manual 2 §8.2 | Tipos ADT anidados en firmas | unit | GREEN

## M3 — Syquex (frontend / F28 certificación)
- OBL-M3-01 | Manual 3 §3 | Frontend Syquex parsea y traduce conforme al manual | unit | GREEN
- OBL-M3-02 | Manual 3 §5 | Analizador de alcance (arena/rc/arc/débil) | unit | GREEN
- OBL-M3-03 | Manual 3 §6 | Métodos con self por puntero (no by-value) | unit | GREEN
- OBL-M3-04 | Manual 3 §3 (certificación) | **Certificación Syquex v1.0 (Hito 7)** | TDD | RED ← ME_28_T1..T3

## M4 — Gestión de memoria (RAII / alcance)
- OBL-M4-01 | Manual 4 §2 | Arena allocator (bump O(1), cascada) | unit | GREEN
- OBL-M4-02 | Manual 4 §3.2/§3.3 | rc<T> / arc<T> reference counting | unit | GREEN
- OBL-M4-03 | Manual 4 §4.2 | débil<T> WeakRef + upgrade | unit | GREEN
- OBL-M4-04 | Manual 4 §5 | Cleanup blocks / CFG / rc_flag | unit | GREEN

## M5 — Concurrencia y canales
- OBL-M5-01 | Manual 5 §3.4 | Canales: `canal(...)`, `ch <-`, `ch ->` en runtime | unit | GREEN
- OBL-M5-02 | Manual 5 §6.2/§6.4/§6.5 | Cluster: conectar/enviar/recibir, raft, multicast | integración | GREEN
- OBL-M5-03 | Manual 5 §9 | Cluster remoto (handshake Ed25519 + crypto_kx) | integración | GREEN

## M6 — ABI / puente AST
- OBL-M6-01 | Manual 6 §1.2 | SemNodo ABI plano de 10 campos | unit | GREEN
- OBL-M6-02 | Manual 6 §1.3 | NOMBRE_NODO cubre los 58 nodos | unit | GREEN
- OBL-M6-03 | Manual 6 §5.1/§5.3 | Axon: serialización/deserialización etiquetada | integración | GREEN

## M7 — OpenSyn (IA / RAG / validación)
- OBL-M7-01 | Manual 7 §2.3 | Inyección de contexto estático (reglas Syquex) en prompt | integración | GREEN
- OBL-M7-02 | Manual 7 §6.3 | Bucle de validación 3 intentos | integración | GREEN
- OBL-M7-03 | Manual 7 §7 | Transpilación Python→Syquex: el .syq generado COMPILA | integración | GREEN

## M8 — HERRAMIENTAS DE DESARROLLO (F27, ACTIVO)
- OBL-M8-01 | Manual 8 §1.2 | LSP initialize/initialized/shutdown | integración | GREEN
- OBL-M8-02 | Manual 8 §1.4 | hover / completion / definition reales | integración | GREEN (8/9)
- OBL-M8-03 | Manual 8 §1.4 | codeAction + formatting + signatureHelp | TDD | RED ← ME_27_T1
- OBL-M8-04 | Manual 8 §1.4 | workspace/didChangeConfiguration | TDD | RED ← ME_27_T2
- OBL-M8-05 | Manual 8 §2.3 | VS Code aiStatus / aiTranspile / aiBindings | TDD | RED ← ME_27_T3
- OBL-M8-06 | Manual 8 §5.2/§5.3/§5.4 | Debugger time-travel + breakpoints reversibles | TDD | RED ← ME_27_T4
- OBL-M8-07 | Manual 8 §4.2/§5/§7 | CLI run / debug / opensyn | TDD | RED ← ME_27_T5
- OBL-M8-08 | Manual 8 §1.4 | completion_symbols real (gap FFI RAII) | TDD | RED ← ME_27_T6
- OBL-M8-09 | Manual 8 §6.3 / Manual 7 §6.3 | Bucle de validación integrado en LSP | integración | GREEN

## M9 — Distribución / F29 / F30
- OBL-M9-01 | Manual 9 §5.7 / F29 | Detección de hardware `std/os.syn` | TDD | RED ← ME_29_T1
- OBL-M9-02 | Manual 9 §9 / F29 | Installer OpenSyn (`opensyn/installer.syn`) | TDD | RED ← ME_29_T2
- OBL-M9-03 | Manual 9 §9 / F29 | Gestión de modelos OpenSyn | TDD | RED ← ME_29_T3
- OBL-M9-04 | Manual 9 §9 / F30 | Instaladores .iss/.sh/.dmg unificados | TDD | RED ← ME_30_T1
- OBL-M9-05 | Manual 9 §9 / F30 | Makefile / build.py reproducible | TDD | RED ← ME_30_T2
- OBL-M9-06 | Manual 9 §9 / F30 | Distribución final empaquetada y firmada | TDD | RED ← ME_30_T3
- OBL-M9-07 | Manual 9 §9 / F30 / Hito 8 | Release unificado (lanzamiento público) | TDD | RED ← ME_30_T4

---

## Notas de mantenimiento
- Toda entrada nueva de test debe añadir su `OBL-*` aquí y citar el `Manual §` en el archivo.
- `auditoria/auditar_calidad_tests.py --mto` verifica que cada `OBL-*` tenga test y cita.
- Las entradas `RED`/`TDD` se cierran cuando su ME de implementación correspondiente las vuelve `GREEN`.
