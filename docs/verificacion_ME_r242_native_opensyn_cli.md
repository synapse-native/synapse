# Verificación MTS — ME r242_native_opensyn_cli

Fecha: 2026-11-17 · Plan: `docs/plan_ME_r242_native_opensyn_cli.md` ·
Expediente: `docs/alineacion/r242_native_opensyn_cli.md` ·
Evidencia: `auditoria/evidencia/4437bc919e048bd1.json` (cambio_hash `4437bc919e048bd1`).

## Estado por requisito

| Requisito | Marca | Evidencia ejecutada |
|---|---|---|
| Manual 8 §4.1 | CUMPLE | `nucleo/principal.syn` despacha `opensyn` con los cinco subcomandos del manual: `--help`/sin subcomando los lista (rc=0), `status`/`doctor` delegan en `opensyn.exe` (rc=0 y estado real), y `download`/`finetune`/`bindings`/`transpile` fallan con mensaje explícito (rc=1). Oráculos `test_opensyn_help_lista_los_cinco_subcomandos`, `test_opensyn_status_delega_en_el_binario_nativo`, `test_opensyn_doctor_delega_en_el_binario_nativo`, `test_paridad_de_subcomandos_con_el_cli_python`. |
| Manual 8 §4.2 | CUMPLE | La rama `opensyn` se evalúa antes del prescan de flags: `synapse.exe opensyn status` ya no imprime «Compilando archivo: opensyn» ni «Error de compilacion» (antes el literal se compilaba como fuente). Oráculo `test_opensyn_status_delega_en_el_binario_nativo` y `test_opensyn_sin_binario_companero_falla_claro`. |

## Cita textual

- Manual 8 §4.1: *"| `synapse opensyn <subcomando>` | Comandos de OpenSyn (status, download, finetune, bindings, transpile). |"* — el binario nativo expone el subcomando en vez de tratarlo como archivo.
- Manual 8 §4.2: los subcomandos se despachan antes de interpretar `argv(1)` como ruta de compilación, igual que `lint`/`fmt`/`test`/`check`/`update`.

## Comportamiento entregado

| Invocación | Resultado |
|---|---|
| `synapse opensyn` / `synapse opensyn --help` | Lista los 5 subcomandos, rc=0 |
| `synapse opensyn status` | Estado real de OpenSyn (delegado en `opensyn.exe`, rc=0) |
| `synapse opensyn doctor` | Diagnóstico real de OpenSyn (delegado, rc=0/1) |
| `synapse opensyn download\|finetune` | rc=1 — requiere servidor local en `:8088` |
| `synapse opensyn bindings\|transpile` | rc=1 — requieren el toolchain Python de `opensyn/` |
| `synapse opensyn <desconocido>` | rc=1 — «Subcomando OpenSyn desconocido» + uso |
| `synapse --help` | Incluye `opensyn <sub>` en la lista de subcomandos |

## Oráculo

`tests/auditoria/test_oraculos_r242_opensyn_nativo.py` — **8 passed** (8.99 s),
usando sólo `dist/bin/synapse.exe` + `dist/bin/opensyn.exe`:

- ayuda con los cinco subcomandos (y sin subcomando),
- `status` con estado real y sin rastro de la pipeline de compilación,
- `doctor` sin error de compilación,
- subcomando desconocido rc=1,
- `--help` global menciona `opensyn`,
- paridad del juego de subcomandos con `cli.py`,
- guarda: `synapse.exe` solo (sin `opensyn.exe` al lado) → rc=1 con error claro
  (no finge éxito).

Regresión dirigida: `test_compilacion_fase32.py`, `test_opensyn_cli.py`,
`test_opensyn_doctor.py`, `test_oraculos_opensyn_exe.py` y
`test_orquesta_comandos.py` → **71 passed**.

## Límites

- `bindings` y `transpile` no se reimplementan en C: dependen de
  `opensyn/generate_runtime_bindings.py` y `opensyn/transpiler.py` (Python). El
  binario devuelve 1 con el mensaje que apunta al CLI Python.
- `status`/`doctor` delegan en `opensyn.exe` para no duplicar el diagnóstico
  local (Manual 7 §2.1); si ese binario falta junto a `synapse.exe`, el
  subcomando falla explícito en vez de inventar un estado.
- `dist/bin/synapse.exe` es un artefacto de build (no se commitea): el oráculo
  exige el binario regenerado con `main.py nucleo/principal.syn -o dist/bin/synapse.exe`.
