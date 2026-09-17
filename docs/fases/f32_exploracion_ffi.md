# Fase 32 — Exploración FFI y Arquitectura del AST

> Bitácora de exploración para el diseño del puente FFI (lista/mapa) y el
> acceso al AST canónico SemNodo[] desde código nativo y el puente Python.

## Misión derivada de MEMORIA_PROYECTO.md

**Fase del roadmap:** Fase 32 (agente de codificación). Sub-fases completadas:
- F32.1: grafo de conocimiento (`nucleo/grafo_conocimiento.syn`)
- F32.2: `explorer_det` determinista (BFS)
- F32.3: `architect_det` determinista (DFS + Tarjan)
- F32.4: pipeline multi-agente optimizado

Próximo ME: Fase 32.5+ — puente FFI para listas/mapas y acceso al AST.

## Factos arquitectónicos confirmados

### SemNodo struct (Manual 6 §1.1, Manual 2 §7.3)

Definido en dos lugares:

1. **`nucleo/analizador_semantico.syn:74-85`** — versión rica usada por el
   analizador semántico nativo (runtime C).
2. **`nucleo/ast_abi.syn`** — versión canónica ABI v1, con verificador formal
   `ast_abi_verificar()` (líneas 43-172).

Campos (11 total):
```
tipo_nodo: entero    // slot 0 — NODO_* constant
linea: entero        // slot 1
columna: entero      // slot 2
valor_int: entero    // slot 3
valor_dec: decimal   // slot 4
ptr_str: entero      // slot 5 — low 32 bits del string payload (ptr_str)
len_str: entero      // slot 6 — longitud del string payload
hijo_izq: entero     // slot 7 — índice hermano/child izquierdo
hijo_der: entero     // slot 8 — índice child derecho
hermano: entero      // slot 9 — índice hermano
ptr_extra: entero     // slot 10 — low 32 bits de payload secundario (tipo_retorno, etc.)
```

El ABI define `AST_ABI_NODOS_CAMPOS = 10` (Manual 6 §1.2) donde ptr_str+len_str
se cuentan como un "span texto" — 10 campos numericos + valor_dec como decimal.

### NodoAST struct (Manual 2 §7.3)

Definido en **`nucleo/parser_base.syn:11`** (producción) y en los archivos
temporales `_tmp_sq_*_drv.syn`. Layout idéntico a SemNodo (11 campos).

### NODO_* constants

NO existen como enum C en `synapse_rt_types.h`. Existen como declaraciones
Synapse `constante` en **`nucleo/parser_constantes.syn`** (importada via
`importar parser_constantes`). La `ast_abi.syn:16` confirma el patrón:

```synapse
importar parser_constantes
// luego usa NODO_PROGRAMA, NODO_FUNCION, etc. directamente
```

Los valores canónicos (parser_constantes.syn):
```
NODO_PROGRAMA      = 1
NODO_FUNCION       = 2
NODO_SI            = 3
NODO_MIENTRAS      = 4
NODO_RETORNAR      = 5
NODO_EXPR          = 6
NODO_ASIGNACION    = 7
NODO_IDENTIFICADOR = 8
NODO_NUMERO        = 9
NODO_DECIMAL       = 10
NODO_CADENA_LIT    = 11
NODO_BINARIA       = 12
NODO_UNARIA        = 13
NODO_LLAMADA       = 14
NODO_PARAMETRO     = 15
NODO_ESTRUCTURA    = 16
NODO_IMPORTAR      = 17
NODO_LANZAR        = 18
NODO_ESCUCHAR      = 19
NODO_ROMPER        = 20
NODO_SIGUIENTE     = 21
NODO_BOOLEANO      = 22
NODO_CONSTANTE     = 23
NODO_INSEGURO      = 24
NODO_IMPORTAR_C    = 25
NODO_EXTERNO       = 26
NODO_RECUPERAR     = 27
NODO_TENSOR        = 28
NODO_INDICE        = 29
NODO_TRANSFERIDO   = 30
NODO_ACCESO_CAMPO  = 31
NODO_ASIGNACION_CAMPO = 32
NODO_PARRAFO       = 33
NODO_DECLARACION   = 34
NODO_LOG           = 35
NODO_PUNTERO       = 36
NODO_DEREF         = 37
NODO_COINCIDIR     = 38
NODO_CASO          = 39
NODO_ASM           = 40
NODO_CANAL_CREAR   = 41
NODO_ENVIAR_CANAL  = 42
NODO_RECIBIR_CANAL = 43
NODO_VACIO         = 44
NODO_PARA          = 45
NODO_CONTRATO      = 46
NODO_NULO          = 47
NODO_LET           = 48
NODO_DELEGAR       = 49
NODO_EXPORT        = 50
NODO_DECLARACION_TIPO = 51
NODO_CONSTRUCTOR   = 52
NODO_PROPAGAR      = 53
NODO_INTENTO       = 54
NODO_LISTA_LIT     = 55
NODO_MAPA_LIT      = 56
NODO_PARA_EN       = 57
NODO_BLOQUE_SQ     = 58
```

