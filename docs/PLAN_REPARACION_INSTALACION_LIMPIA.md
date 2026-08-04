# PLAN DE REPARACIÓN — INSTALACIÓN LIMPIA FUNCIONAL (v5.1.1-industrial)

> **Propósito:** Registro oficial para continuar en próximas sesiones la reparación de los
> fallos de build en instalación limpia y CI. Este documento es AUTOCONTENIDO: no depende
> del historial de conversación.
>
> **Autor:** Buffy (Freebuff AI) — Programador Synapse
> **Fecha de creación:** 2026-08-03
> **Versión del proyecto:** 5.1.1-industrial
> **Commit auditado en el diagnóstico:** `2e50e4dce5dffc6c5ceaf170ec3b612dfdb056cf`
> **Estado del plan:** 🔄 EN PROGRESO (9 micro-entregables definidos, 7 ejecutados)

---

## 1. CONTEXTO Y SÍNTOMA

El Arquitecto reportó: al hacer una **prueba de instalación en limpio** (clon del repositorio
de GitHub), **faltan archivos necesarios** que sí existen en el repo local, y **nunca se
genera `synapse.exe`**. Los **workflows de GitHub fallan al compilar el binario estático**.

**Síntoma exacto reproducido** (comando literal de `.github/workflows/windows_release.yml`):

```bash
gcc -O2 -static -o synapse-windows-amd64.exe synapse_unity.c synapse_rt.c -I. -lws2_32
# → undefined reference to: pool_alloc, pool_free, pool_init, _pool_malloc, _syn_texto_liberar
#                          crypto_sign_ed25519_tweet, _keypair, _open
# → synapse-windows-amd64.exe: No such file or directory   (NO se genera el binario)
```

**Corrección mínima VALIDADA** (probada en clon limpio; exe de 1,169,510 bytes generado):

```bash
gcc -O2 -static -o synapse-windows-amd64.exe synapse_unity.c synapse_rt.c \
    runtime/core/memory.c runtime/core/concurrency.c tweetnacl.c -I. -lws2_32 -lm
```

---

## 2. DIAGNÓSTICO — CAUSAS RAÍZ (con evidencia)

### Causa A (PRINCIPAL): El runtime modularizado no se enlaza en CI
- El commit `f03a7f5` ("M0.2: Modularización runtime/core") **movió** `pool_alloc`/`pool_free`/
  `pool_init` desde `synapse_rt.c` a `runtime/core/memory.c` y las funciones de canales a
  `runtime/core/concurrency.c`. `tweetnacl.c` aporta `crypto_sign_ed25519_tweet*`
  (mapeado vía `tweetnacl.h` líneas 200-209).
- **Workflows afectados:**
  - `windows_release.yml` — enlaza solo `synapse_unity.c synapse_rt.c` → FALLA.
  - `release-binaries.yml` — compila `tweetnacl.o` pero **no lo pasa al link** y no enlaza
    `runtime/core/*.o` → FALLA en los 3 OS.
  - `release_matrix.yml` — compila `runtime/core/*.c` + `tweetnacl.o` y los enlaza → ✅ ÚNICO CORRECTO.
  - `ci-tests.yml` (job `bootstrap`) — grepea `error:` en el log de `python main.py src/main.syn`;
    el log contiene `gcc: error: synapse_rt.o...` y errores C → FALLA.
  - `build-installer.yml` / `cross-compile.yml` — esperan `dist\bin\synapse.exe` que nunca se
    genera → FALLA.
- **Símbolos indefinidos (8):** `_pool_malloc`, `_syn_texto_liberar`, `pool_alloc`, `pool_free`,
  `pool_init`, `crypto_sign_ed25519_tweet`, `crypto_sign_ed25519_tweet_keypair`,
  `crypto_sign_ed25519_tweet_open`. (Log: `/tmp/clean_link.log` en la sesión de diagnóstico.)

### Causa B: `pipeline.py` espera `.o` precompilados que no existen en instalación limpia
- `pipeline.py` `_resolve_rt_obj()` (líneas ~502-516 y ~767-780) busca `synapse_rt.o`,
  `synapse_rt_memory.o`, `synapse_rt_concurrency.o`, `tweetnacl.o` en la raíz o `dist/lib/`.
  Si no existen, **devuelve la ruta igualmente** y el link falla **SILENCIOSAMENTE**
  (imprime `[!]` pero devuelve exit 0).
- Los fuentes `synapse_rt_memory.c` / `synapse_rt_concurrency.c` **no existen** ni en disco
  ni en git (fueron movidos a `runtime/core/`).
