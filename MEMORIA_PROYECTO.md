# 🧠 MEMORIA DEL PROYECTO SYNAPSE

> **Formato optimizado para agentes.**
> - 🚦 **Sección 1 — Dashboard actual** (léase primero, < 30 segundos).
> - 💡 **Sección 2 — Errores recurrentes** (patrones a evitar siempre).
> - 📚 **Sección 3 — Lecciones clave** (reglas de arquitectura/tacticas).
> - 📜 **Sección 4 — Historico detallado (F1–F27)** — conserva el conocimiento profundo del proyecto.
> - 📋 **Sección 5 — Checklist de verificación** (validar antes de commitear).
>
Última actualización: **2026-09-08** (R144c: fix use-after-free RAII en compilador + optimización prompt para deepseek-1.3b)

---

## 🚦 1. DASHBOARD ACTUAL```yaml
Fase roadmap:      FASE 30-b HARDENING — OpenSyn TUI + IA local (R141/R142/R143) COMPLETADA
                   FASE 30 COMPLETADA — Instalación Unificada y Distribución Final
                   Fase 29 COMPLETADA
Estado:            R144c — fix use-after-free RAII en compilador (prompt limpio) + optimización
                   system prompt para deepseek-1.3b. Chat funcional con llama-server OpenAI API.
Commit fase:       db4ccf9 (R144b instalador) sobre a13332b/7d2edbc (F30-b)
Próximo ME:        FASE 31 (próxima fase del roadmap) o follow-ups H-R144-2/3/5
Próximo paso:      Decidir FASE 31 en ROADMAP.md (hoy termina en FASE 30) o cerrar
                   hallazgos del instalador (detección hardware -1, modelos.toml real,
                   upgrade silencioso sin llama-server)
Últimos commits:    db4ccf9 (fix(instalador): fuentes de enlace + hash reales + extracción completa llama-server)
                     a13332b (feat(opensyn): TUI pantalla completa + historial/Tab + vendor skills + instalador SHA256)
                     ce0e291 (fix(opensyn,runtime): R113 chat sin corrupción + UTF-8 + wizard instalador)
                     d9c498a (F30-b: chat OpenSyn real (Ollama) + consola UTF-8 + LSP multi-mensaje + instalador 8.1.0)
                     336c8a4 (docs(release): reporte R139 + fila auditoría + MEMORIA)
                     fa3c548 (feat(installer): generar instalador Windows Manual 9 §2.5)
                     d64a07e (fix(ci): normalizar CRLF→LF + limpiar artefactos)
                     8c0cdc4 (Prepare release v8.1.0-industrial: cross-compile workflow)
                     de901bb (ME_30_T8: Docs/Packaging)
                     f3e5ad3 (ME_30_T7: Auto-actualización)
                     5c22529 (ME_30_T6: Tests de smoke)
                     b1390ba (ME_30_T5: Verificación Ed25519)

                    72f60bd (ME_30_T4: Instalador macOS)
                    e5e9b58 (ME_30_T3: Instalador Linux)
                    5775c5a (ME_30_T2: Instalador Windows)
                    b9aa55f (ME_30_T1: Estructura instaladores)
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
| `7d2edbc` | R143/ME_opensyn_ia_gguf: motor GGUF local endurecido — vocab desde el array real tokenizer.ggml.tokens (antes solo escalar → 0 con GGUFs reales → rechazo), cache de posición O(n) para arrays, límites contra tamano_mmap, cache perezoso F32 (F16/Q4_0/Q4_1/Q5_0/Q5_1/Q8_0 exactos), dims GGUF ne[0]=contigua (w_k OOB corregido), top_p qsort O(vs log vs). Oráculo E2E determinista NUEVO GREEN: GGUF sintético (vocab 11, merges, token_embd Q8_0) → driver .syn compilado con S1 → carga+ingesta 5 tokens+generación "abababababababab" (temp=0)+cierre limpio. H-GGUF-2 INVARIANTE: output.weight debe tener n_vocab filas (LM head itera vocab del tokenizer). Reporte R143. |

### Deudas / Hallazgos críticos activos
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

### Archivos de interés rápido
- `auditoria/registrar_lectura.py` — Gate de lectura previa (obligatorio antes de commit)
- `auditoria/verificar_alineacion.py` — 0 brechas antes de commitear
- `auditoria/auditar_calidad_tests.py` — Valida tests no sean "sniff"
- `scripts/enable_branch_protection.ps1` — Aplica/revisa branch protection en GitHub
- `.github/CODEOWNERS` — Revisión humana obligatoria

---

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
**Fase actual:** F27 — Herramientas de Desarrollo (LSP, VS Code, Debugger)

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