**CRUCIAL:** `ast_abi.syn:12` declara: "los valores del Manual 2 §7.2 son
ILUSTRATIVOS" y `parser_constantes.syn` es la **fuente única de verdad**.

### 64-bit string pointer reconstruction

`nucleo/puente_ast.syn:52-66` (`puente_str` function) muestra el patrón
canónico para reconstruir punteros de 64 bits:

```c
struct NodoAST* _an_s = (struct NodoAST*)parser_nodos();
int* _ahi_s = (int*)parser_ptr_hi();
uintptr_t _pp_s = (uintptr_t)(unsigned)_an_s[idx].ptr_str
               | ((uintptr_t)(unsigned)_ahi_s[idx] << 32);
int _pl_s = _an_s[idx].len_str;
```

- `ptr_str` = bajo 32 bits del puntero
- `ptr_hi[idx]` = altos 32 bits (array paralelo)
- `len_str` = longitud del buffer
- `parser_ptr_hi()` retorna el array paralelo

### FFI: lista/mapa (handle-based, NOT type-based)

El patrón FFI para listas y mapas usa **`entero` como handle**, no una
clave de tipo `lista`/`mapa`. Definido en `tests/_probe_syntax.syn:10-18`:

```synapse
externo funcion _syn_lista_crear() -> entero
externo funcion _syn_lista_longitud(l: entero) -> entero
externo funcion _syn_lista_agregar(l: entero, v: entero)
externo funcion _syn_lista_obtener(l: entero, i: entero) -> entero
externo funcion _syn_lista_establecer(l: entero, i: entero, v: entero)
externo funcion _syn_mapa_crear() -> entero
externo funcion _syn_mapa_poner(m: entero, k: texto, v: entero)
externo funcion _syn_mapa_obtener(m: entero, k: texto) -> entero
externo funcion _syn_mapa_contiene(m: entero, k: texto) -> entero
```

**La excepción:** `_syn_mapa_poner` y `_syn_mapa_obtener` usan `texto` como
clave (no `entero`), porque las claves de mapa son cadenas.

### C runtime FFI — lista/mapa fully implemented

The C runtime has complete implementations. The handle type `void*` maps to
`entero` (int64_t) in the Synapse FFI.

**`runtime/core/lista.c`** — Dynamic array (vector) of `int64_t`:
```c
typedef struct {
    int64_t* datos;
    int longitud;
    int capacidad;
} ListaSyn;
```

| Function | C signature | Purpose |
|----------|-------------|---------|
| `_syn_lista_crear` | `void* _syn_lista_crear(void)` | Create new list (handle) |
| `_syn_lista_longitud` | `int _syn_lista_longitud(void* l)` | Get length |
| `_syn_lista_agregar` | `void _syn_lista_agregar(void* l, int64_t e)` | Append element |
| `_syn_lista_obtener` | `int64_t _syn_lista_obtener(void* l, int i)` | Get element by index |
| `_syn_lista_establecer` | `void _syn_lista_establecer(void* l, int i, int64_t v)` | Set element |
| `_syn_lista_eliminar` | `void _syn_lista_eliminar(void* l, int i)` | Remove by index |
| `_syn_lista_limpiar` | `void _syn_lista_limpiar(void* l)` | Clear (keep capacity) |
| `_syn_lista_liberar` | `void _syn_lista_liberar(void* l)` | Free all memory |

**`runtime/core/mapa.c`** — Hash map with string keys (`char*`) → `int64_t` values:
```c
typedef struct {
    char* clave;
    int64_t valor;
    int estado;  // 0=VACIO, 1=OCUPADO, 2=BORRADO
} ParMapa;

typedef struct {
    ParMapa* pares;
    int capacidad;
    int longitud;
} MapaSyn;
```

| Function | C signature | Purpose |
|----------|-------------|---------|
| `_syn_mapa_crear` | `void* _syn_mapa_crear(void)` | Create new map |
| `_syn_mapa_longitud` | `int _syn_mapa_longitud(void* m)` | Get pair count |
| `_syn_mapa_poner` | `void _syn_mapa_poner(void* m, const char* k, int64_t v)` | Set key→value |
| `_syn_mapa_obtener` | `int64_t _syn_mapa_obtener(void* m, const char* k)` | Get value by key |
| `_syn_mapa_contiene` | `int _syn_mapa_contiene(void* m, const char* k)` | Check key exists |
| `_syn_mapa_eliminar` | `void _syn_mapa_eliminar(void* m, const char* k)` | Remove key |
| `_syn_mapa_limpiar` | `void _syn_mapa_limpiar(void* m)` | Clear all |
| `_syn_mapa_claves` | `void* _syn_mapa_claves(void* m)` | Return list of key ptrs |
| `_syn_mapa_valores` | `void* _syn_mapa_valores(void* m)` | Return list of values |
| `_syn_mapa_liberar` | `void _syn_mapa_liberar(void* m)` | Free all memory |

**Fixture test:** `tests/fixtures/test_f24_lista_mapa.c:529-549` shows the exact
calling convention — handles are `int64_t`, keys are `CadenaSegura` (not raw
`char*`). The Synapse FFI layer converts `texto` → `CadenaSegura.datos`
internally.

