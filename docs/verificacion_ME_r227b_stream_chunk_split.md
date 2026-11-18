# Verificacion ME r227b_stream_chunk_split

## Causa raiz

`_syn_ollama_stream_leer` solo volvia a leer la red si `rbpos >= rblen`. El
decodificador chunked puede quedar en fase 3/4 con 1 byte pendiente (por ejemplo
el `\r` de un CRLF partido entre dos paquetes TCP): no avanza, pero `rbpos <
rblen`, asi que el bucle giraba en CPU sin leer mas datos. El mock de R227
enviaba las tramas completas y no expuso el fallo.

## Marcas por requisito

- Manual 7 §2.2 R1 "Soporta timeouts, reintentos y manejo de errores": CUMPLE.
  `_oll_dechunk` no reentra en fase 5; `_syn_ollama_stream_leer` lee mas red
  ante una trama partida. Evidencia `runtime/core/ollama.c:1435`.
- Manual 7 §2.2 R2 "Esperar la respuesta (con timeout)": CUMPLE. El oraculo
  parte el CRLF y exige terminar dentro del timeout con el contenido completo.

## Oraculo

`tests/auditoria/test_oraculos_r227b_stream_chunk_split.py` (NUEVO)

- Servidor chunked en proceso que envia `payload + \r`, espera, y luego `\n`.
- El probe debe devolver `STREAM:hola mundo`; si el runtime gira, el test falla
  por `TimeoutExpired` en 20 s.

## Evidencia ejecutada

- Oraculo R227b: **1 passed**.
- Regresion R227 + R235 + R227b: **6 passed**.
- Smoke real con `llama-server` build 10819 y el GGUF
  `deepseek-coder-1.3b-Q4_K_M.gguf` (SHA-256 correcto):
  `CONSULTA` y `STREAM` devolvieron contenido; probe completo en **7036 ms**.
  Servidor detenido al finalizar; puerto 8088 libre.
- `contrastar.py --plan docs/plan_ME_r227b_stream_chunk_split.md`: PASS con
  indice temporal aislado (no se mezclo el trabajo staged de R255).
- `alineacion.py --verificar --me r227b_stream_chunk_split`: OK,
  evidencia `8d697386e8e7dfef`.
- `verificar_alineacion.py`: **SIN BRECHAS**.

## Limites

- El oraculo de regresion es unitario y determinista; no levanta
  `llama-server`, por diseno. El smoke real se ejecuto una vez con el modelo
  local y quedo documentado arriba.
- No se modificaron tests existentes; solo se agrego el oraculo R227b.
