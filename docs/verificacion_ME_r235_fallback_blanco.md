# Verificación ME r235_fallback_blanco

## Marcas por requisito

- Manual 7 §2.2 R1 el runtime sólo acepta como respuesta un `content`/`completion` con texto útil: si `/v1/chat/completions` devuelve `"\n\n"` (o sólo `<|im_end|>`) se reintenta `POST /completion`: CUMPLE. Evidencia `runtime/core/ollama.c:869` y `runtime/core/ollama.c:738`; oráculo `tests/auditoria/test_oraculos_r235_fallback_blanco.py`.

- Manual 7 §2.2 R2 la respuesta se retorna como string y, si tampoco el fallback trae texto útil, se devuelve cadena vacía (sin respuesta fantasma): CUMPLE. Evidencia `runtime/core/ollama.c:969`; oráculo `tests/auditoria/test_oraculos_r235_fallback_blanco.py`.

## Oráculo

`tests/auditoria/test_oraculos_r235_fallback_blanco.py` (mock HTTP en proceso,
probe compilado con el pipeline real):

- R1: chat responde `content: "\n\n"` → el runtime llama a `/completion`, retorna
  su `content` y no usa `/api/chat`.
- R2: chat responde `content: "<|im_end|>"` → mismo comportamiento.
- R3: chat responde texto real → se retorna tal cual y **no** se hace la segunda
  petición.

## Evidencia

- `3 passed` en el oráculo R235.
- `2 passed` en la regresión del oráculo R227
  (`tests/auditoria/test_oraculos_r227_llm_mock.py`).
- `verificar_alineacion.py`: 0 brechas.
- `alineacion.py --verificar --me r235_fallback_blanco`: 1 archivo, citas
  textuales verificadas, 1 oráculo ejecutado; evidencia
  `auditoria/evidencia/8bffa132a1f1f3df.json`.
- `contrastar.py --plan docs/plan_ME_r235_fallback_blanco.md`: sin brechas.

## Smoke real (nivel usuario final)

`llama-server` b10819 real + GGUF `deepseek-coder-1.3b-Q4_K_M.gguf`, lanzado con
`--chat-template-file build/smoke_r227/chatml_vacio.jinja` (la plantilla que
reproducía el defecto: el chat de llama-server cierra de inmediato y
`/v1/chat/completions` devuelve `content: "\n\n"`).

- Probe real (`build/smoke_r235/probe_r235.exe`, compilado con `main.py`):
  `CONSULTA:Hola!` (antes del fix: `CONSULTA:` + dos saltos de línea),
  `STREAM:Hola!`, `ESTADO:0`, `ERROR:` vacío, RC=0.
- Proxy TCP de observación (`build/smoke_r235/proxy_r235.py`, 8098→8088):
  `POST /v1/chat/completions` seguido de `POST /completion` con
  `prompt_instruct=True` → el fallback se dispara de verdad contra el servidor
  real, sin mock.
- Binario de usuario final regenerado
  (`python main.py opensyn/principal.syn -o dist/bin/opensyn.exe`, 07:17) y
  ejecutado contra ese mismo servidor: el chat responde contenido del modelo
  (`OpenSyn> Lo siento, pero...`) en lugar del `[Error] No hubo respuesta del
  servidor IA local` que mostraba antes del fix.

## Límites

- El modelo de 1.3B con plantilla vacía responde con texto pobre (calidad del
  modelo, no del cliente); lo verificado es que la respuesta llega al usuario.
- La fuga de `<|im_end|>` cuando la generación agota `max_tokens` con la
  plantilla nativa queda como observación de calidad, fuera del alcance de este
  ME (con contenido real el fallback no se dispara, R3).
- `logs/smoke_r235_llama_vacio.log`, `build/smoke_r235/*` y
  `dist/bin/opensyn.exe` son artefactos locales gitignored o no trackeados.
