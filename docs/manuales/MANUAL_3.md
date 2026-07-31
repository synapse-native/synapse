MANUAL 3: ARQUITECTURA DEL COMPILADOR (PIPELINE)
Archivo: 03_COMPILADOR_PIPELINE.md
Versión: 5.1.1-industrial
Propósito: Describir las 5 etapas del compilador, el AST, la tabla de símbolos, el sistema de errores y la compilación incremental.

3.1 Las 5 Etapas del Pipeline
text
┌─────────────┐
│ fuente.syn  │ (UTF-8)
└──────┬──────┘
       ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 1: LEXER (lexer.syn)                                  │
│  - Lee caracteres, inyecta INDENT/DEDENT por indentación.   │
│  - Detecta #lang: y selecciona diccionario multi-idioma.   │
│  - Salida: flujo de tokens (TokenID + valor + ubicación).  │
└─────────────────────────────────────────────────────────────┘
       ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 2: PARSER (parser.syn)                                │
│  - Descenso recursivo puro.                                 │
│  - Construye AST (linked-list de Nodo*).                   │
│  - Salida: AST enlazado.                                   │
└─────────────────────────────────────────────────────────────┘
       ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 3: ANALIZADOR SEMÁNTICO (analizador_semantico.syn)   │
│  - 3 pasadas: 1) Estructuras, 2) Firmas, 3) Cuerpos.       │
│  - Inferencia de tipos (Hindley-Milner).                   │
│  - Verificación de Ownership y Lifetimes.                  │
│  - Salida: SemNodo[] aplanado + Tabla de Símbolos.         │
└─────────────────────────────────────────────────────────────┘
       ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 4: GENERADOR C (generator.syn)                        │
│  - Traduce SemNodo[] a código C estándar.                  │
│  - Inyecta contratos como assert().                        │
│  - Genera código para canales, estructuras, etc.           │
│  - Salida: synapse_unity.c (o .c separados).              │
└─────────────────────────────────────────────────────────────┘
       ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 5: BACKEND (GCC/Clang/LLVM)                          │
│  - Compila .c + runtime (synapse_rt.o, axon_rt.o).        │
│  - Enlaza con -lpthread -lm (y -lws2_32 en Windows).     │
│  - Salida: binario nativo (.exe, ELF) o WASM (.wat/.wasm).│
└─────────────────────────────────────────────────────────────┘
3.2 El AST (Árbol de Sintaxis Abstracta)
Estructura base del Nodo:

c
// Definición en nucleo/ast_nodes.syn
typedef struct Nodo {
    int tipo;               // NODO_PROGRAMA, NODO_FUNCION, ...
    int linea;
    int columna;
    struct Nodo* siguiente; // Linked-list (hermanos)
    union {
        struct {
            char nombre[64];
            int num_params;
            struct Nodo* params;
            struct Nodo* cuerpo;
            struct Nodo* contratos;
        } funcion;
        struct {
            struct Nodo* condicion;
            struct Nodo* cuerpo_si;
            struct Nodo* cuerpo_sino;
        } si;
        struct {
            char nombre[64];
            struct Nodo* expr;
        } asignacion;
        struct {
            char nombre[64];
            struct Nodo* args;
        } llamada;
        // ... más uniones para cada tipo de nodo
    };
} Nodo;
Constantes de tipo de nodo (tabla completa — 46 tipos reales definidos en nucleo/parser_constantes.syn):

Constante	Valor	Descripción
NODO_PROGRAMA	1	Raíz del archivo
NODO_FUNCION	2	Definición de función
NODO_SI	3	Condicional si
NODO_MIENTRAS	4	Bucle mientras
NODO_RETORNAR	5	Sentencia retornar
NODO_EXPR	6	Sentencia de expresión
NODO_ASIGNACION	7	Asignación =
NODO_IDENTIFICADOR	8	Referencia a identificador
NODO_NUMERO	9	Literal numérico (entero)
NODO_DECIMAL	10	Literal numérico (decimal)
NODO_CADENA_LIT	11	Literal de cadena
NODO_BINARIA	12	Operación binaria (+, -, *, /, ...)
NODO_UNARIA	13	Operación unaria (-, !, ...)
NODO_LLAMADA	14	Llamada a función
NODO_PARAMETRO	15	Parámetro de función
NODO_ESTRUCTURA	16	Definición de estructura
NODO_IMPORTAR	17	Sentencia importar
NODO_LANZAR	18	Sentencia lanzar (spawn)
NODO_ESCUCHAR	19	Sentencia escuchar (listen)
NODO_ROMPER	20	Sentencia romper (break)
NODO_SIGUIENTE	21	Sentencia siguiente (continue)
NODO_BOOLEANO	22	Literal booleano (verdadero/falso)
NODO_CONSTANTE	23	Declaración de constante
NODO_INSEGURO	24	Bloque inseguro
NODO_IMPORTAR_C	25	Importar código C
NODO_EXTERNO	26	Declaración externa
NODO_RECUPERAR	27	Sentencia recuperar (recover)
NODO_TENSOR	28	Expresión tensor
NODO_INDICE	29	Acceso por índice []
NODO_TRANSFERIDO	30	Argumento transferido (ownership move)
NODO_ACCESO_CAMPO	31	Acceso a campo (objeto.campo)
NODO_ASIGNACION_CAMPO	32	Asignación a campo
NODO_PARRAFO	33	Párrafo (bloque de sentencias)
NODO_DECLARACION	34	Declaración de variable
NODO_LOG	35	Llamada de log
NODO_PUNTERO	36	Tipo puntero
NODO_DEREF	37	Desreferencia de puntero
NODO_COINCIDIR	38	Sentencia coincidir (match)
NODO_CASO	39	Caso de coincidir
NODO_ASM	40	Bloque asm
NODO_CANAL_CREAR	41	Creación de canal
NODO_ENVIAR_CANAL	42	Envío a canal
NODO_RECIBIR_CANAL	43	Recepción de canal
NODO_VACIO	44	Nodo vacío
NODO_PARA	45	Bucle para
NODO_CONTRATO	46	Bloque requiere/garantiza
AST Aplanado (SemNodo[]):

