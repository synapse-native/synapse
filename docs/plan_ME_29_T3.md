# Plan ME_29_T3 — Modificación test_latencia_meta

## Bloque MTS (método de trabajo seguro)

### requisito:
Manual 7 §7.2: "Latencia de inferencia: < 1s para prompts cortos (modelo 7B en GPU)."

### texto:
"Latencia de inferencia: < 1s para prompts cortos (modelo 7B en GPU)."

### implementacion:
Reemplazar `pytest.fail()` en `test_latencia_meta` (tests/opensyn/test_inference.py:92-98) por un benchmark que:
1. Envíe un prompt corto al cliente llama_client (llama_client_completion)
2. Mezcle un benchmark usando `time.perf_counter()` para medir la duración
3. Verifique que la latencia < 1.0 segundo
4. Si llama_client no está conectado (no hay llama-server corriendo), usar un mock o skip con mensaje de que el benchmark requiere inferencia real

### oraculo:
- `latencia < 1.0` → PASS (Manual 7 §7.2)
- Si no puede conectar al servidor: FAIL con mensaje claro (no skip)
- El benchmark usa `time.perf_counter()` para precisión de alta resolución

## Archivos a modificar
- `tests/opensyn/test_inference.py` (líneas 92-98)

## Citas de manuales
- Manual 7 §7.2 (latencia < 1s)
- Manual 7 §2.2 (llama_client_completion — flujo de invocación del modelo)