**Sintaxis Synapse correcta para FFI** (validada contra lista.c/mapa.c):
```synapse
externo funcion _syn_lista_crear() -> entero
externo funcion _syn_lista_longitud(l: entero) -> entero
externo funcion _syn_lista_agregar(l: entero, v: entero)
externo funcion _syn_lista_obtener(l: entero, i: entero) -> entero
externo funcion _syn_lista_establecer(l: entero, i: entero, v: entero)
externo funcion _syn_lista_eliminar(l: entero, i: entero)
externo funcion _syn_lista_liberar(l: entero)
externo funcion _syn_mapa_crear() -> entero
externo funcion _syn_mapa_longitud(m: entero) -> entero
externo funcion _syn_mapa_poner(m: entero, k: texto, v: entero)
externo funcion _syn_mapa_obtener(m: entero, k: texto) -> entero
externo funcion _syn_mapa_contiene(m: entero, k: texto) -> entero
externo funcion _syn_mapa_eliminar(m: entero, k: texto)
externo funcion _syn_mapa_liberar(m: entero)
```

### Alto-nivel Lista<T> / Mapa<K,V> types

En `nucleo/grafo_conocimiento.syn:50-52` y `nucleo/reports.syn` se usan
como type aliases:

```synapse
nodos: Lista<NodoGrafo>
aristas: Lista<AristaGrafo>
indice_por_id: Mapa<texto, entero>
```

Métodos disponibles:
- `lista.len()` — longitud (grafo_conocimiento.syn:373, :403)
- `cadena.len()` — longitud de texto (grafo_conocimiento.syn:403)
- `cadena[i]` o `codigo_caracter(texto, i)` — acceso a carácter

### ParserEst struct

Definido en `nucleo/parser_base.syn:25-38` (y temp files). Campos clave:
- `nodos: NodoAST` — array plano de nodos
- `total_nodos: entero`
- `ptr_hi: entero` — array paralelo de high-32-bits
- `tokens: TokenExt` + `total_tokens: entero`
- `error_mensaje: cadena`, `error_linea: entero`, `error_columna: entero`

### puente_ast.syn (FASE A — puente plano→tipado)

`nucleo/puente_ast.syn` contiene el dispatcher principal `puente_nodo(idx)`
que convierte un `NodoAST[idx]` plano → `struct Nodo*` tipado. Incluye:

- `puente_str(idx)` — extrae payload primario (ptr_str+ptr_hi+len_str → malloc'd char*)
- `puente_str2(idx)` — extrae payload secundario (tipo/tipo_retorno → char*)
- `puente_tok(tipo, lexema)` — crea struct Token* para operadores
- `puente_operador(codigo)` — mapea códigos 100-501 a tokens T_* canónicos
- `puente_lista(idx)` — cadena de hermanos → ListaNodo*
- `puente_lista_param(idx)` — chain de parámetros → ListaParametro*

### Test probe: tests/_probe_syntax.syn

Archivo de sondeo creado para validar la sintaxis FFI. Resultados de
compilación (iteraciones err1.txt–err8.txt):

- `lista<entero>()` ❌ — el parser nativo no reconoce la sintaxis genérica
  con paréntesis; usar `_syn_lista_crear()` (FFI handle).
- `[1, 2, 3]` ❌ — no hay sintaxis de array literal entre corchetes.
- `externo funcion` sin `-> tipo` ❌ — requiere tipo de retorno explícito.
- `importar analizador_semantico` ❌ — no declarado en el manifiesto axon.toml.

## Archivos de interés para el próximo paso

| Archivo | Rol | Líneas clave |
|---------|-----|-------------|
| `nucleo/parser_constantes.syn` | NODO_* constants (fuente de verdad) | TODO |
| `nucleo/ast_abi.syn` | ABI verifier + layout docs | 1-180 |
| `nucleo/puente_ast.syn` | Flat→typed AST bridge | 1-617 |
| `nucleo/parser_base.syn` | NodoAST + ParserEst struct | 1-90 |
| `nucleo/analizador_semantico.syn` | SemNodo + AnalizadorSemanticoEst | 74-163 |
| `nucleo/principal.syn` | F8 flatten (_f8_ptr_hi pattern) | 228-558 |
| `runtime/core/lista.c` | C FFI list implementation | 1-95 |
| `runtime/core/mapa.c` | C FFI map implementation | 1-213 |
| `tests/fixtures/test_f24_lista_mapa.c` | C fixture test (calling convention) | 526-549 |
| `tests/_probe_syntax.syn` | FFI probe (iteración) | 1-22 |
| `tests/opensyn/test_grafo.py` | Test del grafo de conocimiento | 1-122 |

## Lecturas registradas (auditoria/lecturas.jsonl)

Registro de la sesión: 13 archivos leídos y registrados, citando
Manual 2 §12, Manual 6 §1.1, Manual 32 §2-4, §4.3-4.4, §7.1.

## Estado de mapa_alineacion.md

Entrada añadida:
```
"nucleo/grafo_conocimiento.syn": ["Manual 6 §1.1", "Manual 2 §5.1"]
```