Para el análisis semántico, la linked-list se aplana a un array contiguo:

c
#define F8_MAX_NODOS 65536

typedef struct {
    int tipo_nodo;
    int linea, columna;
    // Metadatos de ownership
    int owner_id;
    int scope_id;
    bool is_owned;
    bool es_prestado_inmutable;
    bool es_prestado_mutable;
    union {
        struct { char nombre[64]; int num_params; } funcion;
        // ... igual que Nodo pero sin punteros (solo datos planos)
    };
} SemNodo;
3.3 El Analizador Semántico (3 Pasadas)
c
void analizar(AnalizadorSemanticoEst* est) {
    // --- PASADA 1: ESTRUCTURAS Y TIPOS GLOBALES ---
    for (int i = 0; i < est->total_nodos; i++) {
        if (est->nodos[i].tipo_nodo == NODO_ESTRUCTURA) {
            _sem_registrar_struct(est, &est->nodos[i]);
        }
    }

    // --- PASADA 2: FIRMAS DE FUNCIONES (sin cuerpos) ---
    for (int i = 0; i < est->total_nodos; i++) {
        if (est->nodos[i].tipo_nodo == NODO_FUNCION) {
            _sem_registrar_funcion(est, &est->nodos[i]);
        }
    }

    // --- PASADA 3: CUERPOS DE FUNCIÓN + OWNERSHIP + LIFETIMES ---
    for (int i = 0; i < est->total_nodos; i++) {
        if (est->nodos[i].tipo_nodo == NODO_FUNCION) {
            _sem_analizar_cuerpo(est, &est->nodos[i]);
        }
    }
}
Tabla de Símbolos (estructura interna):

c
typedef struct {
    char nombre[64];
    int tipo;           // TIPO_ENTERO, TIPO_FUNCION, TIPO_ESTRUCTURA, ...
    int scope_id;
    int owner_id;       // Para tracking de ownership
    bool es_movido;     // Ya fue movido?
    int num_referencias; // Conteo de préstamos inmutables
    bool tiene_mut_borrow;
} Simbolo;
Inferencia de Tipos (Hindley-Milner):

Las variables de tipo se representan como TVar(id).

La unificación se realiza mediante el algoritmo estándar con occurs check.

Si una expresión tiene tipo ambiguo (ej. []), se emite ERR_SEM_TYPE_AMBIGUOUS y se pide anotación explícita.

3.4 Sistema de Caché Incremental (v5.0)
Clave de caché:

text
clave = SHA-256(
    contenido_archivo +
    hash_dependencias (ordenadas) +
    flags_compilacion +
    version_compilador
)
Estructura de la entrada de caché:

c
typedef struct {
    char key[65];              // SHA-256 hex
    char ast_hash[65];         // SHA-256 del AST
    char* codigo_c;            // Código C generado
    size_t codigo_len;
    char** dependencias;       // Lista de archivos importados
    int num_deps;
    char flags[256];
    time_t timestamp;
} CacheEntry;
Flujo:

Calcular clave.

Buscar en ~/.synapse/cache/.

Si existe y el ast_hash coincide → CACHÉ HIT (usar objeto compilado).

Si existe pero ast_hash no coincide → CACHÉ STALE (recompilar y actualizar).

Si no existe → CACHÉ MISS (compilar y guardar).

3.5 Taxonomía de Errores del Compilador (Códigos)
Categoría	Rango	Ejemplo
Léxico	ERR_LEX_*	ERR_LEX_TAB_DETECTED (tabulador), ERR_LEX_MISSING_LANG
Sintáctico	ERR_SYNTAX_*	ERR_SYNTAX_EXPECTED_TOKEN, ERR_INDENT_INVALID
Semántico	ERR_SEM_*	ERR_SEM_TYPE_AMBIGUOUS, ERR_SEM_REDEFINICION
Memoria	ERR_MEM_*	ERR_MEM_USE_AFTER_MOVE, ERR_MEM_LIFETIME_MISMATCH
Caché	ERR_CACHE_*	ERR_CACHE_CORRUPT, ERR_CACHE_VERSION_MISMATCH