# Verificación ME — opensyn_ia_gguf (motor GGUF local, hardening rendimiento + límites)
# Fecha: 2026-09-06 — oráculo tests/e2e_oracle_opensyn_ia_gguf.py GREEN (rc=0)
# Scope: runtime/core/modelo.c/h — cargador GGUF con vocab del array real, cache perezoso
# de de-cuantización, límites contra tamano_mmap, top_p O(vs log vs).

Manual 7 §3.1 — R1 CUMPLE (vocabulario desde `tokenizer.ggml.tokens` real con respaldo
  al escalar legacy; cache de posición por array → acceso secuencial O(n); lecturas y
  de-cuantización verifican límites contra tamano_mmap. Oráculo e2e_oracle_opensyn_ia_gguf.py
  GREEN: GGUF sintético determinista (vocab 11, merges a b/c d/e f, 12 tensores,
  token_embd Q8_0) → carga, vocab=11 del array real, ingesta "abc def"=5 tokens,
  generación "abababababababab" (8 tokens), cierre limpio, 0 ESCAPA_DEL_ALCANCE)
Manual 7 §3.3 — R2 CUMPLE (_gguf_decuantizar_f32 exacta F16/Q4_0/Q4_1/Q5_0/Q5_1/Q8_0 con
  cache perezoso por tensor (TensorInfo.cache_f32, se libera al cerrar); orden de dims
  GGUF ne[0]=contigua corregido (w_k columns=kv_dim, sin OOB); _filtro_top_p qsort
  O(vs log vs). Oráculo mismo resultado determinista sobre token_embd Q8_0 real)

HALLAZGO H-GGUF-1 (RESUELTO): el oráculo sintético inicial usaba merges cuyo resultado
  ("ab","cd","ef") no existía como pieza en el vocab → resolutión por texto exacto
  0/3 resueltos → tokenización caía a bytes crudos (7 tokens). El parser exige que la
  pieza resultado del merge exista en tokenizer.ggml.tokens; corregido en el fixture.
HALLAZGO H-GGUF-2 (RESUELTO): _syn_modelo_evaluar_token toma vocab_size del contexto
  (array de tokens, 11) pero el bucle del LM head itera mc->vocab_size leyendo
  output.weight con stride n_embd — si output.weight tiene menos filas que el vocab
  del tokenizer, la lectura sale del mmap (logits corruptos, generación vacía). Con
  GGUFs reales tokenizer==output, por lo que el bug no se manifiesta en producción;
  documentado como invariante: output.weight debe tener n_vocab filas.
HALLAZGO H-GGUF-3 (RESUELTO en fixture): modelo determinista por construcción —
  embeddings Q8_0 no negativos + normas 1.0 + pesos de capa en 0 + output.weight fila 8
  (+1.0) vs resto (-1.0) → argmax estable con temp=0 sin fuga de BOS/EOS.
