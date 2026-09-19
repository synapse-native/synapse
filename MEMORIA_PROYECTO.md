# 🧠 MEMORIA DEL PROYECTO SYNAPSE

> **Formato optimizado para agentes.**
> - 🚦 **Sección 1 — Dashboard actual** (léase primero, < 30 segundos).
> - 💡 **Sección 2 — Errores recurrentes** (patrones a evitar siempre).
> - 📚 **Sección 3 — Lecciones clave** (reglas de arquitectura/tacticas).
> - 📜 **Sección 4 — Historico detallado (F1–F27)** — conserva el conocimiento profundo del proyecto.
> - 📋 **Sección 5 — Checklist de verificación** (validar antes de commitear).
>
Última actualización: **2026-09-18** (ME r150_funcional en curso — oráculos y gates evaluados)

---

## 🚦 1. DASHBOARD ACTUAL```yaml
Fase roadmap:      ME r150_funcional EN CURSO (WIP sin commit) — cierre de hallazgos funcionales R149 (frontera std↔runtime)
                   FASE 32 COMPLETA — Agente de Codificación Avanzado + Memoria Persistente (5/5 ME)
                   FASE 31 COMPLETADA — Herramientas Nativas (ME-1..ME-5)
                   FASE 30-c ME_opensyn_best — ME-1..ME-6 TODOS COMPLETADOS
                   FASE 30-b HARDENING — OpenSyn TUI + IA local (R141/R142/R143) COMPLETADA
                   FASE 30 COMPLETADA — Instalación Unificada y Distribución Final
Estado:            Plan MTS 12 bloques (docs/plan_ME_r150_funcional.md). Oráculo del ME
                   tests/auditoria/test_oraculos_r150.py 14/14 GREEN (M2/M3d/M4 reparados).
                   Matriz separada en test_matriz_compilacion.py: 29/35, 6 hallazgos
                   std↔runtime activos. verificar_alineacion SIN BRECHAS. Expediente
                   r150_funcional creado y VERIFICADO (evidencia f82eddaa76c1b58f.json).
Commit fase:       8247564 (docs post-commit R150) sobre d040500 (fix r149)
Próximo ME:        Cerrar los 4 hallazgos restantes de la matriz std↔runtime (31/35)
Próximo paso:      Corregir parseo de `externo funcion` sin retorno + casts (Decimal)x
                   (symbolic_exec/atp_engine/agent_skills) e inferencia TVar ambigua
                   (quantum_err_corr); integrar la matriz en .github/workflows/ci-tests.yml
Últimos commits:    8247564 (docs: post-commit R150 — reporte, bitácora y memoria)
                    d040500 (fix(r149): reparar hallazgos R149 — std/, runtime tiempo, fuga RAII, OpenSyn compilable, --check)
                    f3dab3f (feat(opensyn): Fase 32.4 — pipeline multiagente optimizado)
                    e0493bf (feat(opensyn): Fase 32.3 — memoria persistente cifrada)
                    de7107c (feat(opensyn): Fase 32.2 — explorer_det + architect_det deterministas)
                    fa34825 (feat(nucleo): Fase 32.1 — grafo de conocimiento)
