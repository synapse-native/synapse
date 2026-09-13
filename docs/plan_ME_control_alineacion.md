# Plan ME:control_alineacion — control de alineación verificable

> **Fecha:** 2026-09-13
> **Manual referenciado:** Manual 2 §12 (pruebas obligatorias), Manual 8 §1.2
> (fail-loud del protocolo), Manual 7 §4.2 (validación como paso crítico)
> **Objetivo:** que el agente lea la sección del manual ANTES de codificar y
> después compare su trabajo contra lo que el manual dice, corrigiendo lo que
> no cumpla. Deja de verificar un "registro" y pasa a verificar el cambio.
> **Documentación:** `docs/gobernancia/CONTROL_ALINEACION.md`

---

## 1. Oráculos ejecutados (no declarados)

requisito: Manual 2 §12
texto: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
implementacion: `auditoria/alineacion.py:ejecutar_oraculo` ejecuta el oráculo declarado en el expediente (pytest o script) en modo release y NO acepta como evidencia `SKIP`, "no tests ran", `xfail` ni rc≠0 (`alineacion.py:355-357`).
oraculo: tests/test_alineacion_control.py

## 2. El gate no degrada en silencio (fail-loud)

requisito: Manual 8 §1.2
texto: "Si el LSP no puede leer una cabecera válida (ej. `Content-Length` ausente), emite un error y termina."
implementacion: expediente ausente = brecha (`alineacion.py:406`); cita que no aparece literalmente en la sección vigente = brecha (`indice_manual.py:234`); 0 anclas parseadas y ancla `PENDIENTE` = brecha (no hay "omitir paso").
oraculo: tests/test_alineacion_control.py

## 3. La comparación es contra el manual VIGENTE

requisito: Manual 7 §4.2
texto: "**Validación (paso crítico):** El LSP toma el código generado y ejecuta el compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario"
implementacion: `auditoria/alineacion.py:verificar` contrasta cada ancla contra `docs/manuales/.indice.json` (sha256 del manual vigente) y contra el código real (`evidencia` a ±3 líneas); si el cambio toca los manuales, revalida todas las citas vivas del repo y exige declarar las que quedaron sin sección.
oraculo: tests/test_alineacion_control.py

---

## Cambios del ME

| Archivo | Cambio |
|---|---|
| `auditoria/indice_manual.py` | índice de manuales: secciones + oraciones citables con id estable |
| `auditoria/alineacion.py` | motor: `--leer/--explain/--nuevo/--verificar/--baseline/--indice` |
| `docs/gobernancia/mapa_alineacion.md` | requisito puntual por archivo de producción (nuevo) |
| `docs/gobernancia/CONTROL_ALINEACION.md` | diseño y activación (nuevo) |
| `tests/test_alineacion_control.py` | 22 tests del motor (nuevo) |
| `scripts/githooks/pre-commit` | gate de alineación (warn por defecto, `ALINEACION_MODO=block`) |
| `.github/workflows/ci-tests.yml` | job `alineacion` (`--desde <base> --ci`) |
| `AGENTS.md` | lectura dirigida obligatoria (`--leer`) + verificación `--verificar` |

## Activación y estado

1. `warn` (actual): el hook informa y no bloquea; el baseline
   `docs/alineacion/DEUDA.md` congela la deuda heredada (71 citas muertas).
2. `block` local: `ALINEACION_MODO=block` (con `ALINEACION_ORACULOS=1` si se
   quieren correr los oráculos dentro del hook).
3. `block` en CI: variable de repositorio `ALINEACION_MODO=block`.

## Deuda detectada por el gate (no de este ME)

- `docs/manuales/MANUAL 7.md` perdió las secciones §5 a §9 sin que nadie
  revalidara las citas: 71 citas `cumple Manual` del repo quedaron apuntando a
  secciones inexistentes. En los 6 archivos del commit ME-7 (`2f62084`) hay 53
  de ellas (9 `permisos.syn`, 8 `planificador.syn`, 12 `principal.syn`,
  6 `router.syn`, 11 `run_manager.syn`, 7 `validation_loop.syn`).
- El commit `2f62084` (ME-7) no trae expediente ni evidencia: el gate lo reporta
  como "falta el expediente de alineación" (cambio_hash=1a4b130148cb7d5e).
- `docs/alineacion/ME-7.md` queda como expediente a completar (estado PENDIENTE).
