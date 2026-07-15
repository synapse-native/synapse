# Tokenizador BPE (Byte-Pair Encoding)

El tokenizador BPE es el componente que convierte texto en secuencias de enteros (tokens) que el transformer puede procesar, y viceversa.

## Arquitectura

```
Texto ──► Pre-tokenización ──► BPE merge ──► IDs de token
              │                      │
        división por           fusión iterativa
        whitespace y           del par con menor
        puntuación             rango (rank)
```

## Estructuras de datos

### BpeContext

```c
typedef struct {
    int vocab_size;        // tamaño total del vocabulario
    char** tokens;         // arreglo [vocab_size] de strings de token
    int num_merges;        // cantidad de reglas de fusión
    BpeMerge* merges;      // reglas de fusión (first, second → result)
    int bos_id, eos_id;    // tokens especiales BOS/EOS
} BpeContext;
```

### BpeMerge

```c
typedef struct {
    int first;   // ID del primer token del par
    int second;  // ID del segundo token del par
    int result;  // ID del token resultado de la fusión
} BpeMerge;
```

## Carga desde GGUF

```
_syn_gguf_abrir()
    │
    ├── tokenizer.ggml.tokens  →  BpeContext.tokens[]
    ├── tokenizer.ggml.merges  →  BpeContext.merges[]
    ├── tokenizer.ggml.bos_id  →  BpeContext.bos_id
    └── tokenizer.ggml.eos_id  →  BpeContext.eos_id
```

Las reglas de fusión se cargan desde el metadato ARRAY `tokenizer.ggml.merges`. Cada entrada es un string con formato `"tokenA tokenB"`. Se parsea dividiendo por el último espacio y haciendo lookup de cada token en el vocabulario base para obtener su ID.

## Pre-tokenización (GPT-2 style)

Antes de aplicar BPE, el texto se segmenta en unidades atómicas:

1. División por **whitespace** (` `, `\t`, `\n`, `\r`)
2. Cada palabra se subdivide en segmentos de **letras**, **dígitos** y **puntuación**
3. Cada segmento se codifica independientemente con BPE

```
"¡Hola, mundo!"  →  ["¡Hola", ",", "mundo", "!"]
```

## Algoritmo BPE

```
función codificar_palabra(palabra, ctx):
    // Fase 1: mapear caracteres a tokens base
    tokens = []
    para cada char en palabra:
        si char está en el vocabulario:
            tokens.append(id[char])
        sino:
            tokens.append(UNK=0)

    // Fase 2: fusionar iterativamente
    mientras True:
            mejor_par = encontrar_par_con_menor_rank(tokens, ctx.merges)
            si no hay par fusionable:
                romper
            reemplazar par en tokens con token_resultado

    retornar tokens
```

### Búsqueda de mejor par (`_bpe_mejor_fusion`)

Recorre linealmente todas las reglas de fusión (`merges[]`) buscando el par `(tokens[i], tokens[i+1])` que tenga el **índice de merge más bajo** (menor rank = mayor prioridad).

```c
static int _bpe_mejor_fusion(BpeContext* ctx, int* tokens, int n) {
    int mejor_rank = ctx->num_merges;  // peor caso
    int mejor_pos = -1;
    for (int i = 0; i < n - 1; i++) {
        for (int m = 0; m < ctx->num_merges; m++) {
            if (ctx->merges[m].first == tokens[i] &&
                ctx->merges[m].second == tokens[i+1] &&
                m < mejor_rank) {
                mejor_rank = m;
                mejor_pos = i;
            }
        }
    }
    return mejor_pos;  // -1 si no hay fusión
}
```

## API pública

| Función | Descripción |
|---------|-------------|
| `_syn_modelo_codificar_contar(ctx, texto)` | Codifica el texto y devuelve la cantidad de tokens. El resultado se cachea en `ctx->ultima_codificacion`. |
| `_syn_modelo_codificar_obtener(ctx, i)` | Devuelve el i-ésimo token de la última codificación. |
| `_syn_modelo_decodificar_token(ctx, id)` | Devuelve el string asociado a un ID de token. |