- **El build local solo funciona gracias a 28 objetos `.o` huérfanos en la raíz**
  (`synapse_rt.o`, `synapse_rt_memory.o`, `synapse_rt_concurrency.o`, `tweetnacl.o`,
  `axon_rt.o`, `_*.c.o`, `nucleo/quantum_*.o`) **ignorados por git** → nunca llegan a GitHub.
  **ESTOS son los "archivos que están en el repo original pero faltan en la instalación limpia".**
- Reproducción con el binario nativo en clon limpio (`./synapse.exe hola.syn`):
  ```
  gcc: error: synapse_rt.o: No such file or directory
  gcc: error: synapse_rt_memory.o: No such file or directory
  gcc: error: synapse_rt_concurrency.o: No such file or directory
  gcc: error: tweetnacl.o: No such file or directory
  [Synapse] ERROR: GCC fallo con codigo 1 → "Error de compilacion" → NO se genera .exe
  ```

### Causa C: Errores de C reales en módulos generados (nested functions = extensión GCC)
- El generador emite **funciones anidadas** (extensión GCC). `clang` las rechaza:
  ```
  .\_principal.c:246:37: error: function definition is not allowed here
  .\_principal.c:270:41: error: function definition is not allowed here
  .\_principal.c:395:48: error: call to undeclared function '_f8_flatten'
  clang-22: error: no such file or directory: '...synapse_rt.o'
  ```
- La máquina local resuelve **clang-22 (LLVM-MinGW de WinGet)** como compilador; los errores
  se **tragan** (pipeline devuelve 0). `release_matrix.yml` ya fuerza `export CC=gcc`.
- `nucleo/generator.syn:2982` emite `extern void* pool_alloc(size_t size);` → el C generado
  depende del runtime modular (consistente con Causa A).

### Causa D: Instalador (Inno Setup) roto por dependencias ausentes
- `instalador_synapse.iss` referencia recursos que **no existen**:
  - `LicenseFile=LICENSE.txt` → NO existe (solo `LICENSE` sin `.txt`) → iscc falla.
  - `SetupIconFile=assets\synapse.ico` → NO existe `assets/` → iscc falla.
  - `Source: dist\bin\synapse.exe` → nunca se genera (Causa A) → instalador sin compilador.
  - `build_installer.bat` (raíz) → **NO existe** (referenciado en docs, ausente en disco/git).

### Causa E: Tests que dependen de `.o` locales (skips silenciosos en CI)
- Muchos tests usan constantes `TWEETNACL_O`, `SYNAPSE_RT_O`, `SYNAPSE_RT_MEM_O`,
  `SYNAPSE_RT_CONC_O` apuntando a la raíz del repo (v.g. `tests/integration/*.py`,
  `tests/test_toml_raii.py`, `tests/stress/run_stress.py`, `tests/fuzz/*`).
- Si el `.o` falta → `pytest.skip` → **en CI esos tests ni corren** ("184/184" solo se
  cumple localmente con los `.o` presentes).
- Patrón correcto ya existente: `tests/stress/run_stress.py` L51-57 auto-compila `tweetnacl.c`
  si el objeto no existe.

---

## 3. PLAN DE MICRO-ENTREGABLES (ME-R1 … ME-R9)

**Dependencias:**
```
ME-R1 → ME-R6 (instalador)
ME-R2 ─┬→ ME-R4 → ME-R5
ME-R3 ─┘        ME-R7 → ME-R9 (certificación final)
                ME-R8
```

### ME-R1 — Workflows de CI: enlazar el runtime modular completo ⚡ (fix ya validado)
- **Manual:** Manual 3 §3.1 | Manual 8 §8.1 | Manual 9 §9.1
- **Archivos:** `.github/workflows/windows_release.yml`, `.github/workflows/release-binaries.yml`
- **Cambios:**
  - `windows_release.yml`: link con `synapse_unity.c synapse_rt.c runtime/core/memory.c
    runtime/core/concurrency.c tweetnacl.c -I. -lws2_32 -lm` (comando validado).
  - `release-binaries.yml`: pasar `tweetnacl.o` y los objetos `runtime/core/*.o` al link.
- **Validación:** clon limpio (`git archive HEAD`) + comando del workflow → exe generado.
- **Criterio:** binario estático generado en los 3 OS; CI verde.

