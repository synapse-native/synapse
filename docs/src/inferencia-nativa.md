# Inferencia Nativa (Transformers en C)

El motor de inferencia de Synapse ejecuta transformers completos en C nativo, sin dependencias externas (ni Python, ni CUDA, ni ONNX Runtime).

## Pipeline de Inferencia

```
Token ID ──► Embedding ──► Transformer ──► Logits ──► Sampling ──► Token ID
                │           │                           │
           w_emb[]      n_layers capas              top-k / top-p
                        │                           + temperature
                    RMSNorm + RoPE
                    QKV proyecciones
                    Attention (GQA)
                    SwiGLU FFN
```

## ModeloContexto

```c
typedef struct {
    // Buffers de trabajo (heap)
    float* w_hidden, *w_attn_norm, *w_ffn_norm;
    float* w_q, *w_k, *w_v, *w_attn_out;
    float* w_gate, *w_up, *w_down, *w_scores;

    // Arquitectura
    int n_layers, n_heads, n_kv_heads, n_embd, n_ff;
    float rope_theta;
    int max_seq_len;

    // KV cache (n_layers * n_kv_heads * max_seq_len * head_dim)
    float* k_cache, *v_cache;
    int n_past;

    // Tokenizador BPE
    BpeContext* bpe;
    TokenArray ultima_codificacion;

    // Peso del LM head
    float* output_weight;

    // GGUF subyacente
    void* datos_internos;
} ModeloContexto;
```

## Forward Pass (`_modelo_evaluar_token`)

### 1. Embedding

Cada token ID se convierte en un vector `w_emb[token_id]` (una fila de la matriz de embeddings).

### 2. Capa del transformer (para cada una de `n_layers`)

```
a. RMSNorm pre-attention
   an = rmsnorm(hidden, w_attn_norm[l])
   función rmsnorm(x, weight):
       ss = mean(x²) + 1e-6
       return weight * x / sqrt(ss)

b. Proyecciones QKV (con sesgo de 1:1 para V)
   Q = an @ w_q[l]^T
   K = an @ w_k[l]^T
   V = an @ w_v[l]^T

c. RoPE (Rotary Position Embedding)
   para cada head h en Q, K:
       para cada par (d, d+1) en head_dim:
           θ = pos / (rope_theta^(2d/head_dim))
           rotar(Q[h][d], Q[h][d+1], cos(θ), sin(θ))
           rotar(K[h][d], K[h][d+1], cos(θ), sin(θ))

d. KV cache
   k_cache[l][head][pos][:] = K[head][:]
   v_cache[l][head][pos][:] = V[head][:]

e. Atención GQA (Grouped-Query Attention)
   n_groups = n_heads / n_kv_heads
   para cada grupo g:
       para cada kv_head:
           scores = Q[g*n_groups + hq] @ k_cache[pos]^T
           scores /= sqrt(head_dim)
           attn = softmax(scores)
           out += attn @ v_cache[pos]
       out = out @ w_attn_out[l]^T

f. Residual
   hidden = hidden + attention_output

g. RMSNorm pre-FFN
   an = rmsnorm(hidden, w_ffn_norm[l])

h. SwiGLU FFN (SwiGLU = silu(gate) * up)
   gate = silu(an @ w_gate[l]^T)   donde silu(x) = x / (1 + exp(-x))
   up   = an @ w_up[l]^T
   hidden = (gate * up) @ w_down[l]^T

i. Residual
   hidden = hidden + ffn_output
```

### 3. Finalización

```
hidden = rmsnorm(hidden, w_output_norm)
logits = hidden @ output_weight^T   (LM head)
```

## Sampling

```c
int _syn_modelo_generar(ctx, token_id, temperature, top_k, top_p) {
    // 1. Forward pass (token_id → logits)
    Tensor logits = _syn_modelo_evaluar(ctx, token_id);

    // 2. Top-K: solo los K logits más altos
    _filtro_top_k(logits, top_k);

    // 3. Top-P: solo el conjunto más pequeño con P acumulada
    //    Aplica softmax, ordena, acumula, filtra
    _filtro_top_p(logits, top_p);

    // 4. Escala por temperatura
    for (i = 0; i < n; i++)
        logits[i] /= temperature;

    // 5. Muestreo multinomial
    prob = softmax(logits);
    r = uniforme(0, 1);
    acum = 0;
    for (i = 0; i < n; i++) {
        acum += prob[i];
        if (r < acum) return i;
    }
    return n - 1;
}
```

## Generación de texto (`_syn_modelo_generar_texto`)

```
1. prompt → BPE tokenizer → token_ids[]
2. Para cada token_id en prompt_ids:
       _syn_modelo_generar(ctx, token_id, temp, top_k, top_p)
3. Mientras nuevo_token != EOS y count < max_tokens:
       nuevo_token = _syn_modelo_generar(ctx, último, temp, ...)
       token_str = _syn_modelo_decodificar_token(ctx, nuevo_token)
       salida.append(token_str)
4. Retornar salida como CadenaSegura
```

## Formatos de cuantización soportados

| Tipo GGML | ID | Soportado |
|-----------|----|-----------|
| F32 | 0 | ✅ Sí |
| F16 | 1 | ❌ No |
| Q4_0 | 2 | ❌ No |
| Q4_1 | 3 | ❌ No |
| Q5_0 | 6 | ❌ No |
| Q5_1 | 7 | ❌ No |
| Q8_0 | 8 | ❌ No |
