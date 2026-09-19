# Plan ME r150_funcional — Cierre de hallazgos funcionales R149 (M1/M3/M4/M6/M7/M13/M14/M15 + M2)

Origen: docs/reportes/R149.md §3 (hallazgos mayores y menores) y §4 (causa raíz).
Los bloqueantes R1-R10 ya están reparados (commit d040500, reporte R150.md).
Este ME cierra la frontera entre componentes que ningún gate miraba.

## M1 — synapse_llvm.c/synapse_wasm.c nunca se enlazan (cable suelto)
requisito: Manual 1 §3
texto: "**Enlace:** Runtime modular (memory, concurrency, io, net, quantum, ml, federated)."
implementacion: añadir synapse_llvm.c/synapse_wasm.c (emisores de texto LLVM IR/WAT sin dependencias externas, raíz del repo) a _RT_FUENTES de pipeline.py con // cumple Manual 1 §3. std/llvm.syn y std/wasm.syn pasan de "compilan pero no enlazan" a enlazables. Decisión D-R150-1 (bitácora): backend C canónico; el generador Python (llvm_ir_generator.py/wat_generator.py) queda deprecado para --target llvm/wasm (paso siguiente, no este ME).
oraculo: tests/auditoria/test_oraculos_r150.py (OBL-R150-M1: probe E2E importar std.llvm + llamada LLVMVersion() -> enlaza y ejecuta; ídem std.wasm)

## M2 — std/cluster.syn declara 3 externos sin implementación (worker_ejecutar/robar/cola_vacia)
requisito: Manual 5 §8.1
texto: "El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo."
implementacion: implementar en runtime/core/cluster.c los 3 wrappers sobre la cola work-stealing existente (ws_*): worker_ejecutar(id) procesa la cola global (roba=desencola y desencola hasta vacía, 0 exito/-1 vacía al inicio), worker_robar(id) desencola un elemento (retorna id de tarea o -1), worker_cola_vacia(id) retorna ws_profundidad()==0. Paridad con la estructura Worker del manual (cola única real del scheduler actual; la migración a colas por hilo es deuda del scheduler F4.1, no de este wrapper). Comentario // cumple Manual 5 §8.1 + declaraciones en runtime/core/cluster.h.
oraculo: tests/auditoria/test_oraculos_r150.py (OBL-R150-M2: probe C directo ws_inicializar+worker_* con aserciones)

## M3a — synapse opensyn bindings es un stub que miente
requisito: Manual 7 §1
texto: "generación automática de bindings a librerías C. Todo ello ejecutándose completamente local, sin telemetría y con total soberanía del usuario."
implementacion: cli.py subcomando bindings ejecuta opensyn/generate_runtime_bindings.py como subproceso (regenera lib/runtime_bindings.syq real, 93 funciones) y reporta su salida; rc!=0 se propaga. Comentario # cumple Manual 7 §1.
oraculo: tests/auditoria/test_oraculos_r150.py (OBL-R150-M3a: subprocess synapse opensyn bindings --check → rc=0 y archivo regenerado con marcador)

## M3b — synapse opensyn status es un stub que miente
requisito: Manual 7 §3
texto: "Los modelos se almacenan localmente y el servidor de inferencia se ejecuta en el equipo del usuario."
implementacion: status real: lee config_ollama.txt (ruta real: $HOME/.opensyn o install), consulta http://127.0.0.1:8088/v1/models con urllib timeout 2s, lista modelos locales de ~/.ollama/models/manifests + ~/.synapse/models/, imprime estado. Sin telemetría, 100% local. # cumple Manual 7 §3.
oraculo: tests/auditoria/test_oraculos_r150.py (OBL-R150-M3b: status ejecuta rc=0 y NO imprime "no disponible (offline)" fijo)

## M3c — download/finetune anunciados sin handler (caen a "Subcomando desconocido")
requisito: Manual 8 §4.1
texto: "`synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario."
implementacion: handlers honestos: download/finetune requieren llama-server/Ollama activo y lo verifican con la misma sonda HTTP local; sin servicio activo → mensaje claro y rc=1 (honesto: NO imprimen [OK] sin hacer nada). Se elimina la promesa de ayuda que no se puede cumplir o se redirige al flujo instalador (H-R144-2/H-R144-5 documentan que la provisión de modelos vive en el instalador/OpenSyn TUI). # cumple Manual 8 §4.1.
oraculo: tests/auditoria/test_oraculos_r150.py (OBL-R150-M3c: download/finetune sin servicio → rc=1 con mensaje, jamás [OK])