### ME-R2 — `pipeline.py`: compilar runtime desde fuente + propagar errores
- **Manual:** Manual 9 §9.7 ("0 errores GCC") | Manual 4 §4.4 | Manual 6 §6.4
- **Archivos:** `pipeline.py` (L502-516 `_resolve_rt_obj` en `ejecutar_compilador`;
  L767-780 en `_link_object`)
- **Cambios:**
  1. Nueva función `_compilar_runtime()` → compila desde fuente a `build/obj/` (gitignored):
     `synapse_rt.c`, `runtime/core/memory.c`, `runtime/core/concurrency.c`, `tweetnacl.c`
     (+ `nucleo/quantum_*.c` si existen) con `-I.`.
  2. Sustituir `_resolve_rt_obj` por los objetos compilados.
  3. **Propagar fallos**: cualquier fallo de `gcc -c`/link → exit code ≠ 0 (hoy devuelve 0).
- **Validación:** `python main.py nucleo/principal.syn` en clon limpio genera
  `synapse_bootstrap.exe` funcional y el log NO contiene `error:`.
- **Criterio:** compilación completa desde clon limpio, 0 errores, exe utilizable.

### ME-R3 — `build.sh` / `build.bat`: rutas del runtime modular + pasos muertos
- **Manual:** Manual 3 §3.1 | Manual 9 §9.1
- **Archivos:** `build.sh`, `build.bat`
- **Cambios:** `synapse_rt_memory.c`/`synapse_rt_concurrency.c` → `runtime/core/memory.c`/
  `runtime/core/concurrency.c`; eliminar paso `fixup` (referencia `build/fixup_generator.py`
  que NO existe); resolver la referencia a `build_installer.bat` (crearlo o quitarlo de la doc).
- **Validación:** `build.bat bootstrap` y `build.sh` completos desde clon limpio.
- **Criterio:** Stage 1 genera `synapse_stage2.exe`; Stage 2→3 diff 0 bytes.

### ME-R4 — Toolchain: forzar GCC para el código generado
- **Manual:** Manual 8 §8.1 | Manual 9 §9.7
- **Archivos:** `pipeline.py` (`_resolver_toolchain_gcc`), `cli.py` (`_resolver_gcc`)
- **Cambios:** prioridad: `SYNAPSE_GCC_PATH` → `toolchain_gcc12/mingw64/bin/gcc.exe` →
  **gcc del sistema (antes que clang)** → clang solo en macOS (con gcc-N de brew).
  Documentar la dependencia de extensión GCC (nested functions) del generador.
- **Criterio:** compilación modular de `nucleo/principal.syn` con gcc → 0 errores de C.

### ME-R5 — Pipeline nativo: link desde fuente en `nucleo/principal.syn:404`
- **Manual:** Manual 9 §9.1 (bootstrap auto-hospedado) | Manual 3 §3.1
- **Archivos:** `nucleo/principal.syn` línea 404:
  `asm("snprintf(_cmd, 4096, \"gcc -O2 %s -fno-ident ... -I. synapse_unity.c synapse_rt.o synapse_rt_memory.o synapse_rt_concurrency.o tweetnacl.o -o \\\"%s\\\" -lpthread -lm -lws2_32\", ...)")`
  → cambiar por `synapse_unity.c synapse_rt.c runtime/core/memory.c runtime/core/concurrency.c
  tweetnacl.c ... -lpthread -lm -lws2_32`. Regenerar y commitear `nucleo/principal.c` si está
  trackeado (verificar con `git ls-files nucleo/principal.c`).
- **Validación:** con binario nativo recompilado en clon limpio: `synapse hola.syn` → genera
  `hola.exe` (hoy falla RC=5).
- **Criterio:** el compilador auto-hospedado compila programas en instalación limpia;
  bootstrap S1→S2→S3 diff 0 bytes.

### ME-R6 — Instalador: assets faltantes y binario previo
- **Manual:** Manual 9 §9.9.1 (empaquetado multi-target)
- **Archivos:** `instalador_synapse.iss`, `LICENSE`, crear `assets/`,
  `.github/workflows/build-installer.yml`, `.github/workflows/cross-compile.yml`
- **Cambios:** `LicenseFile=LICENSE` (o crear `LICENSE.txt`); resolver/eliminar
  `SetupIconFile=assets\synapse.ico`; **añadir paso que construya `dist\bin\synapse.exe`
  con el link de ME-R1** antes de `iscc`.
- **Validación:** `iscc instalador_synapse.iss` sin errores; instalador > 10 MB con
  `bin\synapse.exe` dentro.
- **Criterio:** instalación desde el instalador → `synapse --version` responde.