```

### Cambios recientes esta sesión
| Commit | Descripción | Impacto |
|--------|-------------|---------|
| `d9c498a` | F30-b: chat OpenSyn real (Ollama) + consola UTF-8 + LSP multi-mensaje + instalador 8.1.0 revisado | opensyn/principal.syn chat interactivo; runtime/core/ollama.c nuevo; io.c/string_utils.c UTF-8 y stdin pipes; lsp_v3.syn dispatch tolerante a espacios; synapse.iss sin [Run] roto, model=qwen-coder, PATH sin duplicados, Excludes; vsix repack. LSP 36/36, instalador 11/11, 0 brechas |
| `de901bb` | ME_30_T8: Docs/Packaging | README.md con instrucciones completas, 5 tests GREEN |
| `f3e5ad3` | ME_30_T7: Auto-actualización | auto_actualizar.py con verificar_version, 5 tests GREEN |
| `5c22529` | ME_30_T6: Tests de smoke | test_smoke.py con verificación de sintaxis, 5 tests GREEN |
| `b1390ba` | ME_30_T5: Verificación Ed25519 | verificar_firma.py con Ed25519, 5 tests GREEN |
| `72f60bd` | ME_30_T4: Instalador macOS | create_dmg.sh con opciones de componentes, 6 tests GREEN |
| `e5e9b58` | ME_30_T3: Instalador Linux | install.sh con detección de distribución, 6 tests GREEN |
| `5775c5a` | ME_30_T2: Instalador Windows | synapse.iss con componentes, 6 tests GREEN |
| `b9aa55f` | ME_30_T1: Estructura instaladores | Directorios instaladores/{windows,linux,macos,common}, 5 tests GREEN |
| `d64a07e` | fix(ci): normalizar line-endings + limpiar artefactos | CRLF→LF en 87 archivos, `// cumple Manual`→`# cumple Manual`, 2 stray files borrados, release_matrix.yml Create Release step |
| `fa3c548` | feat(installer): generar instalador Windows Manual 9 §2.5 | synapse.iss → instaladores/windows/, install.ps1, 3 CI workflows + 3 tests actualizados, valid_installer.py + AUDIT_EXITOSA, 48 tests pass |
| `609e9a4` | fix: modular S1 build + CI fix + register std lectures | Replaced broken GCC step with `python main.py --output` modular build; registered readings for std/concurrencia (Manual 5 §3.4), std/sync (Manual 5 §5.1), std/wasm (Manual 1 §5.3); cleaned merge conflict markers from lecturas.jsonl; dist/bin/synapse.exe generated (timestamp 2/9/2026 18:59:44) |
| `6dd0139` | docs(release): actualizar memoria y auditoría post-cleanup | Documentación post-commit cleanup |
| `d001d74` | fix(auditoria): reparar gate de citas `cumple Manual` (§ opcional) + tests MTS | ME-Q1: CUMPLE_RE acepta § opcional → citas_archivo valida 552/588 citas (antes 34/588); test_citas_archivo VERDE. ME-Q2: tests/test_citas_formato.py. ME-Q3: MTO OBL-M2-02 §12→§5 (Manual 2 §5=contratos). Plan MTS docs/plan_ME_reparacion_control_calidad.md (contrastar --plan OK, 0 brechas). |
| `ce0e291` | R113: chat OpenSyn estilo OpenCode/Freebuff sin corrupción de cadenas + UTF-8 consola + instalador 8.1.0 | HALLAZGO R113: el generador S1 libera parámetros texto al retornar desde bloques anidados (verificado en C generado) → helpers con alias destruían la lista de modelos del chat (use-after-free). Fix: fix_borrowing en pipeline.py aplicado a módulos C de dir_base (no solo nucleo/); helpers single-pass + copias strcpy_f; chat /modelos /model< n> /model<nombre> /ayuda /skills /tdd /revisar /plan con auto-detección y persistencia del modelo real (qwen-coder→qwen-coder:latest); io.c escribir_linea CP65001 (mojibake consola real); ollama.c _syn_ollama_modelos; synapse.iss wizard pregunta PRIMERO conectar a Ollama existente (Sí omite descargas). Verificado E2E contra Ollama real + pipes. Reporte R139. 0 brechas. |
| `e4d09c0` | R140/ME_agente_opensyn: OpenSyn AGENTE (herramientas TOOL + contexto repo real) + UI estilo OpenCode/Freebuff + cliente Ollama robusto | HALLAZGO R140: `_ollama_leer_respuesta` leía con recv bloqueante SIN timeout → Ollama colgado congelaba el chat en "Tu>" en silencio (150 s+ sin salida). Fix ollama.c: SO_RCVTIMEO 2 s + plazo absoluto 300 s + corte temprano por Content-Length + errores distinguidos (red/plazo/corte). Además: System Prompt con contexto estático (reglas Synapse .syn + Syquex .syq/@export + AGENTS.md + carpetas raíz + git); bucle agente [TOOL] listar/leer/git (sistema.c _syn_listar_directorio/_syn_capturar_comando, solo lectura); banner ASCII retro + prompt ❯ ANSI solo consola real (io.c _syn_es_consola/_syn_ansi); estado "[*] Consultando a <modelo>…" antes de cada llamada. E2E Ollama REAL: responde con la primera línea real de AGENTS.md, stderr 0 bytes, banner 1 sola vez. MTS completo (plan R1 §1.1/R2 §2.3/R3 §8, 2 oráculos E2E, verificacion_ME). Reporte R140. 0 brechas. |
| `a13332b` | R141/R142: OpenSyn TUI pantalla completa (banner de PÍXELES "OpenSyn", panel+caja de entrada con ❯, streaming NDJSON _syn_ollama_stream_*, menús modales / y /model con flechas, fallback pipe OPENSN_TUI_TEST=1) + historial persistente ~/.opensyn/history.jsonl (FIFO 1000, ↑↓) + autocompletado Tab (comandos / y rutas, doble Tab = menú). Vendor deps/agent-skills v0.6.8 MIT (pin d2c37ef, base de std/agent_skills.syn para /tdd /revisar /plan /skills). Instalador: SHA256 de llama-server/modelos (update_hashes.ps1 sin duplicaciones). Oráculos historial/autocomplete GREEN, E2E pipes limpia (rc=0, stderr 0), pytest 38 passed. Reportes R141/R142. |
| `db4ccf9` | R144/R144b: test instalador como usuario real — 3 bloqueantes corregidos en synapse.iss/update_hashes.ps1: (1) faltaban fuentes/headers de enlace en bin\ → compilador instalado no compilaba; (2) hash de modelos placeholder + hash ZIP-vs-exe de llama-server + URL 1B 401 + curl sin --fail → descarga IA imposible; (3) extracción copiaba solo el launcher sin sus 50 DLLs → motor IA no arrancaba. E2E v6b: compilación OK, IA local sirviendo completions, oráculos instalados en verde, PATH sin duplicados. Reporte R144. |
| `bdb615c` | R145: terminar WIP cliente OpenAI-compatible + banner figlet | ollama.c: streaming /v1/chat/completions con system/user ([USUARIO]), errores HTTP ≥400 propagados, cortes [DONE]/finish_reason, prefijo SSE data:, bloque DEBUG con ruta local hardcodeada eliminado, fix OOB 1 byte en escape, truncado system a últimos 3500 bytes (lección R144c) en ambas rutas; principal.syn: banner figlet (decisión Arquitecto; oráculo banner RED → H-R145-1); .syn.json regenerado (R35). Oráculos historial/autocomplete/GGUF GREEN, alineación 0 brechas. |
| `df8ff5f` | R146: prueba interactiva VS Code + instalación completa — principal.syn: filtrar_listado() excluye artefactos de build (prefijo _, .c.o/.o/.syn.json/.exe) del listado inyectado al modelo; TOOL listar y contexto estático devuelven UNA línea compacta acotada a 2400 chars (H-R146-1: el modelo 1.3B repetía el listado en bucle y el contexto cambiaba en cada build). lsp_v3.syn: synapse/aiExplain implementado (Manual 8 §2.3; antes -32601 y el comando de VS Code quedaba colgado), registrado en MODULOS_D9.md (1256 L, regla 13). Oracle banner: prompt natural ("nombra 3" confundía al modelo, determinista con temp 0). Instalador 8.1.0 reinstalado TYPE=full con binarios byte-idénticos (sha256). Oráculos banner GREEN x2 (~90 s)/autocomplete/GGUF GREEN, LSP 33 passed, alineación 0 brechas. |
| `7d2edbc` | R143/ME_opensyn_ia_gguf: motor GGUF local endurecido — vocab desde el array real tokenizer.ggml.tokens (antes solo escalar → 0 con GGUFs reales → rechazo), cache de posición O(n) para arrays, límites contra tamano_mmap, cache perezoso F32 (F16/Q4_0/Q4_1/Q5_0/Q5_1/Q8_0 exactos), dims GGUF ne[0]=contigua (w_k OOB corregido), top_p qsort O(vs log vs). Oráculo E2E determinista NUEVO GREEN: GGUF sintético (vocab 11, merges, token_embd Q8_0) → driver .syn compilado con S1 → carga+ingesta 5 tokens+generación "abababababababab" (temp=0)+cierre limpio. H-GGUF-2 INVARIANTE: output.weight debe tener n_vocab filas (LM head itera vocab del tokenizer). Reporte R143. |

### Deudas / Hallazgos críticos activos

