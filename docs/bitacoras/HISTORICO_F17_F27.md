# HISTÓRICO FASES 17–27 — Snapshot de MEMORIA_PROYECTO.md (estructura legacy)

> ⚠️ Contenido preservado de la estructura original MONOLÍTICA de MEMORIA_PROYECTO.md.
> Útil para investigación histórica.
> Para estado actual, consulta el índice activo en MEMORIA_PROYECTO.md raíz.

---

## 1. CONTEXTO ACTUAL (estructura legacy - ver dashboard raíz)

- **Fase del roadmap:** FASE 27 — Herramientas de Desarrollo (LSP, VS Code, Debugger). Fase 26 COMPLETADA.
  **ME-F27-1 ✅** stdlib I/O + string utils (commit `075eb2c`).
  **ME-F27-L1 ✅** LSP Synapse puro: header parsing + dispatch JSON-RPC (compila a `lsp_v3.exe`).
  **ME-F27-L2 ✅** Fix atoi_f use-after-free + hover/completion/definition reales (commit `73f13ac`). Tests LSP: 0→4/9.
  **ME-F27-L2.1 ✅** hover funcion + definition tests (commit `b453276`). Tests: 4→7/9.
  **ME-F27-L2.2 ✅** lsp_extract_doc_functions C helper + fix hover test pos (commit `c91ecf6`). Tests: 7→8/9.
  **ME-F27-L3 ✅** lsp_get_enclosing_return_type C helper (commit `49ffe06`). Tests: 7→8/9. Solo falta completion_symbols (FFI crash: Synapse RAII corrupts stack when calling void C functions).
  Commit e314d8b: C helpers lsp_build_completion_items + lsp_send_completion_response listos.
  Commit 703b711: cleanup estable 8/9.
  FFI crash: Synapse RAII frees CadenaSegura.datos via shared pointer en parametros de función C.

  **Hallazgos críticos Synapse RAII descubiertos:** (1) `atoi_f()` libera argumento ANTES de parsear → use-after-free;
  (2) `_json_a_texto()` usa buffer estático `_ser_buf` → cada llamada sobreescribe anterior;
  (3) `desde_texto()` libera body vía RAII → body queda invalid después;
  (4) `obtener_campo()` libera nodo → doble free en llamadas encadenadas;
  (5) `lsp_doc_get()` retornaba puntero a buffer estático → RAII lo liberaba → heap corruption;
  (6) Windows stdout text mode duplica \r en \n → headers LSP corruptos.
  (7) `subcadena()` en bucles while con RAII libera `doc` al salir del scope -> hover variable
      no encuentra funcion contenedora (periodo de vida de `doc` reducido).
  (8) Cadenas concatenadas con `var = var + ...` en Synapse: RAII libera valor antiguo ANTES
      de evaluar la expresion derecha -> use-after-free (patron `items = items + ...`).
  (9) `lsp_extract_doc_functions()` (C puro) funciona en C pero Integracion Synapse-FFI
      genera crash silencioso -> investigar frontera de llamadas FFI Synapse.
  (10) Test `hover_variable` posicion original (line=4, char=15) apuntaba a espacio en blanco;
       corregido a (line=3, char=8) que apunta a 'resultado'.
  (11) CadenaSegura sin campo `es_externo`: C functions retornan malloc'd ptr, Synapse RAII
       libera via pool_free -> crash. Solucion: campo `uint8_t es_externo` en CadenaSegura,
       _syn_texto_liberar lo verifica antes de pool_free. Actualizar synapse_rt_types.h
       Y generator.py para mantener consistencia.
  (12) lsp_build_completion_items() retorna CadenaSegura con es_externo=1; funciona desde
       dispatch Synapse (NO desde handler interno). Patron exitoso: C func retorna items,
       Synapse concat y enviar_respuesta.RAII no libera por es_externo.
      (13) RESUELTO (2026-08-29, Opción A del Arquitecto): el campo `es_externo` en CadenaSegura
       era una DEVIACIÓN de Manual 2 §4.1 (CadenaSegura = 16 bytes). Causaba ABI mismatch
       24B (runtime) vs 16B (test inmutable + generador C nucleo/generator.c) → Prueba 5
       "B verifica A" fallaba por desborde de 8 bytes al devolver CadenaSegura por valor
       (gdb watchpoint confirmó: pb contigua a pa en el frame, offset 16; el write de 24B
       cero pa.longitud dentro de cluster.c:67 → extraer_parte copia 0 bytes → pub_a vacío
       → va=-1). Fix Opción A (Manual 2 §4.1 + §9.1): eliminar es_externo de
       synapse_rt_types.h (16B exactos); _syn_texto_liberar libera SIEMPRE con pool_free;
       convertir TODAS las devoluciones CadenaSegura de string_utils.c de malloc→pool_alloc
       (11 sitios) y free→pool_free, eliminando los 5 `.es_externo=1`. Alineados a 16B:
       nucleo/*.c (6), compilador/generator/generator.py:653, tests/integration/
       test_cluster_handshake.c y 770 tmp*.c de fuzz (bulk). NO se modificó el test inmutable.
       Evidencia: test_cluster_handshake_e2e.py 6/6 ("Pasados: 21 Fallos: 0"); harness LSP
       (build/obj/lsp_harness.c) items.longitud=519 / resp.longitud=584, _syn_texto_liberar
       sin crash, rc=0; nucleo/lsp_v3.exe rebuild contra runtime 16B → ciclo LSP rc=0.
       MTS: docs/plan_ME_traza_P5.md + docs/verificacion_ME_traza_P5.md (CUMPLE);
       auditoria/contrastar.py ✅; verificar_alineacion 0 brechas. Commit e79fdcc.
  (14) HALLAZGO DESCARTADO (2026-08-29, FALSO POSITIVO): se registró que
       `runtime/core/string_utils.c:486` escribía `dup[rpos] = ' '` (espacio), pero la
       verificación con test TDD (luego retirado) y el warning del compilador
       (`null character(s) preserved in literal`) confirmaron que el literal contiene un
       NUL real (`'\x00'`) — el visor de archivos renderizó el NUL como espacio. El
       código YA escribe el terminador nulo correcto; no hay bug que corregir. Lección
       MTS: ante un byte sospechoso, verificar con `repr`/bytes o warning del compilador,
       no fiarse del render. Ver AUDITORIA H29 (cerrado como falso positivo).
  (15) BUG CRÍTICO: pool_alloc slab allocator retornaba la misma dirección para dos
       arrays ParArr/ParJson vivos durante parseo JSON recursivo. Causa: el slab
       de 256 bytes albergaba arrays de 192 bytes (8 ParJson). Cuando el root y un
       objeto anidado ambos crecían su array vía pool_alloc(192), el slab retornaba
       la misma dirección → el root sobreescribía sus claves con las del anidado.
       Fix: cambiar par_arr_append/nodo_arr_append de pool_alloc a malloc (json.c).
       Secundario: static input buffer _p_input_buf, _json_str_copy para strings,
       parse stack global para preservar punteros ParArr, fix cmp_texto/contiene
       use-after-free. Commit b6007dd. Tests: 2/2 completion PASS, 16/16 suite PASS.
   **Correcciones runtime:** `_setmode(stdout, O_BINARY)` en io.c; `lsp_doc_get()` retorna malloc copy en string_utils.c.
   **Bug fix:** `_scope_stack[-1]` sin guard en `emit_declarations.py` (causaba crash con variables de destructor a nivel módulo).
   **Contratos:** 19 funciones LSP con `requiere/garantiza` (Manual 2 §12).
   **ANEXO movido:** `docs/ANEXO_INVENTARIO_ARCHIVOS.md` → `docs/manuales/`. Fase 23 COMPLETADA:

- **GATE DE LECTURA PREVIA (2026-08-23, commit `21ace30`):** la regla 1 ("leer el manual antes de codificar") es ahora mecánica — `auditoria/registrar_lectura.py` + `docs/mapa_manuales.md`: todo agente DEBE ejecutar `--pendientes`, leer las secciones mapeadas para los archivos que tocará y registrar la lectura (--registrar valida contra encabezados reales de M1-9; secciones fabricadas se rechazan). El pre-commit BLOQUEA commits con producción modificada sin lectura registrada del día. Obligación adicional: archivo productivo nuevo sin mapeo también bloquea → añadir su entrada al mapa primero.

- **PROMPT DE INICIO CANÓNICO (2026-08-23, commit `c80808f`):** `AGENTS.md` en la raíz — opencode lo inyecta automáticamente en cada sesión de agente. Contiene la secuencia de arranque obligatoria (memoria → gobernanza → git status multi-agente → gate de lectura), reglas duras (tests inmutables, no inventar, detente-y-pregunta) y ciclo de micro-entregable. El prompt antiguo de "AUDITORÍA Y REFACTORIZACIÓN" queda OBSOLETO: la misión SIEMPRE se deriva de la línea "Fase del roadmap" de esta memoria. No duplicar reglas del AGENTS.md aquí ni viceversa.

- **DECISIÓN D-F22-A (Arquitectura, Fase 22):** los frontends de Syquex se implementan en SYNAPSE (`syquex/lexer.syn`, `parser.syn`, `traductor.syn` junto a `nucleo/ast_abi.syn`) porque (i) Manual 1 §4 define `syquex.syn` como "Compilador de Syquex escrito en Synapse"; (ii) paradoja de bootstrap: no existe compilador Syquex que compile lexer.syq hasta completar la fase; (iii) todo el toolchain es Synapse auto-alojado. La migración a .syq auto-alojado es hito posterior DENTRO de F22. Los .syq son los PROGRAMAS de usuario Syquex.

- **Próximos MEs de Fase 22:** R86 ✅ → R87 ✅ → R88 ✅ → R89 ✅ → R90 ✅ → R91 ✅ → R94 ✅ → R95 ✅ → ME-AUDITOR-1 ✅ → ME-AUDITOR-2 ✅ → ME-AUDITOR-3 ✅ → ME-AUDITOR-4 ✅. Auditoría externa Fase 22 vs manuales: **Finding 1 ✅** (SemNodo ABI D-F22-SEM + es_mutable bit0 + verifier NODO_PARRAFO/NODO_VACIO + parser &mut fix; commits `df4d6ca`+`1f6e6f8`, 32/32 tests). **Finding 2 ✅** (NOMBRE_NODO 58/58 completado + 5 categorías + test_categorization_completa_de_nodos; commit `ff0b6bd`, 28/28 tests). **Finding 3 ✅** (D-F22-A: &mut como extensión controlada para FFI; parser ya corregido en ME-AUDITOR-1; commit `c2a0608`). **Finding 4 ✅** (BUG CRÍTICO: self-by-value → self-by-pointer en métodos; context.py _metodos_self + generator.py + emit_declarations.py + emit_expressions.py + fixture multi-campo; commit `865b0b8`, 35/35 tests). **Finding 5 ✅** (AUDITORIA_FASE22.md: CRIT-1 lexer `..` lookahead, CRIT-2 sq_para init+bloque, ALTO-1/2 sq_tipo &mut/tipos función, MED-1..4, OP-1..4; commit `500db49`, 43/43 tests, 0 brechas). **Luego:** fase 22 CERRADA — transición Fase 23.

- **Objetivo actual (histórico F17):** PGO/LTO pipeline completo. Conexión `generator_pgo.syn` → `generator.syn` (visitadores `nodos_flujo.syn`, `orquestador.syn`, `recorrido.syn`). Flags `--release`/`--debug`/`--profile` unificados entre `principal.syn` y `pipeline.py`. Fix bug `_pa.longitud > 9` → `>= 9` (`--profile` no activaba). Bootstrap S1==S3 BYTE-IDENTICAL (sha256 `cca44227…`). Pipeline PGO: Step 1 `-fprofile-generate` → 23 `.gcda` (Step 2) → Step 3 `-fprofile-use -flto` → 38% reducción tamaño (1.7MB→1.1MB). Binario PGO-optimizado compila y ejecuta correctamente. Verifier 0 brechas. Reporte: docs/reportes/FASE_17.md.

- **Fase 11 (Liberación/Distribución):** COMPLETADA (2026-08-20). Artefactos v8.1.0-industrial: synapse.spdx.json (2025 packages, 2024 files, SPDX 2.3), .sha256 + .sig (Ed25519), CHANGELOG_v8.1.0.md, release_keys/. Reporte: docs/reportes/FASE_11.md. Hashes: fb5b75c, 9f69f39, 67ef40c, eda73c8, 302b742.

- **Fase 12 (IA Nativa):** ✅ CERRADA (R79+R80, 2026-08-21) — matriz final: modelo_local 68/68, quantization 142/142 (fix fp16-cero/subnormal IEEE), synapse_rag 81/81, rag_pipeline.py 5/5, ai_orchestrator 27/27, **distillation 101/101** (antes SEGV). **F12-2 resuelta vía opción b del Arquitecto (R80):** API nueva `kd_agregar_par_n(..., n, ...)` con longitud explícita + `KDLogitPair.num_logits` + persistencia v2 (`KD_VERSION 2`, num_logits por par); `kd_agregar_par` queda como wrapper legacy; `kd_paso_destilacion` honra longitud por-par. Modificación del probe APROBADA (regla 5): secciones 4/5/7 → `_n`, sección 10 cfg vocab=10. Commits `ce1f846`+`2be52ef`; reportes R79/R80. **Lección:** el hook pre-commit limpia los `.o` de raíz en cada commit — reconstruirlos vía fixture de sesión conftest o compilación directa antes de linkear probes manualmente.
- **Fase 13 (Federated):** ✅ CERRADA (R79, 2026-08-21) — validate_federated **114/114**, validate_dist_orchestrator **119/119** (fix semántica REDISTRIBUTE: marca+éxito, redistribución explícita del caller). Resoluciones F13-1..4 se mantienen. Commit `ce1f846`; reporte docs/reportes/R79.md.
- **Fase 14 (Proof Bridge):** PARCIAL — `nucleo/proof_bridge.c` (654 L) + `nucleo/proof_bridge.h` (188 L) + `std/proof_bridge.syn` (107 L). **Hallazgo F14-1 resuelto:** `pb_traducir_a_lean` ahora traduce `>=` a `≥` y `<=` a `≤`. **Hallazgo F14-2 resuelto (2026-08-21):** `validate_formal_proof.exe` presentaba stack overflow (exit code 0xC00000FD) por stack default de Windows (1MB). Fix: link con `-Wl,--stack,8388608` (8MB). `tests/conftest.py` actualizado: `proof_bridge.o` en `_RT_OBJ_DEFS` + `validate_formal_proof` en `_RT_BINARIOS_EXTRA` con flag de stack + soporte de `extra_flags` en el loop de compilación. Validación: build automático rc=0, ejecución 95/95 PASS.
- **Fase 15 (Quantum):** ✅ CERRADA COMPLETA (R74+R82, 2026-08-21) — validate_quantum_runtime **96/96** (frontera del test actualizada a QC_MAX_QUBITS=9 con aprobación del Arquitecto; corregía el registro incompleto de R74), err_corr **30/30**, memory **38/38**. Commits `8193892`, `633ed03`; reporte R82.md.
- **Fase 16 (Modularización synapse_rt.c):** VERIFICADA — D-9(d) CERRADA (R42): `synapse_rt.c` 7.882 → 1.769 L; `runtime/core/` tiene 20+ módulos.
- **Fase 17 (PGO/LTO):** COMPLETADA (2026-08-20) — commit `4e0ab7f`.
- **Fase 18 (Caché incremental):** COMPLETADA (2026-08-21) — commit `1f278d8`.
- **Fase 19 (CanalRemoto v2):** ✅ CERRADA COMPLETA (R78+R83+R84, 2026-08-21) — handshake Ed25519 + crypto_kx (R78) + **AEAD crypto_secretbox** en transporte ([nonce24][MAC16][ct], nonce por mensaje; parseo determinista del framing DATA; XOR eliminado regla 12) (R83) + **serialización §6.3 completa** vía `_syn_axon_serializar_valor`/`deserializar_valor` en axon_rt.c: nulo/bool/enteros 8-64 adaptativos/decimal/texto/tensor/lista/mapa etiquetados; ESTRUCTURA 0x08 rechazada sin esquema; ejemplo normativo 42=[0x02]+4B byte-exacto (R84). Tests: handshake 4/4, cluster_remote 3/3, serialization 2/2, probe serialización 15/15. Commits `a7ec2af`,`9f626a9`,`c2043e8`; reportes R78/R83/R84. (H27 concat→runtime: ver bitácora.)
- **Fase 15 (Quantum):** CERRADA COMPLETA (R74+R82) — validate_quantum_runtime **96/96** (frontera del test actualizada a QC_MAX_QUBITS=9 con aprobación del Arquitecto; corregía el registro incompleto de R74), err_corr 30/30, memory 38/38. Commit `633ed03`; reporte R82.md. **H27 resuelta (2026-08-21):** `concat` movido al runtime (`runtime/core/sistema.c`); codegen S1 y nativo ya no emiten la definición de `concat` en el código generado, solo el `extern`. Link modular verificado (`tests/bootstrap_test.syn` compila y ejecuta correctamente).
- **Fase 20 (Lifetimes avanzados):** VERIFICADA — `nucleo/lifetimes.syn` + `tests/integration/test_lifetimes.py` 7/7 PASS.
- **Fase 21 (RAII/scopes):** PARCIAL — RAII runtime completada (F3-2); destructor maps = Fase 23 (Syquex).
- **FASE 5 (Contratos y Bootstrap):** ✅ **TESTS REPARADOS (R98, commit d47d400).** Las 8 fallas preexistentes en tests de contratos `requiere`/`garantiza` corregidas: (A) type check de expresiones booleanas en todos los modos (antes solo `--safe`); (B) eliminada evaluación estática que bloqueaba compilación — contratos son runtime-only via `assert()` (Manual 2 §5.1/§5.3); (C) `main()` retorna `0` en éxito. **62/62 PASS** (contratos+bootstrap+verificación); FASE 4 regresión 28/28 PASS; E2E 73/73 PASS; alignment 0 brechas. **Deuda preexistente registrada (no causada por R98):** 7 fallas en `test_ownership_10.py` (`ERR_MEM_USE_AFTER_MOVE`) — verificadas como preexistentes via stash (fallan en HEAD sin cambios). Causa raíz pendiente de investigación. Código muerto eliminado: `ERR_SEM_CONTRATO_REQUIERE` (diagnostics.py).
- **Fases 22-30 (Syquex/Ecosistema):** NO ADELANTAR (regla 7).

[... resto de secciones 2, 3, 4, 5 ...continúan en este archivo]
