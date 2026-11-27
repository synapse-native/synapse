# Plan ME r235 - Fallback cuando el contenido es solo blanco o marcadores

FASE: R235 (deuda H-R221-1-R1, continuidad R227)
ID: r235_fallback_blanco

## Contexto

El smoke real de R227 (`docs/reportes/R227_smoke_real.md`) demostró que
`_syn_ollama_consultar` decide el fallback con `resultado.longitud > 0`. Si
`/v1/chat/completions` responde `content: "\n\n"` (plantilla de chat incompatible
que cierra de inmediato) o solo marcadores de plantilla (`<|im_end|>`), el
runtime lo acepta como respuesta válida, **no** reintenta `POST /completion` y
el usuario final ve "[Error] No hubo respuesta del servidor IA local" cuando el
servidor sí podía responder por el endpoint instruct.

## Requisitos (MTS)

requisito: Manual 7 §2.2
texto: "Extraer el campo `content` o `completion` de la respuesta JSON."
implementacion: `runtime/core/ollama.c` agrega `_oll_contenido_util()` y
`_syn_ollama_consultar()` solo acepta el resultado de `/v1/chat/completions`
cuando contiene texto útil (no solo espacios, saltos o marcadores de
plantilla); en caso contrario reintenta `POST /completion`.
oraculo: tests/auditoria/test_oraculos_r235_fallback_blanco.py

requisito: Manual 7 §2.2
texto: "Retornar la respuesta como string."
implementacion: el resultado de `/completion` y del fallback `/api/chat` pasa
por la misma validación: si solo trae blancos/marcadores se devuelve cadena
vacía en lugar de una respuesta fantasma, de modo que el llamador .syn distinga
"sin respuesta" de "respuesta" (Manual 2 §12: contrato requiere/garantiza).
oraculo: tests/auditoria/test_oraculos_r235_fallback_blanco.py

## Archivos

- `runtime/core/ollama.c` — validación de contenido útil antes del fallback.
- `tests/auditoria/test_oraculos_r235_fallback_blanco.py` — oráculo con mock HTTP
  que devuelve `"\n\n"` y `<|im_end|>` en chat y contenido real en `/completion`.
- `docs/alineacion/r235_fallback_blanco.md` — expediente de alineación.
- `docs/verificacion_ME_r235_fallback_blanco.md` — verificación del ME.
- `docs/reportes/R235.md` — reporte del micro-entregable.

## Verificación

- `.venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r235_fallback_blanco.py -v`
- `.venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r227_llm_mock.py -v` (regresión)
- `.venv/Scripts/python.exe auditoria/verificar_alineacion.py`
- `.venv/Scripts/python.exe auditoria/alineacion.py --verificar --me r235_fallback_blanco`
- `.venv/Scripts/python.exe auditoria/contrastar.py --plan docs/plan_ME_r235_fallback_blanco.md`
- Smoke real: `llama-server` + GGUF instruct con `--chat-template-file` vacío,
  probe `.syn` y chat de `dist/bin/opensyn.exe` (nivel usuario final).
