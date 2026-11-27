# Verificación ME r227_llm_mock

## Marcas por requisito

- Manual 7 §2.2 R1 el cliente envía `POST /completion` con prompt instruct y extrae `content`/`completion`: CUMPLE. Evidencia `runtime/core/ollama.c:630` y `runtime/core/ollama.c:669`; oráculo `tests/auditoria/test_oraculos_r227_llm_mock.py`.

- Manual 7 §2.2 R2 el streaming usa `/completion`, acumula chunks `content` y cierra con `stop:true`: CUMPLE. Evidencia `runtime/core/ollama.c:1233`; oráculo `tests/auditoria/test_oraculos_r227_llm_mock.py`.

## Oráculo

`tests/auditoria/test_oraculos_r227_llm_mock.py`

- R1: `/v1/chat/completions` devuelve content vacío (plantilla ChatML
  incompatible) y el runtime reintenta `POST /completion`; extrae `content`.
- R2: el streaming usa `/completion`, acumula los chunks `content` y cierra con
  `stop:true`; el prompt enviado contiene `### Instruction:`.

## Evidencia

- `2 passed` en el oráculo R227 con mock HTTP en proceso.
- `26 passed, 1 skipped` en la regresión dirigida
  `test_oraculos_r151.py`, `test_inference.py` y `test_llm_bridge.py`.
- Compilación y ejecución de `tests/e2e/e2e_hola.syn`: `Hola Mundo`.
- `verificar_alineacion.py`: 0 brechas.
- `contrastar.py --plan docs/plan_ME_r227_llm_mock.md`: sin brechas.

## Límites

- No se levantó `llama-server` real: el mock reproduce el contrato HTTP y el
  fallo de plantilla. La prueba real con el GGUF DeepSeek queda como smoke
  manual posterior, no como dependencia de la suite.
- `tests/auditoria/test_oraculos_eof_runtime.py` mantiene RED preexistentes por
  `_resultado_` vs `resultado` (R228) y por ausencia de `modelo_synapse.gguf`
  en el entorno (R227 smoke real).