### ME-R7 — Tests: auto-compilar objetos del runtime (eliminar skips silenciosos)
- **Manual:** Manual 9 §9.3 / §9.7 (184/184 tests reales)
- **Archivos:** helpers de tests (constantes `TWEETNACL_O`, `SYNAPSE_RT_O/MEM/CONC` en
  `tests/integration/*.py`, `tests/test_toml_raii.py`, `tests/stress/run_stress.py`,
  `tests/fuzz/*`).
- **Cambios:** helper compartido que **auto-compila el runtime desde fuente** si el `.o` no
  existe (patrón de `tests/stress/run_stress.py` L51-57), apuntando a `build/obj/`.
- **Criterio:** en clon limpio `pytest tests/ -v` corre la suite completa sin skips por `.o`.

### ME-R8 — Higiene del repositorio
- **Manual:** Manual 9 §9.7 | `.gitignore` coherente
- **Cambios:**
  - Eliminar `.o` huérfanos locales (ignorados).
  - `git rm --cached` de `.axon_cache/*`, `tests/.axon_cache/*`, `test_lsp_bin.oculto`
    (contradicen CLASE G/Q del `.gitignore`).
  - Borrar archivo residual `Native` (31 bytes) y los accidentes `-o`, `--output`,
    `-o.exe`, `--output.exe` de la raíz.
- **Criterio:** `git status` limpio; `.gitignore` sin contradicciones.

### ME-R9 — Job CI de instalación limpia + documentación + certificación final 🏁
- **Manual:** Manual 9 §9.1, §9.7, §9.8/§9.9
- **Cambios:**
  1. Nuevo workflow `clean-install.yml`: checkout → `git archive HEAD` → `build.bat
     bootstrap-full` → link estático → `synapse hola.syn` → `pytest tests/ -v` → subir
     artefactos. **Bloquea regresiones futuras.**
  2. Actualizar `ROADMAP.md` (registro de cambios: Fase R), `BLOCKERS.md`,
     `tests/SKIPPED.md`, checklist Manual 9 §9.7.
- **Validación:** push de prueba en GitHub → todos los workflows verdes.
- **Criterio:** push a `main` con TODOS los workflows verdes.

---

## 4. PRUEBA DE ACEPTACIÓN FINAL (E2E instalación limpia)

```bash
git archive HEAD | tar -x -C /tmp/limpio && cd /tmp/limpio
python main.py nucleo/principal.syn          # → synapse_unity.c, sin "error:"
gcc -O2 -static -o synapse.exe synapse_unity.c synapse_rt.c \
    runtime/core/memory.c runtime/core/concurrency.c tweetnacl.c -I. -lws2_32 -lm
./synapse.exe --version                      # → responde
./synapse.exe hola.syn                       # → genera hola.exe
python -m pytest tests/ -v                   # → 184/184 PASS
build.bat bootstrap-full                     # → S2 == S3 (diff 0 bytes)
```

---

## 5. SEGUIMIENTO (marcar avance en cada sesión)

- [x] **ME-R1** — Workflows: link runtime modular completo (fix validado) — ✅ 2026-08-03, commit `7734d2b`
- [x] **ME-R2** — `pipeline.py`: runtime desde fuente + propagar errores — ✅ 2026-08-03, commit `80e18dd`
- [x] **ME-R3** — `build.sh`/`build.bat`: alineación Manual 9 §9.1 + paso fixup muerto eliminado — ✅ 2026-08-03, commit `c5f5b17`
- [x] **ME-R4** — Toolchain: forzar GCC antes que clang (resolver en pipeline.py absorbido por ME-R2; `cli.py` completado) — ✅ 2026-08-03, commit `547f1e8`
- [x] **ME-R5** — Pipeline nativo: `nucleo/principal.syn:404` link desde fuente — ✅ 2026-08-03, commit `0f1ac2c`
- [x] **ME-R6** — Instalador: `LICENSE`, fuentes runtime junto al binario, `dist\bin\synapse.exe` previo — ✅ 2026-08-03, commit `51ea954`
- [x] **ME-R7** — Tests: auto-compilar `.o` del runtime — ✅ 2026-08-04, commit `8310c17`
- [ ] **ME-R8** — Higiene repo (`.o`, `Native`, `.axon_cache`, `test_lsp_bin.oculto`)
- [ ] **ME-R9** — Workflow `clean-install.yml` + docs + certificación final

### Bitácora de ejecución

