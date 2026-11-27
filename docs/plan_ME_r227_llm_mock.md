# Plan ME r227 - LLM real con mock HTTP y fallback /completion

FASE: R227 (continuidad R221 / deuda H-R221-1)
ID: r227_llm_mock

## Contexto

El chat E2E de OpenSyn no puede declararse cerrado porque `_syn_ollama_consultar`
usa `/v1/chat/completions` y el `llama-server` local aplica una plantilla ChatML
que no corresponde al GGUF DeepSeek-Coder instalado. El modelo responde con
`<|im_end|>` inmediato y el contenido queda vacío. El GGUF local es el instruct
correcto (SHA-256 y tamaño coinciden con `opensyn/modelos.toml`).

Para no depender de un `llama-server` de larga vida en la suite, el oráculo usa
un servidor HTTP mock en proceso y verifica el contrato HTTP real del runtime.

## Requisitos (MTS)

requisito: Manual 7 §2.2
texto: "Enviar un POST a `http://127.0.0.1:8088/completion` con el JSON."
implementacion: `runtime/core/ollama.c` agrega `_openai_completar()` como
fallback cuando `/v1/chat/completions` devuelve contenido vacío, y usa
`/completion` para streaming con `prompt`, `n_predict`, `temperature` y `stop`.
implementacion: el prompt se normaliza al formato instruct DeepSeek
(`### Instruction:` / `### Response:`), separando el bloque `[USUARIO]`.
oraculo: tests/auditoria/test_oraculos_r227_llm_mock.py

requisito: Manual 7 §2.2
texto: "Extraer el campo `content` o `completion` de la respuesta JSON."
implementacion: `_openai_completar()` extrae `content`; si no existe, prueba
`completion`; si tampoco, propaga el campo `error`.
oraculo: tests/auditoria/test_oraculos_r227_llm_mock.py

## Archivos

- `runtime/core/ollama.c` - fallback `/completion` y streaming compatible.
- `tests/auditoria/test_oraculos_r227_llm_mock.py` - oráculo con mock HTTP.
- `docs/alineacion/r227_llm_mock.md` - expediente de alineación.
- `docs/verificacion_ME_r227_llm_mock.md` - verificación del ME.

## Verificación

- `python -m pytest tests/auditoria/test_oraculos_r227_llm_mock.py -v`
- `python main.py tests/e2e/e2e_hola.syn -o <tmp>.exe` (regresión de compilación)
- `python auditoria/verificar_alineacion.py`
- `python auditoria/contrastar.py --plan docs/plan_ME_r227_llm_mock.md`
