# Plan ME-1: std/os.syn — Wrapper FFI sobre detección de hardware

**Fecha:** 2026-08-30
**Fase:** 27 — Herramientas de Desarrollo (LSP, VS Code, Debugger)
**ME:** ME-1 — std/os.syn (M9 §5.7 / F29)
**Estado:** 🔄 EN PROGRESO

---

## CONTEXTO

`std/os.syn` no existe (ANEXO §6 lo confirma como pendiente). El runtime no tiene
`detect_hardware.c`. Se necesita crear tanto el módulo C como el wrapper Synapse.

Funciones objetivo (M9 §5.7):
- `memoria_total()` → entero (bytes RAM total)
- `memoria_libre()` → entero (bytes RAM disponible)
- `vram_total()` → entero (bytes VRAM, 0 si no disponible)
- `cpu_nucleos()` → entero (número de cores lógicos)
- `arquitectura()` → texto (nombre de la arquitectura CPU)

---

## MTS BLOQUE ESTRICTO

### Requisito 1: detect_hardware.c implementa funciones C

```markdown
requisito: Manual 9 §5.7
texto: "módulos std deben exponer funciones C via externo para wrappers Synapse"
implementacion: runtime/core/detect_hardware.c con GlobalMemoryStatusEx/GetSystemInfo (Windows)
  y sysconf/sysinfo (Linux). Retorna valores reales del sistema.
oraculo: tests/unit/test_os_syn.py (asserts de valores reales > 0)
```

### Requisito 2: std/os.syn wrappers Synapse

```markdown
requisito: Manual 9 §5.7
texto: "std.os provee memoria_total, memoria_libre, vram_total, cpu_nucleos, arquitectura"
implementacion: externo declarations + funciones wrapper con contratos
oraculo: tests/unit/test_os_syn.py
```

### Requisito 3: Integración al build

```markdown
requisito: Manual 9 §1.1
texto: "std modules deben compilar y linkear en el pipeline principal"
implementacion: detect_hardware.c compilado y linkeado en lsp_test.exe y pipeline
oraculo: build exitoso + test ejecuta sin crash
```

---

## IMPLEMENTACIÓN

### Paso 1: Crear runtime/core/detect_hardware.h

Declaraciones de las 5 funciones C.

### Paso 2: Crear runtime/core/detect_hardware.c

Implementación multiplataforma:
- **Windows:** `GlobalMemoryStatusEx` (RAM), `GetSystemInfo` (CPU), VRAM via DXGI (fallback 0)
- **Linux:** `sysconf(_SC_PHYS_PAGES)` (RAM), `sysconf(_SC_NPROCESSORS_ONLN)` (CPU)

### Paso 3: Crear std/os.syn

Wrapper Synapse con `externo` declarations + funciones públicas con contratos.

### Paso 4: Crear tests/unit/test_os_syn.py

Tests con asserts de valores reales (no mocks):
- `memoria_total() > 0`
- `memoria_libre() > 0 && memoria_libre() <= memoria_total()`
- `cpu_nucleos() > 0`
- `arquitectura() != ""`

### Paso 5: Integrar al build

Compilar `detect_hardware.c` → `.o` → linkear.

---

## VERIFICACIÓN

1. `python -m pytest tests/unit/test_os_syn.py -v` — todos PASS
2. `python auditoria/verificar_alineacion.py` — 0 brechas
3. `python auditoria/contrastar.py --plan docs/plan_ME_1_std_os.md` — gate MTS

---

## CIERRE

**Commit:** pendiente
**Fecha cierre:** 2026-08-30
**Resultado:** 5/5 tests PASS, detect_hardware.c compila con las 5 funciones, std/os.syn con contratos
**Estado:** ✅ CERRADO