| Fecha | ME | Resultado | Evidencia |
|---|---|---|---|
| 2026-08-03 | ME-R1 | ✅ COMPLETADO — `windows_release.yml` y `release-binaries.yml` enlazan el runtime modular completo (`runtime/core/memory.c`, `runtime/core/concurrency.c`, `tweetnacl.c`); macOS usa gcc de brew (Causa C resuelta en el entregable) | Commits `7734d2ba1f9fee1960e268f0c69a7110a121ab24` + revisión `c921a5a41bdc6b9313490e46256eaa824a76238c` (shell:cmd para continuación `^`, gcc-12 en loop darwin); validado en clon limpio: `synapse-windows-amd64.exe` (1,169,510 B) y `synapse-test.exe` (1,290,818 B), RC=0, cabecera MZ; YAML OK |
| 2026-08-03 | ME-R2 | ✅ COMPLETADO — `pipeline.py` compila el runtime modular desde fuente a `build/obj/` y PROPAGA errores (Causas B/C/E). Absorbió la parte del resolver de ME-R4 (gcc antes que clang + branch darwin con verificación anti-shim). Destapó y corrigió bugs preexistentes enmascarados por la traga de errores: `std/debug.syn` (firmas `externo` no coincidían con el runtime C: `-> Resultado/TraceSession` vs `int/CadenaSegura`; wrappers ahora con prototipos C exactos en asm y `Resultado` ADT), `synapse_rt.c` (trazas ahora en `~/.synapse/traces` vía `_syn_home_dir`, antes `.synapse/traces` relativo al CWD), `tests/unit/test_debug.py` (fixture de aislamiento del directorio compartido de trazas), `tests/security/test_verificacion_formal.py` (`CODIGO_VALIDO_SAFE` sin `principal` → no enlazable) | Commit `80e18dd1f9132cbaf4674115f326ff49ff599082` (+ revisión: guard anti-shim clang en darwin y hint de `funcion principal` faltante). Validado en clon limpio: bootstrap RC=0 con 0 `error:`, `synapse_bootstrap.exe` (1,192,625 B) y `hola.exe` (857,938 B) generados, prueba negativa (toolchain roto) RC=1 con mensaje ME-R2. Suite completa: **667 passed, 0 failed, 9 skipped, 1 xfailed**. Post-revisión: 105/105 en tests afectados (safe, debug, lexer, parser). Tests modificados APROBADOS por el Arquitecto (ver nota de aprobación) |
| 2026-08-03 | ME-R3 | ✅ COMPLETADO — `build.bat`/`build.sh` alineados al Manual 9 §9.1 (Etapa 1 = `python main.py nucleo/principal.syn`): eliminado el paso `fixup` muerto (`build/fixup_generator.py`/`fix_2errors.py` inexistentes), eliminada la compilación manual de `.o` y el link modular sin `main` (imposible; el pipeline ME-R2 compila el runtime desde fuente); `build.sh` con lanzador python portable (anti-stub Microsoft Store) y `build_installer.bat` en raíz (wrapper → `scripts/build_installer.bat`) que los workflows de CI esperaban y se saltaban silenciosamente | Commit `c5f5b1709578f9e4889bb5458c0cb211cd752c1c`. Validado en clon limpio: `cmd //c build.bat bootstrap` → `synapse_stage2.exe` (1,192,625 B); `bash build.sh` → `synapse_v1.exe` (1,192,625 B) + `embedded_libs.h` regenerado (11 librerías). D4 detectado (determinismo embedded_libs) y D5 (opensyn stale) registrados |
| 2026-08-03 | ME-R4 | ✅ COMPLETADO — Toolchain GCC forzado en `cli.py` (`_resolver_gcc`): candidatos darwin brew `gcc-14/13/12` antes de `gcc`/`cc`, rechazo de shims de clang vía `--version` (macOS `/usr/bin/gcc` es clang), override `SYNAPSE_GCC_PATH` respetado, dependencia de extensiones GCC documentada (Manual 8 §8.1); `_auditar_memoria`/`_auditar_hilos` consolidados en `_resolver_gcc()` (antes `SYNAPSE_GCC`). La parte del resolver de `pipeline.py` quedó absorbida por ME-R2 | Commit `547f1e8fcf12e3257c4482234860352403b34354`. Validado: `py_compile` OK; `_resolver_gcc()` → toolchain_gcc12 (ES_CLANG: False); `SYNAPSE_GCC_PATH=clang` → clang (override respetado); `python cli.py hola.syn` → `hola.exe` (366,292 B). D6 registrado (auditorías con `.o` pre-ME-R2 → ME-R7). Revisión post-code-review: import `glob` muerto eliminado |
| 2026-08-03 | ME-R5 | ✅ COMPLETADO — **Bootstrap auto-hospedado reparado**: el asm de `nucleo/principal.syn:404` enlazaba `.o` inexistentes (`synapse_rt.o`… → RC=5); ahora enlaza desde fuente (`synapse_unity.c synapse_rt.c runtime/core/memory.c runtime/core/concurrency.c tweetnacl.c`, paridad ME-R1/ME-R2) | Commit `0f1ac2cece23e9c94b576056f668a8db8755dad3`. Validado en clon limpio: `python main.py nucleo/principal.syn` → unity 576,021 B con el fix; `gcc -static` → `synapse.exe` (1,169,546 B) con uso correcto; `./synapse.exe hola.syn` → RC=0 (antes RC=5), comando corregido en el log, `synapse_stage2.exe` (823,231 B); **Etapa 2** (auto-compilación) → `synapse_v2.exe` (1,159,107 B); **Etapa 3** → `synapse_v3.exe`; **DIFF 0 BYTES** (S2 == S3, md5 `9081419c…`). D7 (quantum nativo) y dependencia ME-R6 (rutas relativas) registrados |
| 2026-08-03 | ME-R6 | ✅ COMPLETADO — Instalador funcional + rutas absolutas del runtime: `nucleo/principal.syn` deriva el directorio del runtime via `GetModuleFileNameA` (guard `_WIN32` con fallback `.` para Linux/macOS, donde `__stdcall` no existe) + probe `fopen`; `instalador_synapse.iss` (LicenseFile=LICENSE, SetupIconFile eliminado, fuentes/headers del runtime en `{app}\bin` + `runtime\core` + `librerias\embedded_libs.h`, `librerias\*` → `{app}\librerias` Manual 9 §9.9.1, `scripts\install.ps1` → `{app}`, eliminados los `Source` inexistentes que abortaban iscc y el `[Run]` `_gen_embedded`); workflows con paso 4b (Setup MinGW + bootstrap + link ME-R1 → `dist\bin\synapse.exe` antes de iscc) y puerta de existencia | Commit `51ea9541d8be03e0f0795520d71a879e8488c12c0`. Validado en clon limpio: bootstrap RC=0; **binario instalado compila `hola.syn` desde CWD aislado (RC=0, rutas absolutas en el log)**; Etapa 2 auto-compilación RC=0 (`synapse_v2_r6.exe` 1,159,489 B); **portabilidad `gcc -U_WIN32` sin errores `__stdcall`** (post-revisión del revisor: el guard era crítico para build.sh/`release-binaries.yml` en Linux/macOS); YAML válido; 18 `Source` del .iss existen en el repo; suite completa 667 passed 0 failed. D8/D9/D10 registrados; **dependencia de rutas relativas RESUELTA** |