- **H-CONTROL-1 (RESUELTO en working tree, ME-control_solido):** el job CI `auditoria` usaba `steps.base.outputs.ref` SIN definir el paso `id: base` → base vacía → `git diff "" HEAD` → 0 brechas FALSAS: el gate de bitácora más fuerte del servidor estaba muerto (fallo abierto). Fix: paso `id: base` propio + fallo por exit code (pipefail). Además `nonnull_base` degrada base vacía a HEAD~1 en verificar_alineacion/contrastar.
- **H-CONTROL-2 (RESUELTO en working tree):** NINGUNA capa ejecutaba los oráculos MTS: CI pasaba `--sin-oraculos` a alineacion.py y el hook solo los corría con ALINEACION_ORACULOS=1 (jamás establecida). Fix: CI sin `--sin-oraculos`; hook los corre por defecto (opt-out=0); contrastar.py EJECUTA cada oráculo del plan (pytest release: SKIP/vacío/fallo = FAIL; scripts: exigen marca OK/PASS/SIN BRECHAS). Oráculo nuevo: tests/auditoria/test_gate_mts_oraculos.py (15 GREEN, OBL-MCTRL-01..04).
- **H-CONTROL-3 (RESUELTO en working tree):** el MTO validaba solo formato. Fix: `auditar_calidad_tests.py --solo-mto` (pre-commit + CI) valida OBL con Manual § real; SIN_OBL fatal en modo incremental; detección SNIFF ampliada (SNIFF_AMP, fatal con --estricto-sniff). DEUDA VISIBLE: MTO cita 10 secciones renumeradas inexistentes (Manual 7 §6.3/§7, Manual 8 §6.3, Manual 9 §9) y 30 GREEN sin test citador — requieren ratificación del Arquitecto (regla 5).
- **H-CONTROL-4 (RESUELTO en working tree):** vínculo plan↔código laxo, sello no bloqueante, evidencia desanclada, .syq fuera del alcance, D-9 sin C/opensyn, hook borraba archivos rastreados por patrón, base CI vacía, parser de bitácora hardcodeaba 2026. Fix: vínculo ESTRICTO multi-plan (--plan repetible; hook/CI contrastan TODOS los planes juntos); cambio_hash mismatch BLOQUEA; sello con frescura + --exigir-sello; evidencia CI comiteada exigida (evidencia_ci_ok); .syq en PROD_EXTS/CI; D-9 escanea opensyn/syquex/runtime-core y MODULOS_D9 acepta .c (11 módulos registrados); limpieza del hook SOLO no-rastreados; bitácora con fecha AAAA-MM-DD. Detalle: docs/plan_ME_control_solido.md + docs/verificacion_ME_control_solido.md + docs/GOBERNANZA_BRANCH_PROTECTION.md.
- **H-TEST-FIX-1 (RESUELTO, fix_test_seccion):** tests/test_auditoria_alineacion.py::test_seccion_es_de_manual fallaba porque la cadena de prueba no contenía el carácter §. Fix: agregar § faltante a "cumple Manual 2 §3 en el codigo". Plan MTS docs/plan_ME_test_seccion_fix.md.
- **D-ALINEACION-F31 (RATIFICADO, 469780a):** secciones Manual 6 §5, Manual 5 §2, Manual 1 §1, Manual 1 §5 no tienen oraciones indexadas en .indice.json (el índice solo indexa subsecciones 5.1/5.3, 2.1, 1.1). El código CUMPLE las secciones del manual pero el gate de alineación no puede verificar citas literales sin oraciones en el índice. Decisión: marcar como DESVIACION en expediente f31_deficiencias.md con nota justificativa. Resolución: re-indexar manuales para incluir secciones padre o aceptar deuda.
- **H-F29-T5b (RESUELTO):** bug RAII preexistente en `runtime/core/sistema.c:24 concat()` con CadenaSegura retornada por FFI — usaba `malloc()` pero liberada con `pool_free()`. Fix commit `478f047`: cambiado a `pool_alloc()`. Mismo bug corregido en `_syn_sha256()`/`_syn_sha256_archivo()` (axon.c:37,63) y `_syn_home()` (modelo.c:781 — usaba `strdup()` que internamente llama `malloc`).
- **test_binding_typescript:** GREEN (ME_29_T2 completado) — bindings TypeScript implementados en opensyn/bindings_generator.py.
- **test_gestion_modelos:** GREEN (ME_29_T3_mod completado) — test modificado para verificar funcionalidad implementada en installer.syn.
  - **test_latencia_meta:** RED esperado — requiere llama-server activo en :8088 (benchmark real).
- **H-CS1 (REGISTRADO):** Config `core.autocrlf=true` (global) conflictuaba con `.gitattributes` (`* text=auto eol=lf`), causando CRLF en working tree en Windows. Fix: `git config --local core.autocrlf false` (commit `d64a07e`). Los archivos `.syn` en working tree quedan con LF.
- **H-CS2 (REGISTRADO):** 2 artefactos accidentales de release v8.1.0-industrial: (1) filename `"e create v8.1.0-industrial --draftgh release create..."` = output de `less` paginador capturado; (2) `tests/unit/tokens.syn` = formato YAML no-Synapse no referenciado. Borrados en commit `d64a07e`.
- **H-F30b-1 (RESUELTO, d9c498a):** el `[Run]` del instalador ejecutaba `synapse.exe {app}\opensyn\installer.syn`, que SOLO COMPILA (nunca ejecuta) y fallaba en silencio (~240 ms, sin GCC). Eliminado: la configuración de OpenSyn la hace el wizard [Code] `DownloadAIComponents` (Manual 9 §5.2-5.3) y `opensyn.exe` lee la config instalada. Desviación documentada.
- **H-F30b-2 (RESUELTO, d9c498a):** el wizard escribía `model=<nombre GGUF>` (ej. deepseek-coder-1.3b-Q4_K_M.gguf) en `config_ollama.txt` al conectar con Ollama existente — nombre inválido como tag de Ollama. Ahora escribe `model=qwen-coder` (el modelo que anuncia el diálogo).
- **H-F30b-3 (RESUELTO, d9c498a):** reinstalaciones repetidas anexaban `{app}\bin` al PATH una y otra vez (se observaron 9-10 entradas duplicadas apuntando a carpetas inexistentes en esta máquina). Fix: Checks `NotSynapseInUserPath`/`NotSynapseInMachinePath` en [Registry]; en esta máquina se limpiaron manualmente las entradas fantasma (User+Machine).
- **H-F30b-4 (RESUELTO, d9c498a):** la consola Windows mostraba mojibake (┬┐/├®) porque el runtime no alineaba la consola a UTF-8. Fix: `SetConsoleOutputCP(65001)`/`SetConsoleCP(65001)` SOLO cuando stdout/stdin es consola real (GetConsoleMode OK); los pipes del LSP quedan intactos (Manual 8 §1.2).
- **H-LSP-1 (RESUELTO, d9c498a):** el dispatch del LSP (WIP) extraía `method` asumiendo JSON compacto (`"method":"x"`, como VS Code); `json.dumps` de Python emite `"method": "x"` con espacios → `method_name` vacío → ningún request respondía (test_lsp_multimsg/workspace RED). Fix: extracción tolerante a espacios. Los tests pasaban antes solo porque apuntaban al binario viejo `nucleo/lsp_test.exe`.
- **H-R113 (REGISTRADO, ce0e291 — deuda de compilador):** el generador S1 del pipeline modular libera los parámetros `CadenaSegura` de una función cuando un `retornar` ocurre dentro de un bloque anidado (si/mientras, depth≥1) — `_syn_texto_liberar(param)` antes del return — y también en varios retornos de nivel raíz. Consecuencia: una función .syn que recibe `texto` NO es de solo lectura por defecto; CONSUME la cadena del llamador (use-after-free silencioso sobre el pool). Manual 2 §11 prescribe borrowing; hoy se resuelve con el post-proceso `fix_borrowing` (whitelist read-only) + regla empírica para helpers .syn: single-pass, retornos solo en depth 0, y el llamador pasa copias `strcpy_f` de cadenas vivas. No se corrige el generador (fuera de alcance); registrar como deuda para el compilador S1.
- **H-R140 (REGISTRADO, e4d09c0 — cliente HTTP sin plazo):** `_ollama_leer_respuesta` (runtime/core/ollama.c) usaba `recv()` bloqueante sin timeout ni plazo absoluto: si Ollama aceptaba la conexión y se colgaba (llama-server caído a mitad de generación, doble instancia, carga lenta del modelo), opensyn quedaba congelado en "Tu>" en silencio indefinido. Fix: `SO_RCVTIMEO` 2 s + plazo absoluto de 300 s por request (carga en frío + generación) + corte temprano cuando `Content-Length` queda satisfecho; código de resultado que distingue error de red (-1), plazo agotado (-2) y corte a mitad de cuerpo (-3), traducido por `_syn_ollama_consultar` a un mensaje claro. Lección: todo cliente de red del runtime debe tener plazo absoluto + timeout de grano fino; el chat imprime "[*] Consultando a <modelo>…" antes de cada llamada bloqueante para que la carga del modelo sea visible.
- **ME-agente-herramientas (CALIDAD, pendiente opcional):** con qwen-coder el modelo a veces responde directamente (con el contexto ya inyectado) en lugar de pedir [TOOL] — aceptable porque la inyección estática cubre la mayoría de preguntas del repo; refuerzo con few-shot de [TOOL] en el System Prompt queda como mejora opcional de prompts.
- **H-R144-2 (REGISTRADO, db4ccf9):** VRAM/RAM/CPU detectan -1 en contexto elevado del instalador → modo silencioso elige siempre el 1B (conservador); ME futuro: logging de detección + fallback.
- **H-R144-3 (REGISTRADO, db4ccf9):** `opensyn/modelos.toml` distribuido contiene URLs/hashes placeholder (`abc123...`) — catálogo runtime con datos falsos; regenerar con datos reales (ME futuro; no afecta al instalador).
- **H-R144-5 (REGISTRADO, db4ccf9):** upgrade silencioso con GGUF existente salta la provisión de llama-server (bloque `if not UseExisting`); caso borde tras crash sin modelo ni server (ME futuro).
- **H-R144-4 (DOCUMENTADO):** MSYS Git Bash manglea `/FLAG` de instaladores silenciosos (usar .cmd literal o MSYS2_ARG_CONV_EXCL); el diálogo de idioma aparece en VERYSILENT sin /LANG (Inno, 2 [Languages]).
- **H-R144-6 (RESUELTO, sesión 2026-09-08):** prompt enviado al modelo LLM contiene bytes basura (16 bytes de prefijo no ASCII) que corrompen el system prompt, causando que el modelo no responda correctamente. Causa raíz: `visitar_asignacion` en `compilador/generator/emit_declarations.py` generaba `_syn_texto_liberar(var)` ANTES de evaluar la expresión RHS — use-after-free para `sys = concat(sys, ctx)` que liberaba `sys` antes de que `concat` leyera su valor. Fix: evaluar en variable temporal única (`_syn_tmp_{var}_{counter}`) ANTES de liberar. Elimina trabajo previo de skip de 16 bytes en `ollama.c` (ya no necesario). Lección: RAII con reasignación requiere evaluar RHS primero; el compilador debe generar código defensivo incluso cuando el usuario viola semántica de borrowing.
- **Lección R144:** la validación del instalador debe incluir instalación+compilación+ejecución E2E (los tests de estructura del .iss no ven bloqueantes de runtime); los defines de hash con placeholder "TODO_..." no fallan el build — fallan el usuario final; el hash debe calcularse sobre el MISMO objeto que se verifica (exe extraído, no zip).
- **Lección R144c:** optimizar system prompt para modelos pequeños (1.3B) es crítico — el contexto completo de OpenSyn (~8KB) excede la ventana de 2048 tokens de deepseek-1.3b; truncar a últimos 3500 bytes preserva el mensaje del usuario al final del prompt.
- **H-GGUF-2 (INVARIANTE REGISTRADO, 7d2edbc):** `_syn_modelo_evaluar_token` dimensiona logits con `mc->vocab_size` (tokens del tokenizer) pero el LM head itera `output.weight` con stride n_embd — si output.weight tiene menos filas que el vocab del tokenizer la lectura sale del mmap (logits corruptos → generación vacía). Con GGUFs reales tokenizer==output por diseño, así que no se manifiesta en producción; INVARIANTE: output.weight debe tener n_vocab filas. Detectado por el oráculo sintético (vocab 11 vs output 8).
- **H-GGUF-1 / H-HIST-1 / H-HIST-2 (RESUELTOS, a13332b y 7d2edbc):** merges BPE exigen la pieza resultado en el vocab (resolución por texto exacto); " salir" con espacios se recorta antes de filtrar; Tab/flechas en modo pipe Windows con semántica idéntica a POSIX. Detalle en verificacion_ME_opensyn_ia_gguf.md y verificacion_ME_opensyn_historial_autocomplete.md.
- **Entorno de esta máquina (nota operativa):** Ollama NO instalado — los oráculos de contenido (banner chequeo 2, agente) requieren Ollama vivo con modelo descargado; en esta máquina pasan los chequeos que no dependen de él (banner ASCII, historial, autocomplete, GGUF sintético, pytest 38). Los print con ↑↓/❯ requieren PYTHONIOENCODING=utf-8 en consola cp1252 (patrón conocido).

