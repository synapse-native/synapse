# Plan ME r242 — `synapse opensyn` en el binario nativo

## Contexto

El CLI Python (`cli.py`) expone `synapse opensyn <subcomando>` desde R149
(`status` real, `download`/`finetune` con error honesto si no hay servidor,
`bindings` regenerando `lib/runtime_bindings.syq`, `transpile` vía
`opensyn.transpiler`). El binario nativo que se distribuye en `{app}\bin` no
tiene ese despacho: `nucleo/principal.syn` sólo reconoce `axon`, `lint`, `fmt`,
`test`, `check` y `update`, así que `dist/bin/synapse.exe opensyn status` trata
`opensyn` como **archivo fuente** y falla con «Compilando archivo: opensyn …
Error de compilacion» (criterio de cierre 6 del PLAN MAESTRO INDUSTRIAL).
El usuario final que instala con el setup de R237 no tiene Python: el
subcomando tiene que existir en el ejecutable, no sólo en `cli.py`.

## Requisitos

requisito: Manual 8 §4.1 — el CLI unificado despacha los comandos del ecosistema
texto: "| `synapse opensyn <subcomando>` | Comandos de OpenSyn (status, download, finetune, bindings, transpile). |"
implementacion: `nucleo/principal.syn` gana una rama `opensyn` en `principal()` antes de la pipeline de compilación, con el mismo orden de despacho que el resto de subcomandos nativos (`cmd` = `argv(1)`): `opensyn` sin subcomando y `opensyn --help`/`-h` imprimen la lista de los cinco subcomandos y devuelven 0; `status`/`doctor` delegan en el binario OpenSyn nativo `opensyn.exe` instalado junto a `synapse.exe` (`{app}\bin` en el instalador, `dist/bin` en el checkout), que ya implementa las comprobaciones locales de Manual 7 §2.1 — no se duplica ni se inventa el diagnóstico; `download`/`finetune`/`bindings`/`transpile` responden con el error honesto correspondiente (requieren servicio de inferencia local o el toolchain Python de `opensyn/`), igual que el CLI Python para `download`/`finetune`; cualquier otro valor sale con 1 y «Subcomando OpenSyn desconocido».
oraculo: tests/auditoria/test_oraculos_r242_opensyn_nativo.py

requisito: Manual 8 §4.2 — el binario nativo no interpreta subcomandos como archivos
texto: "| `--target` | `native`, `wasm`, `llvm` (por defecto `native`). |"
implementacion: la rama `opensyn` se evalúa en el dispatcher de subcomandos de `principal()` (junto a `lint`/`fmt`/`test`/`check`/`update`), de modo que `argv(1) == "opensyn"` nunca llega al prescan de flags ni a la pipeline `generar_etapa()`: el binario deja de intentar compilar el literal `opensyn` y devuelve un código de salida definido (0 para ayuda/estado correcto, 1 para subcomando desconocido o capacidad ausente).
oraculo: tests/auditoria/test_oraculos_r242_opensyn_nativo.py

## Cambios

1. `nucleo/principal.syn`: nueva rama de despacho `opensyn` en `principal()`
   (bloque `inseguro` con C embebido, mismo patrón que `axon`/`update`), con
   ayuda, delegación a `opensyn.exe` para `status`/`doctor` resolviendo la ruta
   desde `argv(0)`, y errores honestos para el resto.
2. `nucleo/principal.syn`: `--help` global y el uso sin argumentos listan también
   `opensyn <subcomando>` (Manual 8 §4.1: el CLI unificado es el punto de
   entrada de todas las herramientas).
3. `tests/auditoria/test_oraculos_r242_opensyn_nativo.py` (nuevo): oráculo E2E
   contra `dist/bin/synapse.exe` — `opensyn --help`/sin argumentos (rc=0 y lista
   de subcomandos), `opensyn status` (rc=0 y estado real de OpenSyn delegado, sin
   «Error de compilacion» ni «Compilando archivo: opensyn»), `opensyn doctor`
   (rc=0), subcomando desconocido (rc=1) y paridad con `cli.py` en la lista de
   subcomandos.
4. Rebuild de `dist/bin/synapse.exe` con `main.py nucleo/principal.syn` (el
   artefacto no se commitea: el oráculo lo exige fresco, OBL-EXE-R2).

## Límites

- `bindings` y `transpile` no se reimplementan en C: dependen del generador
  Python (`opensyn/generate_runtime_bindings.py`) y de `opensyn/transpiler.py`.
  El binario devuelve 1 con un mensaje que apunta al CLI Python, en lugar de
  fingir éxito.
- `status`/`doctor` delegan en `opensyn.exe` en vez de duplicar las
  comprobaciones: una sola fuente de verdad para el diagnóstico local
  (Manual 7 §2.1) y sin divergencia entre los dos binarios del mismo producto.
- Sin red: el oráculo no requiere servidor de inferencia ni modelo descargado;
  sólo comprueba códigos de salida y contenido estable.