> **Aprobación del Arquitecto (2026-08-03):** los cambios a `tests/unit/test_debug.py`
> (fixture de aislamiento) y `tests/security/test_verificacion_formal.py` (dato de prueba
> `CODIGO_VALIDO_SAFE` con `principal`) fueron APROBADOS con justificación documentada, bajo
> la regla: **SIEMPRE preguntar antes de modificar cualquier test** (los tests son solo
> lectura por protección). Ninguna aserción fue modificada.
>
> **DEUDAS COMPROMETIDAS — resolución obligatoria en próximos ME (sin dejar deuda):**
>
> | # | Deuda | Resolución asignada |
> |---|---|---|
> | D1 | Desajuste ABI `tr_grabar_snapshot`: runtime `long long valor_entero` vs `std/debug.syn` `entero` (int). Latente: ningún test actual lo ejercita vía .syn (los de integración usan ctypes con la firma real del runtime). | ✅ **ME-R7** (`8310c17`) — firma alineada a `int` + prototipos colgantes en `test_distributed_debug.c`/`test_memory_snapshots.c`; validado con `test_time_travel.py`/`test_memory_snapshots.py` |
> | D2 | Un test C de tar borra el fixture `tests/fixtures/tar_test_out/test_normal.txt` como efecto secundario de la suite (restaurado con `git checkout` en cada corrida). | ✅ **ME-R7** (`8310c17`) — `test_axon_e2e_native.c` y extensión aprobada `test_path_traversal.c` operan sobre `.axon_cache/tar_test_out`; fixture intacto tras corridas |
> | D3 | Semántica de programa sin `funcion principal`: ME-R2 eligió RC=1 con hint explícito ("el programa no define 'funcion principal'"), lo que obligó a completar `CODIGO_VALIDO_SAFE`. | **ME-R9** — validar la semántica contra Manual 9 §9.1/§9.7 en la certificación final; si el Arquitecto prefiere RC=0 para bibliotecas, cambio de pipeline acotado (aviso explícito, sin generar exe) |
| D4 | **Determinismo de `embedded_libs.h`**: `tests/_gen_embedded.py` incrusta los bytes crudos de los `.syn`; en checkout Windows (CRLF) genera escapes `\r\n`, en Linux (LF) `\n` → el archivo regenerado difiere entre plataformas y rompe Manual 9 §9.7 ("mismo SHA-256"). Detectado en ME-R3 (hash 55ac7e7 → 3ae036c). Fix: normalizar fin de línea en el generador (toca `tests/_gen_embedded.py` → **requiere aprobación del Arquitecto** por la regla de tests) o forzar `eol=lf` para `librerias/*.syn` en `.gitattributes`. | **ME-R8** (con aprobación previa) |
| D5 | `opensyn/` stale: `opensyn/principal.syn` no bootstrapea (89 errores semánticos preexistentes); build.sh ya no lo usa (alineado a `nucleo/principal.syn`). | **ME-R8** — higiene: evaluar eliminar `opensyn/` o repararlo |
| D6 | Auditorías CLI (`cli.py test --auditar-memoria/--auditar-hilos`, Manual 9 §9.5) referencian `synapse_rt.o`/`synapse_rt_memory.o`/`synapse_rt_concurrency.o` en la raíz (nombres pre-ME-R2 inexistentes en clon limpio); además necesitan el runtime compilado CON sanitizadores desde fuente. | ✅ **ME-R7** (`8310c17`) — `_compilar_runtime_sanitizado()` compila desde fuente con `-fsanitize` a `build/obj/` |
| D7 | **Brecha quantum en el link nativo** (ME-R5): `nucleo/principal.syn` no incluye `nucleo/quantum_*.c` mientras el pipeline ME-R2 los enlaza condicionalmente → programas que usen `std.quantum` fallarían al compilar con el compilador nativo (símbolos `_syn_quantum_*` indefinidos). Coherente con el binario de release ME-R1, pero inconsistente con el pipeline. | **ME-R9** — alinear link nativo con el pipeline (o documentar la restricción) en la certificación final |
| 2026-08-04 | ME-R7 | ✅ COMPLETADO — Tests reales en clon limpio (Causa E) + deudas D1/D2/D6 aprobadas: **`tests/conftest.py`** fixture autouse session (HARNESS, sin tocar tests) que auto-compila desde fuente los `.o` del runtime a la raíz (tweetnacl/synapse_rt/synapse_rt_memory con `-DSYNAPSE_DEBUG_MEM`/synapse_rt_concurrency/axon_rt) con dependencias mtime (fuente + headers, incl. `librerias/embedded_libs.h` que memory.c/concurrency.c incluyen) y linkea **5 binarios de test** (work_stealing, cluster_raft, path_traversal_new, ed25519_axon_new con todos los .o; gen_axon_test_fixtures SOLO con tweetnacl.o por su `randombytes` propio — conflicto de símbolo evitado). Post-revisión: `.o` parcial se borra en fallo (evita reutilizar objeto corrupto con mtime fresco); fallo del fixture emite WARNING sin abortar suite. **D1**: `tr_grabar_snapshot` `long long valor_entero` → `int` (contrato `std/debug.syn` `entero`) + 2 prototipos colgantes en tests C alineados. **D2 + extensión aprobada**: `test_axon_e2e_native.c` y `test_path_traversal.c` → salida `.axon_cache/tar_test_out` (el binario viejo pre-compilado de la Causa E borraba el fixture trackeado en cada corrida); entrada `malicious.tar` intacta; CERO cambios de aserción. **D6**: `cli.py` `_compilar_runtime_sanitizado(dir_rel, san_flags)` compila el runtime modular desde fuente con `-fsanitize` a `build/obj/`; `_auditar_memoria`/`_auditar_hilos` lo usan (antes `.o` pre-ME-R2). Commit `8310c17`. Validado: clon limpio SIN `.o` ni binarios → `test_axon_e2e.py` 5 passed y `tests/integration/` **331 passed** (el fixture compiló todo desde fuente); suite completa **667 passed, 0 failed** (mismo baseline); **fixture trackeado `tar_test_out/test_normal.txt` permanece intacto (21 B) tras las corridas** |
| D8 | **std.* en el compilador instalado**: el `[Run]` `_gen_embedded` fue eliminado (ejecutaba un archivo no instalado); el instalador sí lleva `librerias/embedded_libs.h` en `{app}\bin\librerias` y `-I"{app}\bin"` la encontraría si el C generado la incluye como `librerias/embedded_libs.h`, pero NO se verificó que un programa con `std.*` compile con el binario instalado. | **ME-R9** — certificación: compilar un programa con `std.*` con el binario instalado |
| D9 | **iscc no validado localmente**: `iscc` no está instalado en la máquina de desarrollo → la compilación real del instalador (`iscc instalador_synapse.iss`) solo se validará en CI (ME-R9, push de prueba). Validación estructural hecha: los 18 `Source` del .iss existen en el repo. | **ME-R9** — validación iscc en CI |
| D10 | **Instalador < 10 MB en modo core**: sin MinGW empaquetado ni componentes IA (se descargan en tiempo de instalación vía `DownloadAIComponents` en `[Code]`), el instalador core queda ~2 MB → el criterio del plan "> 10 MB" no aplica al modo core (el workflow solo emite WARN, no falla). | Documentado; el tamaño real se completa en instalación con las descargas IA |
| ~~Dep.~~ | ~~**ME-R6 (instalador)**: rutas relativas del runtime~~ — **RESUELTA en ME-R6**: el link nativo deriva rutas absolutas via `GetModuleFileNameA` y el instalador coloca los fuentes/headers del runtime junto al binario (`{app}\bin` + `runtime\core` + `librerias\embedded_libs.h`). Validado: binario instalado compila `hola.syn` desde CWD aislado (RC=0). | ✅ ME-R6 (`51ea954`) |