- **H-R145-1 (CERRADO, 4a7e77d):** el Arquitecto autorizó modificar el oráculo banner en sesión 2026-09-10: chequeo 1 actualizado al banner figlet y marcas del chequeo 2 ampliadas a entradas reales de la raíz (el modelo responde con porciones variables del listado real vía TOOL listar). GREEN verificado con llama-server real (deepseek-coder-1.3b en :11434).
- **H-R145-2 (CERRADO, 4a7e77d):** obsoleto — llama-server SÍ está disponible en esta máquina (:11434, GGUF deepseek-coder-1.3b); el chequeo 2 del oráculo banner pasa con backend real.
- **H-R145-3 (RESUELTO, 4a7e77d):** el parser SSE de ollama.c tratab "finish_reason":null — presente en TODOS los chunks de streaming OpenAI — como fin de stream → el chat se quedaba en "Consultando…" sin respuesta. Fix `_oll_linea_json`: extraer content PRIMERO (el chunk final de llama.cpp trae content + finish_reason:"stop" en la misma línea) y marcar done solo si finish_reason tiene valor entre comillas; "done":true (Ollama) y data: [DONE] intactos.
- **H-R145-4 (RESUELTO, 4a7e77d):** GGUF sin chat template (deepseek-coder-1.3b vía llama-server) genera el template ChatML como TEXTO (<|im_end|>, <|im_start|>system...) en bucle hasta agotar max_tokens (~87 s por consulta). Fix: stop sequences ["<|im_end|>","<|im_start|>","<|EOT|>"] en el body de ambas rutas (stream y no-stream). Consulta real: 87 s → ~5 s.
- **H-R145-5 (REGISTRADO, 4a7e77d — resolución asignada):** el oráculo historial tiene timeout fijo de 60 s por ejecución de subprocess; con backend real cada prompt enviado ES una llamada al modelo (su test 3 envía 3 prompts = 105 s). Funcionalidad validada manualmente con timeout largo (3 entradas exactas en history.jsonl + navegación ↑↑ = "dos", rc=0). ME futuro: subir timeout del oráculo o acortar sus prompts (requiere aprobación del Arquitecto).
- **Lección R145:** (1) el cache `~/.synapse/cache/runtime_obj/*.o` puede enmascarar ediciones de runtime/core/*.c — invalidar el .o y recompilar tras editar (patrón "exe stale"); (2) los WIP heredados pueden contener decisiones NO ratificadas (banner) que revierten planes completados — contrastar contra el plan/la bitácora antes de continuar; (3) el smoke de opensyn reescribe config_ollama.txt (auto-persistencia R139) — restaurarlo antes de commitear.

- **Lección R145b (E2E contra servidor real):** (1) en streaming OpenAI, "finish_reason":null aparece en TODOS los chunks — jamás usarlo como terminador sin verificar el valor; (2) los GGUF sin chat template reproducen el template como texto (ChatML <|im_end|>) → enviar stop sequences siempre (patrón cliente robusto); (3) los oráculos E2E de chat con timeout fijo (60 s) quedan obsoletos cuando el chat FUNCIONA: cada prompt es una llamada real al modelo — diseñar oráculos con prompts que no disparen consultas o con timeout proporcional.
- **H-R146-1 (RESUELTO, df8ff5f):** el contexto inyectado al modelo no era determinista — el listado de la raíz incluía artefactos de build que cambian en cada compilación (_*.c/_*.o/synapse_bootstrap.exe generados por S1 en la raíz) y el modelo 1.3B repetía el listado multilinea en bucle agotando max_tokens (las respuestas variaban según la basura del momento). Fix: filtrar_listado() en principal.syn excluye artefactos por convención del repo (prefijo _, .c.o/.o/.syn.json/.exe) y comprime a UNA línea acotada a 2400 chars, aplicado a TOOL listar y al contexto estático. Respuestas deterministas y con contenido real verificado x2.
- **Lección R146 (producto instalado = producto validado):** (1) al corregir binarios, reconstruir el instalador y reinstalar de inmediato — y verificar sha256 de lo instalado contra lo validado — para que la prueba interactiva del usuario ejerza el mismo binario que pasaron los oráculos; (2) los prompts de los oráculos no deben contener números literales ("nombra 3"): un modelo pequeño los copy-pastea como respuesta literal (determinista con temperature:0); (3) los artefactos que el propio build genera en la raíz contaminan cualquier listado inyectado a un agente — filtrar por convención, no limpiar a mano.

### Archivos de interés rápido
- `auditoria/registrar_lectura.py` — Gate de lectura previa (obligatorio antes de commit)
- `auditoria/verificar_alineacion.py` — 0 brechas antes de commitear
- `auditoria/auditar_calidad_tests.py` — Valida tests no sean "sniff"
- `scripts/enable_branch_protection.ps1` — Aplica/revisa branch protection en GitHub
- `.github/CODEOWNERS` — Revisión humana obligatoria

---

### Decisiones y hallazgos del ME r149_reparacion (2026-09-17)

- **H-R149-WIP (RESUELTO en working tree, sesión 2026-09-17):** el WIP del ME
  introdujo `var ultimo_tipo_tarea: entero = 0` a nivel de módulo en
  `opensyn/principal.syn` alegando "patrón de memoria_persistente_cifrada.syn".
  Verificado: (1) `var` NO existe en la gramática (Manual 2 §2 L134 solo define
  `let`; parser.py:148) y el compilador lo rechaza; (2) Synapse nativo no define
  globales mutables (semantic_checker.py:341-343 — `variable` es keyword de
  SyQuex, Manual 3 §3); (3) `let` a nivel de módulo SÍ emite el global en el C
  MONOLÍTICO pero NO en el MODULAR (queda como local sombra dentro de
  `_principal_impl` — sondeado con probe en $TEMP); (4) el "patrón de
  referencia" `memoria_persistente_cifrada.syn` usa `var` en fuente pero ni
  siquiera compila aislado (header `#lang`). Fix definitivo: sin estado global —
  `tui_agente()` retorna la clasificación (0..4), `tui_comando()` la recibe por
  parámetro (mismo nombre → lectores /next sin tocar) y el estado es `let`
  local en `chat_tui()` y `modo_oraculo()`. Exe fresco relinkado. Lección:
  verificar que el patrón citado en un comentario realmente compila antes de
  copiarlo; los comentarios de WIP no son evidencia.
- **H-R149-2 (RESUELTO en working tree):** la autodetección de expedientes en
  `alineacion.py --verificar` (sin `--me`, la que corre el hook) matchea por
  INTERSECCIÓN de archivos y recorre `docs/alineacion/*.md` alfabéticamente:
  expedientes históricos (ME-7, f31_*, f32_*) con anclas PENDIENTES y hash
  vacío interceptaban cambios nuevos que tocaban los mismos archivos (ej.
  `opensyn/principal.syn` está en ME-7 y en r149) → el gate validaba contra un
  expediente muerto y bloqueaba. Fix: expedientes históricos archivados en
  `docs/alineacion/archivo/` (el glob de autodetección no es recursivo); el
  expediente activo r149_reparacion queda en la raíz. Los tests no dependen de
  ellos (test_alineacion_control.py usa fixture ME-T).
- **H-R149-EXP (RESUELTO en working tree):** el expediente
  `docs/alineacion/f32_4b_cita_principal.md` era un borrador no verificable:
  duplicaba anclas de `r149_reparacion.md` sobre el MISMO cambio_hash
  (94c9b9fff045f0e2) con solo 1 de 12 archivos → "el expediente no tiene bloque
  para: …". Además usaba clave `citation:` (el validador lee `cita:`) y apuntaba
  a Manual 3 §12.1 que NO existe (Manual 3 termina en §12 sin subsecciones; la
  cita literal vive en §12, línea 458). Consolidado: expediente borrado, su plan
  apunta a r149_reparacion.md.
- **D-R149-1 (RATIFICADA, con expresa aprobación del Arquitecto en sesión):** los
  comentarios `// cumple Manual` DEBEN citar secciones que existan en el índice
  de manuales (`docs/manuales/.indice.json`); NO pueden usarse secciones
  "ilustrativas" ni "mentoras" (ej. `Manual 3 §12.1: CLI debe aceptar -o` o
  `Manual 7 §8: capa de IA`). El requisito literal que el código implementa
  (texto no indexado como prosa) queda registrado en el PLAN MTS y en el
  EXPEDIENTE (bloque DESVIACION con `decision: D-R149-1`); el comentario en el
  código se ancla a la sección REAL más próxima que especifica ese archivo.
  Origen: 21 citas muertas heredadas en archivos del cambio; 14 re-ancladas a
  secciones reales (cli.py/synapse_rt.c/tiempo.h→M1 §3.2, M8 §4.1, M4 §2,
  M5 §2.6; opensyn/principal.syn→M7 §2.1/§2.3; permisos.syn→M7 §1.1), 7
  declaradas en expediente.
- **D-R149-2 (RATIFICADA, con expresa aprobación del Arquitecto en sesión):**
  `docs/gobernancia/mapa_alineacion.md` entraba `opensyn/permisos.syn` a
  `Manual 7 §7.3`, sección que NO existe en Manual 7 (que termina en §4.2).
  Corregido el mapa a `Manual 7 §1.1` (asistente IA local: permisos mínimos,
  cero telemetría, sin nube), que es la sección que realmente especifica el
  sandbox de rutas del agente. Origen: DEUDA de alineación 2026-09-14.
- **Nota técnica D-R149-3:** el formato del expediente de alineación permite
  `decision: D-xxx` solo en bloques DESVIACION (alineacion.py:605-611); en
  CUMPLE solo hay evidencia+oráculo. Los archivos sin prosa citable (cabeceras
  nuevas) se anclan a la sección real que especifica el área.

## 💡 2. ERRORES RECURRENTES (patrones a evitar)

1. **Encoding UTF-8 en `subprocess.run`** en Windows
   - ❌ `subprocess.run([...], text=True)` → usa `cp1252` por defecto → `UnicodeDecodeError`
   - ✅ Siempre: `subprocess.run([...], text=True, encoding="utf-8", errors="replace")`
   - Archivos afectados: `auditoria/verificar_alineacion.py` (fix en commit 553fde1)

2. **ABI mismatch CadenaSegura**
   - ❌ Añadir campos a `CadenaSegura` (struct en C) → desborda 16 bytes de `synapse_rt_types.h`
   - ✅ Solo 16 bytes exactos (`Manual 2 §4.1`): `{char* datos; int longitud; int capacidad;}`
   - Solución para C functions que retornan malloc'd: `pool_alloc` + `pool_free`

3. **GitHub API version obsoleta**
   - ❌ Usar default o `2022-04-21` → error 400 "Problems parsing JSON"
   - ✅ Siempre header `X-GitHub-Api-Version: 2022-11-28`

4. **Ruleset API — `integration_owner` como string**
   - ❌ `"integration_owner": "synapse"` → 422
   - ✅ `"integration_owner": ["GitHub Actions"]` (array) o omitir

5. **Ruleset API — `ref_name` pattern**
   - ❌ `"include": ["main"]` → 422 "Invalid target patterns"
   - ✅ `"include": ["refs/heads/main"]`

6. **PowerShell `git add && git commit`**
   - ❌ `&&` no funciona en PS 5.1 (error parser)
   - ✅ Usar `;` o ejecutar comandos por separado

7. **PowerShell `Out-File -Encoding utf8`**
   - ❌ Agrega BOM que rompe `gh api --input`
   - ✅ Usar `-Encoding ascii` o `[System.IO.File]::WriteAllText()`

8. **`git diff` puede devolver `None` en hooks**
   - ❌ `diff.splitlines()` → `AttributeError: 'NoneType'`
   - ✅ Siempre `diff = out.stdout or ""`

---

## 📚 3. LECCIONES CLAVE

### Arquitectura / Diseño
- **D-F22-A:** Frontends Syquex → Synapse (no .syq hasta completar fase)
- **R10:** `pool_alloc` registra punteros fuera-del-pool en `_g_extra_ptrs[]` → `pool_free` solo libera punteros registrados → literales estáticos = no-op
- **Regla D-2:** Escanear TDOS los parámetros (retorno + params) para ADT en nativo
- **Regla H-R90-8b:** Inyectar `principal` en .syq source físico ANTES del runtime S1

### Build / Bootstrap
- **S2==S3 byte-idéntico** (criterio de aceptación por fase)
- **Timeout builds ≥ 900s** (`python main.py` toma 2-5 min)
- **Verificar timestamp del exe** después de build (no asumir por log)
- **`nucleo/generator.syn` es UNITY regenerado** → `_rebuild_generator.py` después de editar `nucleo/generador/`

### Codificación / Patrones
- **Parámetros de salida:** funciones C no pueden devolver `CadenaSegura` por valor → usar buffers por puntero
- **Escapado en `.syn`:** `\\n` (2 BS) → `\n` en C emitido; `\\\\n` (4 BS) para arrays C embebidos
- **Lexema real en tokens:** todo token debe conservar el lexema del buffer fuente (patrón `lexer_push_token_punt`)
- **Pre-scans AST:** deben cubrir TODOS los attrs recursivos (`'derecho'`/`'izquierdo'`)
- **Stubs con structs:** emitir SOLO cuando ADT instanciado en el programa

### TDD / Tests
- **Test nace del MANUAL, no del código** → si el test falla, corregir el CÓDIGO (no el test)
- **Sin `pytest.skip`** → el test debe FALLAR si código no implementado
- **`pytest --collect-only -q` = 0 errores** ANTES de cada commit
- **Baseline `git stash`** antes de modificar (confirmar fallas preexistentes)
- **Leer manual antes de tocar tests** → registrar lectura en `auditoria/registrar_lectura.py`

### Seguridad (FFI / RAI)
- **RAII sobre literales estáticos → 0xC0000374 (heap corruption)** → fix `pool_free` registry
- **CadenaSegura: 16 bytes exactos** → no usar `es_externo` (causaba ABI mismatch)
- **Nonce CSPRNG:** `randombytes()` C API, no `rand()` (Manual 6 §5.3)
- **Serialización:** validar ESTRUCTURA 0x08 rechazada sin esquema

---

## 📜 4. HISTÓRICO DETALLADO (F1–F27)

> 📄 **Snapshot completo con historia de fases, fixes y decisiones arquitectónicas.**
> Ver: `docs/bitacoras/HISTORICO_F17_F27.md` (contenido preservado de la estructura legacy).

**Fase completa:** F23 — Syquex auto-alojado (parche de bootstrap S1→S2→S3)
**Fase completa:** F26 — Herramientas (S1 bootstrap toolchain)
**Fase completa:** F27 — Herramientas de Desarrollo (LSP, VS Code, Debugger)
**Fase completa:** F32 — Agente de Codificación Avanzado y Memoria Persistente

| Fase | Estado | Commit | Tests | Reporte |
|------|--------|--------|-------|---------|
| F11 | ✅ | fb5b75c | — | FASE_11.md |
| F12 | ✅ | ce1f846 | 417/417 | R79/R80 |
| F13 | ✅ | ce1f846 | 233/233 | R79 |
| F14 | PARCIAL | — | 95/95 | — |
| F15 | ✅ | 633ed03 | 164/164 | R82 |
| F16 | ✅ | — | — | R42 |
| F17 | ✅ | 4e0ab7f | — | FASE_17.md |
| F18 | ✅ | 1f278d8 | — | — |
| F19 | ✅ | a7ec2af | 24/24 | R78/R83/R84 |
| F20 | ✅ | — | 7/7 | — |
| F21 | PARCIAL | — | — | RAII completa, destructor maps F23 |
| F22 | ✅ | — | — | D-F22-A aplicado |
| F23 | ✅ | — | — | Syquex auto-alojado |
| F26 | ✅ | — | — | Toolchain S1 |
| F27 | ✅ (52/52) | 1aa62ba | 52/52 | — |
| F32 | ✅ (72/72) | 20ba43f | 72/72 | — |

### Decisiones clave históricas
- **D-F22-A (2026-08-10):** Frontends Syquex → Synapse (no .syq hasta completar fase). Justificado por Manual 1 §4 (auto-alojado) + paradoja de bootstrap.
- **R7 (2026-08-10):** Parser nativo pasada 3 declara parámetros en scope → elimina 653 falsos positivos "variable no declarada".
- **R10 (2026-08-10):** RAII sobre literales estáticos — fix en `runtime/core/memory.c` con `_g_extra_ptrs[]`.
- **R11 (2026-08-10):** Exhaustividad `coincidir` nativa → switch sobre `.tag` + hoisting D-2 para ADT en parámetros.
- **R13 (2026-08-11):** Tipos ADT anidados → parseo balanceado `<...>` (consumir solo `>` de nivel 0).

---

## 📋 5. CHECKLIST DE VERIFICACIÓN (antes de commitear)

1. ✅ `python auditoria/verificar_alineacion.py` → 0 brechas
2. ✅ `python auditoria/registrar_lectura.py --pendientes` → nada pendiente (registrar lecturas si modifica productivo)
3. ✅ `python -m pytest <tests-afectados> -v` → todos pass
4. ✅ `git diff --cached --name-only` → solo paths explícitos (no `.exe`/artefactos)
5. ✅ Trailing whitespace: `grep -r ' $'` en archivos modificados
6. ✅ Hook pre-commit: limpieza artefactos + higiene + alineación + lectura previa
7. ✅ Si agregaste `docs/plan_ME_*.md`: `python auditoria/contrastar.py --plan docs/plan_ME_<id>.md` → 0 brechas

> 📄 Para historia completa, decisiones y debugging detallado: `docs/bitacoras/HISTORICO_F17_F27.md`

### H-INST-1 (2026-09-08): Inno Setup installer download pages frozen
- **Síntoma:** `DownloadPage` showed "Descargando..." but progress bar never moved; download was invisible
- **Causa raíz:** `DownloadFile()` used `Exec(... ewWaitUntilTerminated)` which blocked the UI thread entirely. Even though DownloadPage was added at `wpInstalling`, the UI never repainted during download.
- **Fix:** Changed `DownloadFile()` to use `Exec(... ewNoWait)` with `Sleep(1000)` polling loop + `WizardForm.Repaint`. Moved `DownloadPage` from `wpReady` to `wpInstalling` so it appears during actual installation phase.
- **Compilación:** `ISCC.exe` exitoso — `Synapse-8.1.0-industrial-Windows-x64.exe` generado
- **Resolución:** Fix aplicado, usuario debe probar con reinstalación limpia

### H-TEST-REPAIR (2026-09-14): Reparación de tests bajo MTO/TDD — 9 bugs reales de producción
- **Regla aplicada:** MTO/TDD — el test es el oráculo; se corrige CÓDIGO, jamás tests (regla 5).
- **Bugs corregidos (producción):**
  1. `sino si` no compilaba (parser Python y espejo .syn se comían el `sino`) → desugar a `si` anidado (paridad `_P_si` C): `compilador/parser_control.py`, `nucleo/parser_sentencias.syn`
  2. Frontend Syquex sin enlazar: blob `importar` llamaba `sq_arena_alloc` inexistente → usa `sbuf/str_pos` de SqLexerBuffers (1 MiB), disponible en TODO contexto lexer+parser (antes usaba trad_arena que no existe en el combinado de test_parser): `syquex/parser.syn`
  3. `para i en 0..10` (rango, Manual 3 §L133) sin soporte frontend → `sq_para_desugar` reutiliza el desugar C-style + contratos requiere/garantiza (Manual 2 §12): `syquex/parser.syn`
  4. `intentar:` (forma bloque) se parseaba como forma funcional → el `:` inmediato ahora fuerza bloque: `syquex/parser.syn` (sintaxis del dialecto: `y` no `&&`)
  5. `escuchar c:` consumía `:` dos veces → removido el token_esperar duplicado: `syquex/parser.syn`
  6. `canal <- valor` generaba `0;` (envío NUNCA emitido en ruta .syq) → SentenciaExpr despacha sentencias de canal envueltas: `compilador/generator/generator.py`
  7. `texto` no puede viajar por canal como void* → par runtime `canal_enviar_texto`/`canal_recibir_texto` (CadenaSegura por valor + liberación heap emisor): `runtime/core/concurrency.c`, `synapse_rt_types.h`, emisores
  8. `extern void _listener_N` faltante (pre-scan no recursaba en cuerpos) → `_contar_escuchar_emision` recorre funciones: `compilador/generator/generator.py`
  9. Send `<-` parseaba su RHS con unario (envío anidado en suma → C inválido) → el envío consume la expresión completa y retorna: `syquex/expr.syn`
- **Enlaces rotos en conftest (build, no tests):** `test_math/texto/tiempo/web` no enlazaban sus `.o` del runtime (math.o/texto.o/tiempo.o/web.o). ADVERTENCIA: `test_tiempo/test_web` pasaban por EXES STALE (fuente Sep 1 > exe Aug 26) — trampa documentada en AGENTS.md; al reconstruir fallaban → enlace real corregido.
- **Resultado:** tests/syquex 273 passed (antes 252), 6 failed restantes = 2 contradicciones de FÁBRICA (regla 5 → Arquitecto):
  (a) `test_result.py` 3 tests exigen compilar INTENTO/PARA_EN por el puente vs `tests/unit/test_puente_canonico.py::test_no_soportados_fallan_rapido` exige fail-fast (decisión 93e1ee5: handlers generaban C silenciosamente incorrecto — PARA_EN→while(0), LISTA_LIT→NULL). AMBOS inmutables → decisión del Arquitecto: o implementar backend de NODO_INTENTO/ PARA_EN, o modificar test_result.
  (b) `test_wasm_extended.py` 3 tests exigen el WAT en stdout vs el C nunca lo imprime (solo buffer interno + archivo .wat temporal que borra). Roto desde el commit de creación 45cfcd7 (test C y test Python nacieron incompatibles).
- **Otros fallos verificados preexistentes a HEAD (no míos):** `test_r3_param_adt` (D-2 documentada, ROJO TDD deliberado), `test_seccion_es_de_manual` (roto por construcción propia, documentado).
- **Gates:** verificar_alineacion SIN BRECHAS (D-9: syquex/parser.syn registrado en MODULOS_D9.md); lectura file-binding OK (24 registros); MTO rc=0; MTS multi-plan rc=0.
- **Lección:** exe stale = verde falso (confirmado empíricamente 2 veces en esta ronda); el verificador anti-stale de build_syquex_frontend.py funciona, el patrón `if os.path.exists(BIN_ABS): return BIN_ABS` en fixtures NO verifica mtime.

---

## 🚦 1. DASHBOARD — Actualización de sesión 2026-09-16

**Exploración FFI y arquitectura del AST:**

- Fase 32 completada (F32.1-F32.4). Próximo ME: Fase 32.5+ (puente FFI lista/mapa).
- **Fase 32 completada** (F32.1-F32.5, 72 tests GREEN):
  - **F32.1 Grafo de Conocimiento** (fa34825): `nucleo/grafo_conocimiento.syn` (471 líneas, 22 funciones, 13 tests)
  - **F32.2 Explorer + Architect Det.** (de7107c): `opensyn/explorer_det.syn` (BFS, `ArchivoRelevante`, 6 tests) + `opensyn/architect_det.syn` (DFS invertido + Tarjan, `AnalisisImpacto`, 11 tests)
  - **F32.3 Memoria Persistente Cifrada** (e0493bf): `opensyn/memoria_persistente_cifrada.syn` (XSalsa20-Poly1305 + Argon2id, 14 tests)
  - **F32.4 Pipeline Multi-Agente** (f3dab3f): `opensyn/pipeline_multiagente.syn` (5 fases, 5 modos, 15 tests)
  - **F32.5 Verificación AOT** (20ba43f): `opensyn/verificacion_aot.syn` (auto-refutación, timeouts, 13 tests)
  - Todos con plan MTS, expediente de alineación, lecturas registradas.
- `nucleo/grafo_conocimiento.syn` registrado en `docs/gobernancia/mapa_alineacion.md`
  → Manual 6 §1.1, Manual 2 §5.1.
- SemNodo struct confirmado en `nucleo/analizador_semantico.syn:74` + `nucleo/ast_abi.syn`;
  NODO_* constants provienen de `importar parser_constantes` (Manual 2 §7.2 = ILUSTRATIVO).
- Patrón FFI lista/mapa: `entero` handle, NO `lista`/`mapa` tipo. Ver detalle en
  `docs/fases/f32_exploracion_ffi.md`.

**Archivo de referencia:** `docs/fases/f32_exploracion_ffi.md` (bitácora completa de la exploración).

## 🚦 1. DASHBOARD — Actualización de sesión 2026-09-17

**Fase 32 COMPLETADA — Agente de Codificación Avanzado y Memoria Persistente:**

- Fase 32 completa (F32.1-F32.5). 72 tests GREEN, 5 expedientes, 5 planes MTS.
- Próximo: definir Fase 33 del roadmap.

## 🚦 1. DASHBOARD — Actualización de sesión 2026-09-18

**ME r150_funcional EN CURSO — estado de oráculos y gates (WIP sin commit):**

- Plan: `docs/plan_ME_r150_funcional.md` (12 bloques: M1 llvm/wasm a _RT_FUENTES,
  M2 cluster worker_*, M3a-d CLI honesto, M4 construir eliminado (D-R150-2),
  M6 versión única desde VERSION, M7 raw string, M13 .gitignore, M14 pytest-timeout,
  M15 std/testing.verificar + oráculo matriz de compilación).
- WIP (12 archivos): cli.py, pipeline.py, compilador/generator/generator.py,
  runtime/core/cluster.{c,h}, std/testing.syn, scripts/verificar_e2e.py,
  .gitignore, requirements.txt, ROADMAP.md + NUEVOS: plan, tests/auditoria/test_oraculos_r150.py.
- ORÁCULOS R150 (sesión 2026-09-18, ronda 2): test_oraculos_r150.py **14/14 GREEN**.
  - M2 RESUELTO: el probe C ahora enlaza la FRONTERA CANÓNICA del S1 (_RT_FUENTES:
    synapse_rt + runtime/core/*.c + motores nucleo + tweetnacl + sqlite3 + cuánticos +
    federated + IA, pipeline.py:828-850) — el harness anterior enlazaba solo
    cluster.c+synapse_rt.c y el link reventaba con pool_alloc/sha256_*/crypto_*.
    Lección: un probe que enlaza menos que el S1 no mide la frontera real.
  - M3d RESUELTO (2 bugs reales en cli.py): (1) `_debug_cargar_traza` construía la
    lista `eventos` pero nunca la incluía en `meta` → KeyError 'eventos' (D-R150-5);
    (2) `--reverse` con semántica off-by-one: el cursor apunta al SIGUIENTE evento
    de --step, retroceder debe mostrar _dbg_pos-2 (D-R150-6).
  - M4 RESUELTO: `axon_build.exe` eliminado también de los comentarios de cli.py.
  - MATRIZ (sesión 2026-09-18, ronda 3): **31/35**. math/mem RESUELTOS con D-R150-8:
    los prototipos hardcodeados `Tensor crear_tensor(int,int)`/`Tensor reserva(int)`
    en generator.py:893/emit_tensors.py contradecían las definiciones int64_t
    emitidas desde std.math/std.mem (entero→int64_t desde 86e89db) → "conflicting
    types" en _synapse_shared.h. Fix: int64_t en prototipos y emisores; el ancho
    64-bit de entero está en Manual 2 §4.1 ("Alias de int64_t") — ancla real, sin
    desviación. Regresión: 633 passed/4 failed línea base EXACTA.
  - MATRIZ (sesión 2026-09-18, ronda 4): **35/35 GREEN — ME CERRADO**. Los 4 fallos
    restantes resueltos con D-R150-9/D-R150-10:
    (a) parseo: Manual 2 §2 L56 hace `[ "->" tipo ]` OPCIONAL en declaracion_funcion;
        el parser lo exigía → retorno ausente normaliza a 'nulo' en
        _parsear_def_funcion y _parsear_externo_funcion (+ UnboundLocalError de
        tok_retorno en DeclaracionExterna corregido);
    (b) casts `(Decimal)x`: no existen en la gramática; la coerción entero→decimal
        en FFI es implícita (verificada por bisección, caso F) → eliminados de
        symbolic_exec se_crear_entero;
    (c) TVar ambiguo en quantum_err_corr: CAUSA RAÍZ = tipos capitalizados
        (Entero/Decimal/Puntero/Cadena/Booleano) no son aliases de Manual 2 §4.1;
        el generador los acepta pero el checker unifica TVar frescos por ocurrencia
        (bisección: C3 capitalizado RED, canónico GREEN) → los 4 std normalizados a
        los canónicos en minúsculas;
    (d) agent_skills definía `principal` → colisión con el entry point del programa
        importador → renombrado a demostrar_agent_skills() (los std son bibliotecas,
        el patrón `principal() -> nulo` es solo de programa, M2 §13) + contrato
        requiere (M2 §12, gate global).
    Regresión final: 633 passed/4 failed = línea base EXACTA (0 regresiones).
