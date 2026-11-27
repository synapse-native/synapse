# Plan ME — ME_opensyn_ia: motor de inferencia GGUF local (hardening rendimiento + límites)

FASE: 30-b / R141 (hardening F30; visión Manual 7 §3)
ID: ME_opensyn_ia_gguf
ESTADO: completado (oráculo GREEN, verificación en docs/verificacion_ME_opensyn_ia_gguf.md)

## Contexto

Trabajo hallado en el working tree (sesión anterior) sin plan propio: mejoras de
rendimiento y límites en el cargador GGUF / motor de inferencia local
(`runtime/core/modelo.c`, `runtime/core/modelo.h`) que OpenSyn usa como
respaldo cuando no hay Ollama (`modo_oraculo` → `_syn_modelo_cargar`). Este
plan formaliza ese trabajo bajo MTS.

## Requisitos del manual (MTS — bloque estricto)

### Requisito R1 — Cargador GGUF para modelos locales cuantizados

requisito: Manual 7 §3.1 — OpenSyn soporta modelos en formato GGUF (cuantizados)
texto: OpenSyn soporta modelos en formato GGUF (cuantizados) de las siguientes
  familias: DeepSeek Coder 1.3B Q4_K_M, CodeLlama 7B/13B/34B Q4_K_M, etc.
implementacion:
  - `runtime/core/modelo.c` `_syn_modelo_cargar`: vocabulario desde el array
    GGUF real `tokenizer.ggml.tokens` (formato llama.cpp/Qwen) con respaldo al
    escalar legacy `vocab_size` (antes solo leía el escalar → 0 con GGUFs
    reales → rechazo del modelo).
  - Cache de posición por array de metadatos (`ArrayMetaEntry.cache_indice` /
    `cache_pos`): el acceso secuencial al vocab pasa de O(n²) a O(n) total
    (antes cada acceso re-caminaba desde `data_pos`).
  - Lecturas de arreglos y de-cuantización verifican límites contra
    `tamano_mmap` antes de acceder (archivos truncados/corruptos → error
    controlado, sin lectura fuera de rango).
oraculo: tests/e2e_oracle_opensyn_ia_gguf.py

### Requisito R2 — Cuantización: inferencia sobre tensores cuantizados acelerada

requisito: Manual 7 §3.3 — OpenSyn utiliza cuantización para reducir el tamaño
  de los modelos y acelerar la inferencia
texto: OpenSyn utiliza cuantización para reducir el tamaño de los modelos y
  acelerar la inferencia.
implementacion:
  - `_gguf_decuantizar_f32` (exacta, bloque ggml de 32): F16, Q4_0, Q4_1,
    Q5_0, Q5_1 y Q8_0 → F32; materialización PEREZOSA con cache en
    `TensorInfo.cache_f32` (se des-cuantiza una sola vez por tensor; se libera
    al cerrar el contexto; `es_mapeado=1` conserva el contrato mmap del motor).
  - Orden de dimensiones GGUF/llama.cpp corregido: `ne[0]` = contigua
    (columnas), la externa al final (filas) — antes se leían invertidas y
    `w_k` daba columnas=128 (kv_heads*head_dim) en vez de n_embd → matmul OOB.
  - `_filtro_top_p`: ordenamiento O(vs²) → qsort O(vs log vs) (antes ~30 s por
    token con vocab 151k).
oraculo: tests/e2e_oracle_opensyn_ia_gguf.py

## Archivos que modifica

- runtime/core/modelo.c, runtime/core/modelo.h (cargas arriba; citas Manual 7 §3.1/§3.3)
- tests/e2e_oracle_opensyn_ia_gguf.py (oráculo: construye GGUF sintético Q8_0,
  compila driver .syn y verifica carga/ingesta/generación determinista)
- tests/fixtures/e2e_opensyn_ia/driver_gguf_test.syn (driver de verificación)
- docs/plan_ME_opensyn_ia_gguf.md, docs/verificacion_ME_opensyn_ia_gguf.md

## Verificación

- `.venv/Scripts/python.exe tests/e2e_oracle_opensyn_ia_gguf.py` → GREEN (rc=0).
- `python main.py opensyn/principal.syn` sigue compilando (exe nuevo).
- `python auditoria/verificar_alineacion.py` → 0 brechas.
- `python auditoria/contrastar.py --plan docs/plan_ME_opensyn_ia_gguf.md` → sin brechas.