---

## 6. DATOS CLAVE DE REFERENCIA (para retomar rápido)

| Ítem | Dato |
|---|---|
| Link roto CI (Windows) | `windows_release.yml` — falta `memory.c`, `concurrency.c`, `tweetnacl.c` |
| Link roto CI (multi-OS) | `release-binaries.yml` — `tweetnacl.o` compilado pero no enlazado |
| Workflow correcto (referencia) | `release_matrix.yml` (compila `runtime/core/*.c` y enlaza todo) |
| Link hardcodeado nativo | `nucleo/principal.syn:404` (asm snprintf gcc) |
| Extern pool_alloc en generador | `nucleo/generator.syn:2982` |
| Objetos que `pipeline.py` busca | `synapse_rt.o`, `synapse_rt_memory.o`, `synapse_rt_concurrency.o`, `tweetnacl.o` |
| Símbolos faltantes (8) | `pool_alloc`, `pool_free`, `pool_init`, `_pool_malloc`, `_syn_texto_liberar`, `crypto_sign_ed25519_tweet{,_keypair,_open}` |
| Fuente de los símbolos | `runtime/core/memory.c`, `runtime/core/concurrency.c`, `tweetnacl.c` (+`tweetnacl.h` L200-209) |
| Commit de modularización | `f03a7f5` (M0.2 — movió memory.c/concurrency.c a runtime/core/) |
| Toolchain local (dev) | clang-22 LLVM-MinGW (WinGet) — rechaza nested functions |
| Comando de fix validado | ver §1 (exe 1,169,510 bytes generado OK) |
| Tests con skips por `.o` | `tests/integration/*.py`, `tests/test_toml_raii.py`, `tests/fuzz/*` |
| Directorio temporal diagnóstico | `/tmp/synapse_clean`, logs `/tmp/clean_bootstrap.log`, `/tmp/clean_link.log` (sesión 2026-08-03) |

---

## 7. NOTAS DE GOBERNANZA

- Cada ME se entrega con el formato `--- REPORTE DE MICRO-ENTREGABLE ---` de
  `GUIA_DE_GOBERNANZA.md`:
  TAREA / FASE / MANUAL REFERENCIADO / HASH COMMIT / COMPILACIÓN (log 10 líneas) / TESTS /
  COBERTURA / MODIFICACIONES DE TESTS / MODULARIZACIÓN / RIESGOS / PRÓXIMO PASO.
- Reglas: no inventar APIs; `requiere`/`garantiza` en funciones públicas nuevas; sin
  hardcoding; si no se puede cumplir → DETENERSE y preguntar al Arquitecto.
- Los manuales se citan como `Manual N §Sección` (los archivos reales son
  `docs/manuales/MANUAL N.md` con espacio, aunque la guía los nombra con guion bajo).
