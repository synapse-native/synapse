# Plan ME r227b - Streaming chunked sin bucle ante tramas partidas

FASE: R227b (hotfix del smoke real de R227)
ID: r227b_stream_chunk_split

## Contexto

El smoke real con `llama-server` reprodujo un cuelgue intermitente del chat
streaming. La causa esta en `_syn_ollama_stream_leer`: si un CRLF de chunk, una
linea de tamano o un trailer queda partido entre dos lecturas TCP, el
decodificador no avanza pero deja bytes en `rb`; el bucle no vuelve a leer la
red y gira en CPU indefinidamente. El mock de R227 enviaba cada trama completa y
no expuso el fallo.

## Requisitos (MTS)

requisito: Manual 7 §2.2
texto: "Soporta timeouts, reintentos y manejo de errores."
implementacion: `_oll_dechunk` termina en fase 5 sin reentrar; si no hay linea
completa y quedan bytes parciales en `rb`, `_syn_ollama_stream_leer` lee mas
red en lugar de girar sobre el mismo buffer.
oraculo: tests/auditoria/test_oraculos_r227b_stream_chunk_split.py

requisito: Manual 7 §2.2
texto: "Esperar la respuesta (con timeout)."
implementacion: el test parte el CRLF de un chunk entre dos envios y exige que
el probe termine dentro del timeout, con el contenido completo.
oraculo: tests/auditoria/test_oraculos_r227b_stream_chunk_split.py

## Archivos

- `runtime/core/ollama.c` - corte del bucle activo en fase 3/4 y lectura de red
  ante tramas incompletas.
- `tests/auditoria/test_oraculos_r227b_stream_chunk_split.py` - oraculo NUEVO
  con servidor chunked en proceso que parte el CRLF.
- `docs/alineacion/r227b_stream_chunk_split.md` - expediente de alineacion.
- `docs/verificacion_ME_r227b_stream_chunk_split.md` - verificacion del ME.

## Verificacion

- `.venv\Scripts\python.exe -m pytest tests/auditoria/test_oraculos_r227b_stream_chunk_split.py -v`
- `.venv\Scripts\python.exe -m pytest tests/auditoria/test_oraculos_r227_llm_mock.py tests/auditoria/test_oraculos_r235_fallback_blanco.py -v`
- `.venv\Scripts\python.exe auditoria\verificar_alineacion.py`
- `.venv\Scripts\python.exe auditoria\contrastar.py --plan docs/plan_ME_r227b_stream_chunk_split.md`
- `.venv\Scripts\python.exe auditoria\alineacion.py --verificar --me r227b_stream_chunk_split`