## M3d/M4 — debugger time-travel del CLI imprime éxito fijo; construir requiere axon_build.exe inexistente
requisito: Manual 8 §3.4
texto: "El CLI unificado (`synapse`) incluye comandos para depuración:"
implementacion: debug --load parsea el formato TRACE v1 REAL que escribe _syn_debug_finalizar_sesion (runtime/core/debug.c:335: header id=/programa=/eventos=/capacidad=, eventos "tag|timestamp|funcion|archivo|linea|valor_entero|valor_decimal|valor_texto|variable") en Python; --step/--reverse/--snapshots navegan esa traza cargada (estado en memoria del proceso CLI: índice de evento, filtro por tag según EVENT_* de debug.h, resumen de snapshots = eventos con variable no vacía). Sin --load: --step/--reverse/--snapshots fallan con rc=1 y mensaje honesto (hoy imprimen éxito vacío). construir: removido del CLI (código muerto, regla 12: axon_build.exe no existe ni tiene receta; el build real es main.py/synapse build) — acción D-R150-2 ratificada en bitácora.
oraculo: tests/auditoria/test_oraculos_r150.py (OBL-R150-M3d: traza sintética TRACE v1 → --load/--step/--reverse/--snapshots operan eventos reales; sin traza → rc=1)

## M6 — Versión inconsistente (VERSION=8.1.0, ROADMAP=8.3.0, banner v5.0)
requisito: Manual 8 §4.1
texto: "El CLI unificado es el punto de entrada único para todas las operaciones del ecosistema."
implementacion: banner del cli.py lee VERSION (única fuente de verdad) en vez de hardcodear "v5.0 - Poligolota"; ROADMAP.md cabecera corregida a 8.1.0-industrial (la rama es release/v8.1.0-industrial; 8.3.0 solo existirá al abrir la rama de la Fase 33+). # cumple Manual 8 §4.1.
oraculo: tests/auditoria/test_oraculos_r150.py (OBL-R150-M6: banner == contenido de VERSION)

## M7 — SyntaxWarning invalid escape en scripts/verificar_e2e.py
requisito: Manual 1 §3
texto: "Valida que el instalador silencioso descargó y ubicó correctamente"
implementacion: la ruta literal C:\Synapse\... del docstring/strings pasa a raw string. # cumple Manual 1 §3.
oraculo: tests/auditoria/test_oraculos_r150.py (OBL-R150-M7: import sin SyntaxWarning)

## M13 — Ruido de working tree: .venv-1/, keep/, htmlcov/, _test_*_temp/
requisito: Manual 9 §9
texto: "Los directorios de build del repositorio (`build/`, artefactos `*.o` en la raíz) son **efímeros** y se limpian en cada commit (hook \"Limpiando artefactos de build\")"
implementacion: agregar .venv-1/ y keep/ a .gitignore (htmlcov/ y _test_*/ ya ignorados) y borrar los directorios no rastreados del working tree (son 20M+302K+probes: ruido que envenena listados). Los *.o sueltos de raíz los limpia el hook en el commit (se verifica).
oraculo: tests/auditoria/test_oraculos_r150.py (OBL-R150-M13: tras limpieza, ls raíz no contiene keep/ ni .venv-1/)

## M14 — pytest.ini timeout sin plugin (warning en cada corrida)
requisito: Manual 2 §12
texto: "| Lexer multi‑idioma | `pytest tests/unit/test_lexer.py -v` | 100% pass, >95% cobertura |"
implementacion: instalar pytest-timeout en el venv y añadirlo a requirements.txt (dev). Sin cambios en pytest.ini (timeout=300 queda operativo).
oraculo: tests/auditoria/test_oraculos_r150.py (M14: la suite corre sin "Unknown config option: timeout" desde pytest-timeout en requirements.txt)

