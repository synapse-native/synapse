# 🧠 MEMORIA DEL PROYECTO SYNAPSE

> **Formato optimizado para agentes.**
> - 🚦 **Sección 1 — Dashboard actual** (léase primero, < 30 segundos).
> - 💡 **Sección 2 — Errores recurrentes** (patrones a evitar siempre).
> - 📚 **Sección 3 — Lecciones clave** (reglas de arquitectura/tacticas).
> - 📜 **Sección 4 — Historico detallado (F1–F27)** — conserva el conocimiento profundo del proyecto.
> - 📋 **Sección 5 — Checklist de verificación** (validar antes de commitear).
>
> Última actualización: **2026-09-01T13:00Z** (FASE 29 COMPLETADA)

---

## 🚦 1. DASHBOARD ACTUAL

```yaml
Fase roadmap:      FASE 29 COMPLETADA — Detección de Hardware y Gestión de Modelos (Hito 8)
                   Fase 30 PENDIENTE
Estado:            F29 COMPLETADA — ME_29_T1 RED (requiere servidor), ME_29_T2 GREEN, ME_29_T3 GREEN (benchmark), ME_29_T3_mod GREEN, ME_29_T4 GREEN, ME_29_T5 GREEN, ME_29_T6b GREEN, ME_29_T5u GREEN, H-F29-T5b RESUELTO
Commit fase:       786cb3e (ME_29_T3_mod: test_gestion_modelos)
Próximo ME:        F30_T1 (instalador unificado)
Próximo paso:      Iniciar FASE 30 — Instalación Unificada y Distribución Final
Últimos commits:    786cb3e (ME_29_T3_mod: test_gestion_modelos)
                    dceca88 (ME_29_T2: bindings TypeScript)
                    9fd745e (ME_29_T5u: instalar_modelo + ConfigInfo + escribir_config)
                    478f047 (H-F29-T5b fix: malloc→pool_alloc en concat/sha256/home)
                    6063e39 (docs: R137 bitácora MEMORIA + auditoría para H-F29-T5b)
```

### Cambios recientes esta sesión
| Commit | Descripción | Impacto |
|--------|-------------|---------|
| pendiente | ME_29_T2: bindings TypeScript implementados | 1 test RED → GREEN (test_binding_typescript), funciones generar_typescript_completo y generar_javascript_wrapper agregadas |
| `478f047` | H-F29-T5b fix memory management mismatch | Fix crítico: malloc→pool_alloc en concat(), _syn_sha256(), _syn_sha256_archivo(), _syn_home() |
| `9fd745e` | ME_29_T5u: instalar_modelo + ConfigInfo + escribir_config + _syn_escribir_archivo | 4 tests nuevos GREEN, installer_opensyn GREEN, 33/36 GREEN total |
| `6063e39` | docs: R137 bitácora + auditoría para H-F29-T5b | Documentación |
| `2fee5b0` | FASE 29: ME_29_T6b fix test_installer_opensyn — usa main.py (Manual 8 §1.2) | 1 test pre-existente FAIL → GREEN |
| `27bd3bb` | FASE 29: ME_29_T3 benchmark latencia + infraestructura OpenSyn | 7 archivos nuevos/modificados, test_latencia_meta modificado (autorización Arquitecto) |

### Deudas / Hallazgos críticos activos
- **H-F29-T5b (RESUELTO):** bug RAII preexistente en `runtime/core/sistema.c:24 concat()` con CadenaSegura retornada por FFI — usaba `malloc()` pero liberada con `pool_free()`. Fix commit `478f047`: cambiado a `pool_alloc()`. Mismo bug corregido en `_syn_sha256()`/`_syn_sha256_archivo()` (axon.c:37,63) y `_syn_home()` (modelo.c:781 — usaba `strdup()` que internamente llama `malloc`).
- **test_binding_typescript:** GREEN (ME_29_T2 completado) — bindings TypeScript implementados en opensyn/bindings_generator.py.
- **test_gestion_modelos:** GREEN (ME_29_T3_mod completado) — test modificado para verificar funcionalidad implementada en installer.syn.
- **test_latencia_meta:** RED esperado — requiere llama-server activo en :8088 (benchmark real).

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
