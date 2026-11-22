// Documento informativo; la ley es docs/manuales/
# R227 — Smoke REAL de chat OpenSyn con llama-server y el GGUF instruct

**Fecha:** 2026-11-17 | **ME:** r227_llm_mock (commit `24a7feb`) | **Manual:** 7 §2.2
**Objetivo del run:** ejecutar el smoke real pendiente de H-R221-1 — el fallback
`POST /completion` y el chat de OpenSyn contra `llama-server` real con el GGUF
instruct, para decidir si el hallazgo puede cerrarse.
**Veredicto:** H-R221-1 **NO se cierra** — el smoke destapa un defecto residual
(`H-R221-1-R1`) y refuta la hipótesis del "GGUF base".

## Entorno real usado

- `dist/opensyn/ia/llama-server.exe` b10819 (2026-09-05), `-c 2048 -t 2 -ngl 0`.
- Modelo: `C:/Users/marce/.opensyn/models/deepseek-coder-1.3b-Q4_K_M.gguf`
  (873 MB). Metadatos: `general.name = deepseek-ai_deepseek-coder-1.3b-instruct`
  → **es el variante instruct** (repo "Chat-GGUF" de Manual 9 §7).
- Probe `build/smoke_r227/probe_r227_real.syn`: compilado con el pipeline real
  (`main.py -o`), llama `_syn_ollama_consultar` y el streaming con el mismo
  prompt que `opensyn/principal.syn::consultar_agente` (incluye `[USUARIO]`).
- Observación de endpoints: proxy TCP transparente en :8098 → :8088 que solo
  registra la línea de petición y reenvía los bytes intactos (el servidor y el
  modelo siguen siendo los reales; no hay mock de respuestas).

## Resultados

### A) Plantilla nativa del GGUF (configuración distribuida)

- `/v1/chat/completions` devuelve contenido (puede incluir marcadores de
  plantilla si la generación llega a `max_tokens`).
- Probe: `CONSULTA:Hola, ¿cómo estás? ¿Qué puedo hacer para ayudarte?`
- Probe: `STREAM:Hola!` · `ESTADO:0` · `ERROR:` (vacío)
- Proxy: `POST /v1/chat/completions` (consulta) y `POST /completion` con
  `prompt_instruct=True` (streaming) → **el path de R227 se ejerce en real**.
- Binario de usuario regenerado
  (`python main.py opensyn/principal.syn -o dist/bin/opensyn.exe`, rc=0,
  06:51, 2× `### Instruction:`): el chat conecta, lista modelos y responde.
  Antes del smoke, `dist/bin/opensyn.exe` era del 2026-11-15 (STALE, sin R227).

### B) Reproducción del defecto original (plantilla que cierra de inmediato)

Servidor real con `--chat-template-file build/smoke_r227/chatml_vacio.jinja`:

- `/v1/chat/completions` → `{"message":{"content":"\n\n"},"finish_reason":"stop"}`
- Probe: `CONSULTA:` seguido de dos saltos de línea (sin reintento).
- Proxy: solo `POST /v1/chat/completions` para la consulta — **no** hubo
  `POST /completion`.
- Chat real: `OpenSyn> [Error] No hubo respuesta del servidor IA local.`

## Hallazgo H-R221-1-R1 (NUEVO, ALTO)

`runtime/core/ollama.c::_syn_ollama_consultar` decide el fallback con
`resultado.longitud > 0`. Un `content` que solo trae blancos (`"\n\n"`) o
marcadores de plantilla cuenta como éxito, así que el reintento con
`/completion` **no se ejecuta** y el usuario ve una respuesta vacía.

Fix propuesto (no implementado en este run — `runtime/core/ollama.c` intacto):
recortar blancos y descartar `content` compuesto solo por `<|im_end|>` /
`<|im_start|>` antes de aceptar la respuesta; oráculo nuevo con servidor HTTP
que devuelva `"\n\n"`. Resolución asignada: **ME r235_fallback_blanco**.

## Límites

- Los logs del servidor quedan en `logs/` (gitignored): `smoke_r227_llama_*.log`
  y `smoke_r227_llama_server_verbose.log`; el probe y el proxy viven en
  `build/smoke_r227/` (gitignored).
- No se modificó código de producción ni tests: no aplica `contrastar` ni el
  gate de lectura. `verificar_alineacion.py` se ejecutó al inicio de la sesión
  (SIN BRECHAS) y las únicas modificaciones de este run son documentales.
- `opensyn/principal.syn.json` regenerado por el build fue revertido para no
  dejar ruido en el árbol.

--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: smoke real de R227 (H-R221-1) con llama-server y GGUF instruct
FASE: POST-FASE 33 (deuda R221/R227)
MANUAL REFERENCIADO: Manual 7 §2.2 (y §7.3 para inferencia 100% local)
HASH COMMIT: sin commit (verificación; sin cambios de producción)
COMPILACION: probe real rc=0; dist/bin/opensyn.exe regenerado rc=0 (06:51)
TESTS: smoke real 3 escenarios (nativo, defecto reproducido, chat de usuario)
COBERTURA: N/A
MODIFICACIONES DE TESTS: ninguna
MODULARIZACION: ninguna (probe/proxy temporales en build/, gitignored)
RIESGOS IDENTIFICADOS: H-R221-1-R1 — fallback no dispara con contenido en blanco
PROXIMO PASO: ME r235_fallback_blanco y luego re-ejecutar este smoke
--- FIN ---