## M15 — SKILL_TDD_PROMPT promete verificar() que std/testing.syn no expone
requisito: Manual 7 §2.3
texto: "Las reglas de Synapse/Syquex se inyectan en el System Prompt"
implementacion: añadir wrapper verificar(condicion, nombre) a std/testing.syn (delega en assert_verdadero; el prompt TDD genera código que compila). # cumple Manual 7 §2.3.
oraculo: tests/auditoria/test_oraculos_r150.py (OBL-R150-M15: probe importa std.testing y llama verificar(1==1,"x") → compila+enlaza+PASS)

## Oráculo matriz de compilación (causa raíz R149 §4)
requisito: Manual 1 §3
texto: "[ Backend GCC/Clang/LLVM/emcc ] ──(Linker, -lpthread, -lws2_32)─────────────────────► [ Binario Nativo (.exe / ELF) / WASM ]"
implementacion: tests/auditoria/test_matriz_compilacion.py: genera en TEMP un programa mínimo por CADA std/*.syn (importar + llamada inocua + escribir_linea), lo compila ENLACE COMPLETO via pipeline (no check_only) y ejecuta (rc=0). Cubre la frontera std↔runtime que ningún gate miraba. Marcado slow (timeout 600 por módulo). El CI (ci-tests.yml) lo invoca como job aparte: `matriz-compilacion` (ubuntu-latest, D-R150-7); los jobs `test`/`bootstrap` lo excluyen con --ignore para no duplicar 35 enlaces completos en la matriz 3×3.
oraculo: tests/auditoria/test_matriz_compilacion.py

## M16 — Paridad de tipos compilador↔std y gramática de retorno opcional (rondas 3-4, D-R150-8/9/10)
requisito: Manual 2 §2
texto: "La gramática de Synapse se define mediante una notación EBNF extendida."
implementacion: cerrar los hallazgos de la matriz de compilación (rondas 3-4): (a) parseo de `declaracion_funcion` con retorno ausente — Manual 2 §2 L56 hace `[ "->" tipo ]` OPCIONAL — normaliza a 'nulo' en _parsear_def_funcion y _parsear_externo_funcion (+ UnboundLocalError de tok_retorno en DeclaracionExterna); (b) casts `(Decimal)x` eliminados de std/symbolic_exec (no existen en la gramática; la coerción entero→decimal en FFI es implícita, verificada por bisección). Archivos: compilador/parser_declarations.py (# cumple Manual 2 §2), std/symbolic_exec.syn (# cumple Manual 2 §4.1). D-R150-10: std/agent_skills deja de definir `principal` (el patrón `principal() -> nulo` es solo de programa, M2 §13) → demostrar_agent_skills() con contrato requiere (M2 §12).
oraculo: tests/auditoria/test_matriz_compilacion.py tests/auditoria/test_oraculos_r150.py

## M17 — Prototipos builtin y tipos canónicos (entero=int64_t, Manual 2 §4.1)
requisito: Manual 2 §4.1
texto: "| `entero` / `int` | Entero con signo de 64 bits | 8 bytes | Alias de `int64_t` |"
implementacion: D-R150-8: los prototipos hardcodeados `Tensor crear_tensor(int,int)`/`Tensor reserva(int)` en compilador/generator.py:893 y emisores de compilador/generator/emit_tensors.py contradecían las definiciones int64_t emitidas desde std.math/std.mem (entero→int64_t desde 86e89db) → "conflicting types" en _synapse_shared.h. Fix: int64_t en prototipos y emisores — el compilador y sus protos son UNA sola frontera de tipos (D-R150-8). D-R150-9: tipos capitalizados (Entero/Decimal/Puntero/Cadena/Booleano) NO son aliases de §4.1 → std/atp_engine.syn y std/quantum_err_corr.syn normalizados a los canónicos en minúsculas (el checker unifica TVar frescos por ocurrencia y producía TVar ambiguos). Archivos: generator.py + emit_tensors.py (# cumple Manual 2 §4.1), std/atp_engine.syn, std/quantum_err_corr.syn (# cumple Manual 2 §4.1).
oraculo: tests/auditoria/test_matriz_compilacion.py tests/auditoria/test_oraculos_r150.py