- Notas D-R150 (ronda 4): (9) los tipos capitalizados NO son aliases del manual:
  los std y el runtime usan SOLO los canónicos §4.1 — el checker no los unifica y
  produce TVar ambiguos; (10) una biblioteca std jamás define `principal`; (11) las
  citas `cumple Manual` a secciones inexistentes (M7 §6 no existe) se re-anclan o se
  documentan como D-R149-1 — el gate las trata como citas muertas bloqueantes.
- GATES (ronda 2): `verificar_alineacion.py` **SIN BRECHAS**; `alineacion.py --verificar
  --me r150_funcional` **OK** (6 archivos, citas textuales verificadas, oráculo ejecutado,
  evidencia auditoria/evidencia/f82eddaa76c1b58f.json); lecturas previas registradas
  (3 registros: M1 §3.1 ×3, M5 §8.1 ×2, M2 §2 ×1); mapa_alineacion gana
  std/testing.syn → Manual 2 §2 (el requisito real del wrapper verificar es la
  gramática, no M7 §2.3); `contrastar.py --plan` resuelve los 12 requisitos y ejecuta
  los oráculos: el del ME pasa, la matriz sigue RED por diseño hasta cerrar los 6
  hallazgos std↔runtime.
- Notas D-R150: (5) meta['eventos'] debe viajar con la traza parseada; (6) semántica
  de cursor del debugger documentada en cli.py; (7) el oráculo matriz vive en SU
  propio archivo (job CI aparte) para que el oráculo del expediente sea ejecutable
  en verde mientras la matriz expone hallazgos; (8) los prototipos de builtin en
  generator.py y los emisores de emit_tensors.py deben mantener paridad de tipos
  con el C emitido (entero=int64_t, Manual 2 §4.1) — el compilador y sus protos
  son UNA sola frontera de tipos.
- GOBERNANZA RESUELTA (sesión 2026-09-19, decisión del Arquitecto "alinea todo a lo
  que indican los manuales"): (1) el oráculo matriz quedó integrado en
  .github/workflows/ci-tests.yml como job aparte `matriz-compilacion` (ubuntu,
  gcc, 90 min) y los jobs test/bootstrap lo excluyen con --ignore (D-R150-7); (2)
  D-R150-9 RATIFICADA: Manual 2 §4.1 es la línea canónica — los tipos capitalizados
  NO son aliases y los std se normalizan a §4.1; el parser NO acepta capitalizados.
  Además el plan ganó los bloques M16/M17 (rondas 3-4) con citas M2 §2/§4.1 y el
  gate MTS fase 4b contrastar.py pasa con 14 requisitos y 2 oráculos ejecutados en
  release (docs/verificacion_ME_r150_funcional.md creado).
