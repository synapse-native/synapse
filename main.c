// salida_metal.c - Generado por Synapse Compilador
// Lenguaje: Synapse v1.0 (#lang: es)
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <string.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

typedef struct { uint32_t filas; uint32_t columnas; float* datos; } Tensor;

typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;

// Constantes del pool de memoria (definidas en synapse_rt.c)
#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096

// Constantes de tags para uniones etiquetadas (ADTs)
#define TAG_OK 0
#define TAG_ERR 1
#define TAG_ALGUNO 0
#define TAG_NINGUNO 1

// --- Declaraciones extern del runtime precompilado (synapse_rt.o) ---
extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void pool_free(void* ptr);
extern void escribir(CadenaSegura contenido);
extern void escribir_linea(CadenaSegura contenido);
extern CadenaSegura leer_linea(void);
extern Canal abrir(CadenaSegura ruta, CadenaSegura modo);
extern CadenaSegura leer(Canal canal);
extern void cerrar(Canal canal);
extern Tensor crear_tensor(int filas, int columnas);
extern Tensor suma_tensor(Tensor a, Tensor b);
extern Tensor producto_punto(Tensor a, Tensor b);
extern Tensor relu(Tensor a);
extern Tensor reserva(int tamano);
extern void libera(Tensor bloque);
extern Tensor suma(Tensor a, Tensor b);
extern Tensor producto(Tensor a, Tensor b);
extern int texto_a_entero(CadenaSegura str);
extern float texto_a_decimal(CadenaSegura str);
extern CadenaSegura decimal_a_texto(float n);
extern CadenaSegura entero_a_texto(int n);
extern void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);
extern void synapse_esperar_hilos(void);

static int _g_argc;
static char** _g_argv;
int _argc() { return _g_argc; }

CadenaSegura _argv(int i) {
    if (i < 0 || i >= _g_argc) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_g_argv[i]), .datos = _g_argv[i] };
}

void salir(int codigo) { exit(codigo); }

CadenaSegura concat(CadenaSegura a, CadenaSegura b) {
    int _tl = a.longitud + b.longitud;
    char* _buf = (char*)malloc(_tl + 1);
    if (!_buf) { fprintf(stderr,"Error: Asignación de memoria falló en concat()\n"); exit(1); }
    memcpy(_buf, a.datos, a.longitud);
    memcpy(_buf + a.longitud, b.datos, b.longitud);
    _buf[_tl] = 0;
    CadenaSegura _r = { .longitud = _tl, .datos = _buf };
    return _r;
}

struct Token;
struct Nodo;
struct ListaNodo;
struct Programa;
struct Identificador;
struct LiteralNumero;
struct LiteralCadena;
struct OpBinaria;
struct OpUnaria;
struct LlamadaFuncion;
struct ExprAccesoCampo;
struct AsignacionVariable;
struct AsignacionCampo;
struct SentenciaSi;
struct SentenciaMientras;
struct SentenciaRetornar;
struct SentenciaExpr;
struct LogLlamada;
struct Parametro;
struct ListaParametro;
struct DefinicionFuncion;
struct DefinicionEstructura;
struct SentenciaRomper;
struct SentenciaSiguiente;
struct SentenciaLanzar;
struct SentenciaRecuperar;
struct SentenciaEscuchar;
struct ExprTensor;
struct ExprIndice;
struct ArgumentoTransferido;
struct SentenciaImportar;
struct BloqueInseguro;
struct ExprObtenerDireccion;
struct ExprDereferencia;
struct ImportarC;
struct DeclaracionExterna;

typedef struct Token {
    int tipo;
    CadenaSegura lexema;
    int linea;
    int columna;
} Token;

static inline struct Token Token_nuevo() {
    struct Token _r = {0};
    return _r;
}

typedef struct Nodo {
    CadenaSegura tipo;
} Nodo;

static inline struct Nodo Nodo_nuevo() {
    struct Nodo _r = {0};
    return _r;
}

typedef struct ListaNodo {
    struct Nodo* cabeza;
    struct ListaNodo* cola;
} ListaNodo;

static inline struct ListaNodo ListaNodo_nuevo() {
    struct ListaNodo _r = {0};
    return _r;
}

typedef struct Programa {
    CadenaSegura tipo;
    struct ListaNodo* sentencias;
} Programa;

static inline struct Programa Programa_nuevo() {
    struct Programa _r = {0};
    return _r;
}

typedef struct Identificador {
    CadenaSegura tipo;
    CadenaSegura nombre;
} Identificador;

static inline struct Identificador Identificador_nuevo() {
    struct Identificador _r = {0};
    return _r;
}

typedef struct LiteralNumero {
    CadenaSegura tipo;
    int valor;
} LiteralNumero;

static inline struct LiteralNumero LiteralNumero_nuevo() {
    struct LiteralNumero _r = {0};
    return _r;
}

typedef struct LiteralCadena {
    CadenaSegura tipo;
    CadenaSegura valor;
} LiteralCadena;

static inline struct LiteralCadena LiteralCadena_nuevo() {
    struct LiteralCadena _r = {0};
    return _r;
}

typedef struct OpBinaria {
    CadenaSegura tipo;
    struct Nodo* izquierdo;
    struct Token* operador;
    struct Nodo* derecho;
} OpBinaria;

static inline struct OpBinaria OpBinaria_nuevo() {
    struct OpBinaria _r = {0};
    return _r;
}

typedef struct OpUnaria {
    CadenaSegura tipo;
    struct Token* operador;
    struct Nodo* expr;
} OpUnaria;

static inline struct OpUnaria OpUnaria_nuevo() {
    struct OpUnaria _r = {0};
    return _r;
}

typedef struct LlamadaFuncion {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaNodo* argumentos;
} LlamadaFuncion;

static inline struct LlamadaFuncion LlamadaFuncion_nuevo() {
    struct LlamadaFuncion _r = {0};
    return _r;
}

typedef struct ExprAccesoCampo {
    CadenaSegura tipo;
    struct Nodo* objeto;
    CadenaSegura nombre_campo;
} ExprAccesoCampo;

static inline struct ExprAccesoCampo ExprAccesoCampo_nuevo() {
    struct ExprAccesoCampo _r = {0};
    return _r;
}

typedef struct AsignacionVariable {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct Nodo* expresion;
} AsignacionVariable;

static inline struct AsignacionVariable AsignacionVariable_nuevo() {
    struct AsignacionVariable _r = {0};
    return _r;
}

typedef struct AsignacionCampo {
    CadenaSegura tipo;
    struct Nodo* objeto;
    CadenaSegura nombre_campo;
    struct Nodo* expresion;
} AsignacionCampo;

static inline struct AsignacionCampo AsignacionCampo_nuevo() {
    struct AsignacionCampo _r = {0};
    return _r;
}

typedef struct SentenciaSi {
    CadenaSegura tipo;
    struct Nodo* condicion;
    struct ListaNodo* cuerpo;
    struct ListaNodo* cuerpo_sino;
} SentenciaSi;

static inline struct SentenciaSi SentenciaSi_nuevo() {
    struct SentenciaSi _r = {0};
    return _r;
}

typedef struct SentenciaMientras {
    CadenaSegura tipo;
    struct Nodo* condicion;
    struct ListaNodo* cuerpo;
} SentenciaMientras;

static inline struct SentenciaMientras SentenciaMientras_nuevo() {
    struct SentenciaMientras _r = {0};
    return _r;
}

typedef struct SentenciaRetornar {
    CadenaSegura tipo;
    struct Nodo* expr;
} SentenciaRetornar;

static inline struct SentenciaRetornar SentenciaRetornar_nuevo() {
    struct SentenciaRetornar _r = {0};
    return _r;
}

typedef struct SentenciaExpr {
    CadenaSegura tipo;
    struct Nodo* expr;
} SentenciaExpr;

static inline struct SentenciaExpr SentenciaExpr_nuevo() {
    struct SentenciaExpr _r = {0};
    return _r;
}

typedef struct LogLlamada {
    CadenaSegura tipo;
    struct ListaNodo* argumentos;
} LogLlamada;

static inline struct LogLlamada LogLlamada_nuevo() {
    struct LogLlamada _r = {0};
    return _r;
}

typedef struct Parametro {
    CadenaSegura tipo;
    CadenaSegura nombre;
    CadenaSegura tipo_param;
    int es_transferencia;
} Parametro;

static inline struct Parametro Parametro_nuevo() {
    struct Parametro _r = {0};
    return _r;
}

typedef struct ListaParametro {
    struct Parametro* cabeza;
    struct ListaParametro* cola;
} ListaParametro;

static inline struct ListaParametro ListaParametro_nuevo() {
    struct ListaParametro _r = {0};
    return _r;
}

typedef struct DefinicionFuncion {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaParametro* parametros;
    CadenaSegura tipo_retorno;
    struct ListaNodo* cuerpo;
} DefinicionFuncion;

static inline struct DefinicionFuncion DefinicionFuncion_nuevo() {
    struct DefinicionFuncion _r = {0};
    return _r;
}

typedef struct DefinicionEstructura {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaParametro* campos;
} DefinicionEstructura;

static inline struct DefinicionEstructura DefinicionEstructura_nuevo() {
    struct DefinicionEstructura _r = {0};
    return _r;
}

typedef struct SentenciaRomper {
    CadenaSegura tipo;
} SentenciaRomper;

static inline struct SentenciaRomper SentenciaRomper_nuevo() {
    struct SentenciaRomper _r = {0};
    return _r;
}

typedef struct SentenciaSiguiente {
    CadenaSegura tipo;
} SentenciaSiguiente;

static inline struct SentenciaSiguiente SentenciaSiguiente_nuevo() {
    struct SentenciaSiguiente _r = {0};
    return _r;
}

typedef struct SentenciaLanzar {
    CadenaSegura tipo;
    struct Nodo* llamada;
} SentenciaLanzar;

static inline struct SentenciaLanzar SentenciaLanzar_nuevo() {
    struct SentenciaLanzar _r = {0};
    return _r;
}

typedef struct SentenciaRecuperar {
    CadenaSegura tipo;
    struct Nodo* accion_critica;
    struct Nodo* plan_b;
} SentenciaRecuperar;

static inline struct SentenciaRecuperar SentenciaRecuperar_nuevo() {
    struct SentenciaRecuperar _r = {0};
    return _r;
}

typedef struct SentenciaEscuchar {
    CadenaSegura tipo;
    struct Nodo* canal;
    struct Nodo* respuesta;
} SentenciaEscuchar;

static inline struct SentenciaEscuchar SentenciaEscuchar_nuevo() {
    struct SentenciaEscuchar _r = {0};
    return _r;
}

typedef struct ExprTensor {
    CadenaSegura tipo;
    struct Nodo* filas;
    struct Nodo* columnas;
} ExprTensor;

static inline struct ExprTensor ExprTensor_nuevo() {
    struct ExprTensor _r = {0};
    return _r;
}

typedef struct ExprIndice {
    CadenaSegura tipo;
    struct Nodo* expr;
    struct Nodo* indice;
} ExprIndice;

static inline struct ExprIndice ExprIndice_nuevo() {
    struct ExprIndice _r = {0};
    return _r;
}

typedef struct ArgumentoTransferido {
    CadenaSegura tipo;
    struct Nodo* expr;
} ArgumentoTransferido;

static inline struct ArgumentoTransferido ArgumentoTransferido_nuevo() {
    struct ArgumentoTransferido _r = {0};
    return _r;
}

typedef struct SentenciaImportar {
    CadenaSegura tipo;
    CadenaSegura ruta;
} SentenciaImportar;

static inline struct SentenciaImportar SentenciaImportar_nuevo() {
    struct SentenciaImportar _r = {0};
    return _r;
}

typedef struct BloqueInseguro {
    CadenaSegura tipo;
    struct ListaNodo* cuerpo;
} BloqueInseguro;

static inline struct BloqueInseguro BloqueInseguro_nuevo() {
    struct BloqueInseguro _r = {0};
    return _r;
}

typedef struct ExprObtenerDireccion {
    CadenaSegura tipo;
    struct Nodo* expr;
} ExprObtenerDireccion;

static inline struct ExprObtenerDireccion ExprObtenerDireccion_nuevo() {
    struct ExprObtenerDireccion _r = {0};
    return _r;
}

typedef struct ExprDereferencia {
    CadenaSegura tipo;
    struct Nodo* expr;
} ExprDereferencia;

static inline struct ExprDereferencia ExprDereferencia_nuevo() {
    struct ExprDereferencia _r = {0};
    return _r;
}

typedef struct ImportarC {
    CadenaSegura tipo;
    CadenaSegura ruta;
    int es_sistema;
} ImportarC;

static inline struct ImportarC ImportarC_nuevo() {
    struct ImportarC _r = {0};
    return _r;
}

typedef struct DeclaracionExterna {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaParametro* parametros;
    CadenaSegura tipo_retorno;
} DeclaracionExterna;

static inline struct DeclaracionExterna DeclaracionExterna_nuevo() {
    struct DeclaracionExterna _r = {0};
    return _r;
}

int tokenizar(CadenaSegura fuente) {
    int _i = 0;
    int _linea = 1;
    int _columna = 1;
    int _token_count = 0;
    while (_i < fuente.longitud) {
        char _c = fuente.datos[_i];
        if (_c == ' ' || _c == '\t') { _i++; _columna++; continue; }
        if (_c == '\r') { _i++; continue; }
        if (_c == '\n') { _i++; _linea++; _columna = 1; continue; }
        if (_c == '/' && _i + 1 < fuente.longitud && fuente.datos[_i + 1] == '/') {
            while (_i < fuente.longitud && fuente.datos[_i] != '\n') { _i++; }
            continue;
        }
        if (_c == '"' || _c == '\'') {
            char _q = _c; int _start = _i; _i++; _columna++;
            while (_i < fuente.longitud && fuente.datos[_i] != _q) { _i++; _columna++; }
            if (_i >= fuente.longitud) {
                fprintf(stderr, "  TOKEN STRING_UNCLOSED L%d:%d\n", _linea, _columna);
                break;
            }
            _i++; _columna++;
            _token_count++;
            fprintf(stderr, "  TOKEN STRING L%d:%d\n", _linea, _columna);
        }
        else if (_c >= '0' && _c <= '9') {
            int _start = _i;
            while (_i < fuente.longitud && fuente.datos[_i] >= '0' && fuente.datos[_i] <= '9') { _i++; }
            _columna += _i - _start;
            _token_count++;
            fprintf(stderr, "  TOKEN NUMBER L%d:%d\n", _linea, _columna);
        }
        else if ((_c >= 'a' && _c <= 'z') || (_c >= 'A' && _c <= 'Z') || _c == '_') {
            int _start = _i;
            while (_i < fuente.longitud && (
                (fuente.datos[_i] >= 'a' && fuente.datos[_i] <= 'z') ||
                (fuente.datos[_i] >= 'A' && fuente.datos[_i] <= 'Z') ||
                (fuente.datos[_i] >= '0' && fuente.datos[_i] <= '9') ||
                fuente.datos[_i] == '_'
            )) { _i++; }
            int _len_id = _i - _start;
            char _buf_id[256]; int _clip = _len_id < 255 ? _len_id : 255;
            strncpy(_buf_id, fuente.datos + _start, _clip); _buf_id[_clip] = 0;
            _columna += _len_id;
            _token_count++;
            typedef struct { const char* p; int t; } _KWE;
            static const _KWE _kws[] = {
                {"si",1},{"if",1},{"se",1},{"wenn",1},
                {"sino",2},{"else",2},{"sinon",2},{"senao",2},{"sonst",2},{"altrimenti",2},
                {"funcion",3},{"function",3},{"fonction",3},{"funcao",3},{"funktion",3},{"funzione",3},
                {"retornar",4},{"return",4},{"retourner",4},{"rueckgabe",4},{"restituisci",4},
                {"lanzar",5},{"spawn",5},{"lancer",5},{"lancar",5},{"starten",5},{"lancia",5},
                {"recuperar",6},{"recover",6},{"recuperer",6},{"wiederherstellen",6},{"recupera",6},
                {"escuchar",7},{"listen",7},{"ecouter",7},{"escutar",7},{"hoeren",7},{"ascolta",7},
                {"mientras",8},{"while",8},{"tantque",8},{"enquanto",8},{"waehrend",8},{"mentre",8},
                {"importar",9},{"import",9},{"importer",9},{"importieren",9},{"importa",9},
                {"romper",10},{"break",10},{"rompre",10},{"parar",10},{"abbrechen",10},{"interrompi",10},
                {"siguiente",11},{"continue",11},{"continuer",11},{"continuar",11},{"fortsetzen",11},{"continua",11},
                {"estructura",37},{"struct",37},{"structure",37},{"estrutura",37},{"struktur",37},{"struttura",37},
                {"y",38},{"and",38},{"et",38},{"e",38},{"und",38},
                {"o",39},{"or",39},{"ou",39},{"oder",39},
                {"no",40},{"not",40},{"non",40},{"nao",40},{"nicht",40},
                {"verdadero",41},{"true",41},{"vrai",41},{"verdadeiro",41},{"wahr",41},{"vero",41},
                {"falso",42},{"false",42},{"faux",42},{"falsch",42},
                {"inseguro",43},{"unsafe",43},
                {"importar_c",44},{"import_c",44},{"importer_c",44},{"importa_c",44},
                {"externo",46},{"extern",46},{"externe",46},{"esterno",46},
                {NULL,0}
            };
            int _kt = 0;
            for (int _ki = 0; _kws[_ki].p; _ki++) {
                if (strcmp(_buf_id, _kws[_ki].p) == 0) { _kt = _kws[_ki].t; break; }
            }
            if (_kt)
                fprintf(stderr, "  TOKEN %d L%d:%d\n", _kt, _linea, _columna);
            else
                fprintf(stderr, "  TOKEN IDENTIFIER L%d:%d\n", _linea, _columna);
        }
        else {
            _i++; _columna++;
            _token_count++;
            fprintf(stderr, "  TOKEN CHAR(%c) L%d:%d\n", _c, _linea, _columna);
        }
    }
    fprintf(stderr, "Total tokens: %d\n", _token_count);
    return _token_count;
}

// --- Token IDs ---
#define T_IF 1
#define T_ELSE 2
#define T_FUNC 3
#define T_RET 4
#define T_SPAWN 5
#define T_RECOVER 6
#define T_LISTEN 7
#define T_WHILE 8
#define T_IMPORT 9
#define T_BREAK 10
#define T_CONTINUE 11
#define T_DOT 12
#define T_IDENT 13
#define T_NUM 14
#define T_STR 15
#define T_GT 16
#define T_LT 17
#define T_EQ 18
#define T_NE 19
#define T_LE 20
#define T_GE 21
#define T_ASSIGN 22
#define T_PLUS 23
#define T_MINUS 24
#define T_MUL 25
#define T_DIV 26
#define T_MOD 27
#define T_ARROW 28
#define T_LPAREN 29
#define T_RPAREN 30
#define T_COLON 31
#define T_COMMA 32
#define T_NL 33
#define T_INDENT 34
#define T_DEDENT 35
#define T_EOF 36
#define T_STRUCT 37
#define T_AND 38
#define T_OR 39
#define T_NOT 40
#define T_TRUE 41
#define T_FALSE 42
#define T_INSEGURO 43
#define T_IMPORTAR_C 44
#define T_AMPERSAND 45
#define T_EXTERNO 46

#define MAX_TOKS 16384
typedef struct { int tipo; int linea; int col; char val[256]; } _P_Token;
static _P_Token _P_tks[MAX_TOKS];
static int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;
static int _P_pila_indent[64], _P_nivel_pila = 0;

static void _P_tokenizar(const char* s, int len) {
    int i = 0, li = 1, co = 1;
    while (i < len && _P_ntks < MAX_TOKS - 1) {
        char c = s[i];
        if (c == ' ' || c == '\t') { i++; co++; continue; }
        if (c == '\r') { i++; continue; }
        if (c == '\n') {
            _P_tks[_P_ntks].tipo = T_NL; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = 0;
            _P_ntks++; i++; li++; co = 1;
            while (i < len && (s[i]==' '||s[i]=='\t')) { if(s[i]==' ')co++; else co+=4; i++; }
            if (i < len && s[i]=='\n') continue;
            if (i < len && s[i]=='#') { while(i<len&&s[i]!='\n')i++; continue; }
            if (i < len && s[i]=='/' && i+1<len && s[i+1]=='/') { while(i<len&&s[i]!='\n')i++; continue; }
            { int _sp = co-1;
            if (_sp > _P_pila_indent[_P_nivel_pila]) {
                _P_nivel_pila++; _P_pila_indent[_P_nivel_pila] = _sp;
                _P_tks[_P_ntks].tipo = T_INDENT; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = 0;
                _P_ntks++;
            } else if (_sp < _P_pila_indent[_P_nivel_pila]) {
                while (_P_nivel_pila > 0 && _sp < _P_pila_indent[_P_nivel_pila]) {
                    _P_tks[_P_ntks].tipo = T_DEDENT; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = 0;
                    _P_ntks++; _P_nivel_pila--;
                }
            } }
            continue;
        }
        if (c == '/' && i+1 < len && s[i+1] == '/') {
            while (i < len && s[i] != '\n') i++; continue;
        }
        if (c == '#') {
            while (i < len && s[i] != '\n') i++; continue;
        }
        if (c == '"' || c == '\'') {
            char q = c; int st = i; int scol = co; i++; co++;
            while (i < len && s[i] != q) { i++; co++; }
            if (i >= len) break;
            i++; co++;
            int vl = (i - st - 2) < 255 ? (i - st - 2) : 255;
            strncpy(_P_tks[_P_ntks].val, s + st + 1, vl); _P_tks[_P_ntks].val[vl] = 0;
            _P_tks[_P_ntks].tipo = T_STR; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = scol;
            _P_ntks++; continue;
        }
        if (c >= '0' && c <= '9') {
            int st = i; int scol = co; while (i < len && s[i] >= '0' && s[i] <= '9') i++;
            if (i < len && s[i] == '.') { i++; while (i < len && s[i] >= '0' && s[i] <= '9') i++; }
            int vl = (i - st) < 255 ? (i - st) : 255;
            strncpy(_P_tks[_P_ntks].val, s + st, vl); _P_tks[_P_ntks].val[vl] = 0;
            _P_tks[_P_ntks].tipo = T_NUM; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = scol;
            _P_ntks++; co += (i - st); continue;
        }
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_') {
            int st = i; int scol = co;
            while (i < len && ((s[i] >= 'a' && s[i] <= 'z') || (s[i] >= 'A' && s[i] <= 'Z') || (s[i] >= '0' && s[i] <= '9') || s[i] == '_')) i++;
            int vl = (i - st) < 255 ? (i - st) : 255;
            strncpy(_P_tks[_P_ntks].val, s + st, vl); _P_tks[_P_ntks].val[vl] = 0;
            _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = scol;
            typedef struct { const char* p; int t; } _KW;
            static const _KW _ks[] = {
                {"si",T_IF},{"if",T_IF},{"se",T_IF},{"wenn",T_IF},
                {"sino",T_ELSE},{"else",T_ELSE},{"sinon",T_ELSE},{"senao",T_ELSE},{"sonst",T_ELSE},{"altrimenti",T_ELSE},
                {"funcion",T_FUNC},{"function",T_FUNC},{"fonction",T_FUNC},{"funcao",T_FUNC},{"funktion",T_FUNC},{"funzione",T_FUNC},
                {"retornar",T_RET},{"return",T_RET},{"retourner",T_RET},{"retornar",T_RET},{"rueckgabe",T_RET},{"restituisci",T_RET},
                {"lanzar",T_SPAWN},{"spawn",T_SPAWN},{"lancer",T_SPAWN},{"lancar",T_SPAWN},{"starten",T_SPAWN},{"lancia",T_SPAWN},
                {"recuperar",T_RECOVER},{"recover",T_RECOVER},{"recuperer",T_RECOVER},{"recuperar",T_RECOVER},{"wiederherstellen",T_RECOVER},{"recupera",T_RECOVER},
                {"escuchar",T_LISTEN},{"listen",T_LISTEN},{"ecouter",T_LISTEN},{"escutar",T_LISTEN},{"hoeren",T_LISTEN},{"ascolta",T_LISTEN},
                {"mientras",T_WHILE},{"while",T_WHILE},{"tantque",T_WHILE},{"enquanto",T_WHILE},{"waehrend",T_WHILE},{"mentre",T_WHILE},
                {"importar",T_IMPORT},{"import",T_IMPORT},{"importer",T_IMPORT},{"importar",T_IMPORT},{"importieren",T_IMPORT},{"importa",T_IMPORT},
                {"romper",T_BREAK},{"break",T_BREAK},{"rompre",T_BREAK},{"parar",T_BREAK},{"abbrechen",T_BREAK},{"interrompi",T_BREAK},
                {"siguiente",T_CONTINUE},{"continue",T_CONTINUE},{"continuer",T_CONTINUE},{"continuar",T_CONTINUE},{"fortsetzen",T_CONTINUE},{"continua",T_CONTINUE},
                {"estructura",T_STRUCT},{"struct",T_STRUCT},{"structure",T_STRUCT},{"estrutura",T_STRUCT},{"struktur",T_STRUCT},{"struttura",T_STRUCT},
                {"y",T_AND},{"and",T_AND},{"et",T_AND},{"e",T_AND},{"und",T_AND},
                {"o",T_OR},{"or",T_OR},{"ou",T_OR},{"oder",T_OR},
                {"no",T_NOT},{"not",T_NOT},{"non",T_NOT},{"nao",T_NOT},{"nicht",T_NOT},
                {"verdadero",T_TRUE},{"true",T_TRUE},{"vrai",T_TRUE},{"verdadeiro",T_TRUE},{"wahr",T_TRUE},{"vero",T_TRUE},
                {"falso",T_FALSE},{"false",T_FALSE},{"faux",T_FALSE},{"falsch",T_FALSE},
                {"inseguro",T_INSEGURO},{"unsafe",T_INSEGURO},
                {"importar_c",T_IMPORTAR_C},{"import_c",T_IMPORTAR_C},{"importer_c",T_IMPORTAR_C},{"importa_c",T_IMPORTAR_C},
                {"externo",T_EXTERNO},{"extern",T_EXTERNO},{"externe",T_EXTERNO},{"esterno",T_EXTERNO},
                {NULL,0}
            };
            int _kt = T_IDENT;
            for (int _ki = 0; _ks[_ki].p; _ki++) {
                if (strcmp(_P_tks[_P_ntks].val, _ks[_ki].p) == 0) { _kt = _ks[_ki].t; break; }
            }
            _P_tks[_P_ntks].tipo = _kt;
            _P_ntks++; co += (i - st); continue;
        }
        if ((unsigned char)c >= 0x80) { i++; continue; }
        if (i+1 < len) {
            if (c == '-' && s[i+1] == '>') {
                _P_tks[_P_ntks].tipo = T_ARROW; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
                _P_ntks++; i+=2; co+=2; continue;
            }
            if (c == '=' && s[i+1] == '=') {
                _P_tks[_P_ntks].tipo = T_EQ; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
                _P_ntks++; i+=2; co+=2; continue;
            }
            if (c == '!' && s[i+1] == '=') {
                _P_tks[_P_ntks].tipo = T_NE; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
                _P_ntks++; i+=2; co+=2; continue;
            }
            if (c == '<' && s[i+1] == '=') {
                _P_tks[_P_ntks].tipo = T_LE; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
                _P_ntks++; i+=2; co+=2; continue;
            }
            if (c == '>' && s[i+1] == '=') {
                _P_tks[_P_ntks].tipo = T_GE; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
                _P_ntks++; i+=2; co+=2; continue;
            }
        }
        {
            int tt = T_EOF;
            if (c == '=') tt = T_ASSIGN;
            else if (c == '+') tt = T_PLUS;
            else if (c == '-') tt = T_MINUS;
            else if (c == '*') tt = T_MUL;
            else if (c == '/') tt = T_DIV;
            else if (c == '%') tt = T_MOD;
            else if (c == '(') tt = T_LPAREN;
            else if (c == ')') tt = T_RPAREN;
            else if (c == ':') tt = T_COLON;
            else if (c == ',') tt = T_COMMA;
            else if (c == '.') tt = T_DOT;
            else if (c == '>') tt = T_GT;
            else if (c == '<') tt = T_LT;
            else if (c == '&') tt = T_AMPERSAND;
            if (tt == T_EOF) { fprintf(stderr,"Error Lexico: caracter inesperado '%%c'(%%d) en linea %%d\n",c,c,li); exit(1); }
            _P_tks[_P_ntks].tipo = tt; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
            _P_ntks++; i++; co++;
        }
    }
    while (_P_nivel_pila > 0) {
        _P_tks[_P_ntks].tipo = T_DEDENT; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = 0;
        _P_ntks++; _P_nivel_pila--;
    }
    _P_tks[_P_ntks].tipo = T_EOF; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = 0;
    _P_ntks++;
}

static void _P_procesar_indentacion_final() {
    while (_P_nivel_pila > 0) {
        _P_tks[_P_ntks].tipo = T_DEDENT; _P_tks[_P_ntks].linea = _P_tks[_P_ntks-1].linea; _P_tks[_P_ntks].col = 0;
        _P_ntks++; _P_nivel_pila--;
    }
}

// --- AST builder helpers ---
static CadenaSegura _P_cs(const char* s) {
    CadenaSegura c; c.longitud = (int)strlen(s);
    char* d = (char*)malloc(c.longitud + 1); strcpy(d, s); c.datos = d; return c;
}
static struct ListaNodo* _P_mk_list(struct Nodo* h, struct ListaNodo* t) {
    struct ListaNodo* n = (struct ListaNodo*)calloc(1,sizeof(struct ListaNodo));
    n->cabeza = h; n->cola = t; return n;
}

static _P_Token* _P_mirar() { return &_P_tks[_P_tpos]; }
static void _P_avanzar() { if (_P_tpos < _P_ntks) _P_tpos++; }
static int _P_posible(int t) { return _P_mirar()->tipo == t ? 1 : 0; }
static int _P_esperar(int t) {
    if (_P_mirar()->tipo == t) { _P_avanzar(); return 1; }
    fprintf(stderr, "[PARSER] L%d:%d: esperaba token %d, encontre %d\n",
            _P_mirar()->linea, _P_mirar()->col, t, _P_mirar()->tipo);
    exit(1);
}
static void _P_sinc_skip() {
    while (_P_tpos < _P_ntks) {
        int tt = _P_mirar()->tipo;
        if (tt == T_NL || tt == T_DEDENT || tt == T_EOF || tt == T_COMMA || tt == T_RPAREN || tt == T_COLON) break;
        _P_avanzar();
    }
}

// Forward declarations
static struct Nodo* _P_expr();
static struct Nodo* _P_logica();
static struct ListaNodo* _P_bloque();
static struct Nodo* _P_sentencia();
static struct Nodo* _P_comp();
static struct Nodo* _P_suma();
static struct Nodo* _P_term();
static struct Nodo* _P_una();
static struct Nodo* _P_prim();
static struct Programa _P_programa();
static struct ListaNodo* _P_bloque() {
    if (!_P_esperar(T_NL)) { _P_sinc_skip(); return NULL; }
    while (_P_mirar()->tipo == T_NL) { _P_avanzar(); }
    if (!_P_esperar(T_INDENT)) { _P_sinc_skip(); return NULL; }
    struct ListaNodo* lst = NULL;
    struct ListaNodo** cur = &lst;
    while (_P_mirar()->tipo != T_DEDENT && _P_mirar()->tipo != T_EOF) {
        if (_P_mirar()->tipo == T_NL) { _P_avanzar(); continue; }
        struct Nodo* st=_P_sentencia();
        if (st) { *cur=_P_mk_list(st,NULL); cur=&(*cur)->cola; }
    }
    _P_esperar(T_DEDENT);
    return lst;
}
static struct Nodo* _P_sentencia() {
    while (_P_mirar()->tipo == T_NL) { _P_avanzar(); }
    _P_Token* t = _P_mirar();
    if (t->tipo == T_FUNC) {
        _P_avanzar();
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _nm[256]; strcpy(_nm, _P_mirar()->val);
        _P_avanzar();
        _P_esperar(T_LPAREN);
        struct ListaNodo* params = NULL;
        struct ListaNodo** pcur = &params;
        if (_P_mirar()->tipo != T_RPAREN) {
            while (1) {
                int is_transfer = 0;
                if (_P_mirar()->tipo == T_ARROW) { is_transfer=1; _P_avanzar(); }
                if (_P_mirar()->tipo != T_IDENT) break;
                char _pn[256]; strcpy(_pn, _P_mirar()->val);
                _P_avanzar();
                _P_esperar(T_COLON);
                if (_P_mirar()->tipo != T_IDENT) break;
                char _pt[256]; strcpy(_pt, _P_mirar()->val);
                _P_avanzar();
                while (_P_mirar()->tipo == T_MUL) { strcat(_pt,"*"); _P_avanzar(); }
                struct Parametro* pp = (struct Parametro*)calloc(1,sizeof(struct Parametro));
                pp->tipo=_P_cs("Parametro");
                pp->nombre=_P_cs(_pn); pp->tipo_param=_P_cs(_pt);
                pp->es_transferencia = is_transfer;
                *pcur=_P_mk_list((struct Nodo*)pp,NULL); pcur=&(*pcur)->cola;
                if (_P_mirar()->tipo != T_COMMA) break;
                _P_avanzar();
            }
        }
        _P_esperar(T_RPAREN); _P_esperar(T_ARROW);
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _rt[256]; strcpy(_rt, _P_mirar()->val);
        _P_avanzar();
        _P_esperar(T_COLON);
        struct ListaNodo* body=_P_bloque();
        struct DefinicionFuncion* n = (struct DefinicionFuncion*)calloc(1,sizeof(struct DefinicionFuncion));
        n->tipo=_P_cs("DefinicionFuncion");
        n->nombre=_P_cs(_nm); n->parametros=(struct ListaParametro*)params;
        n->tipo_retorno=_P_cs(_rt); n->cuerpo=body;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_STRUCT) {
        _P_avanzar();
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _snm[256]; strcpy(_snm, _P_mirar()->val);
        _P_avanzar();
        _P_esperar(T_COLON);
        if (!_P_esperar(T_NL)) { _P_sinc_skip(); return NULL; }
        while (_P_mirar()->tipo == T_NL) { _P_avanzar(); }
        if (!_P_esperar(T_INDENT)) { _P_sinc_skip(); return NULL; }
        struct ListaParametro* campos = NULL;
        struct ListaParametro** ccur = &campos;
        while (_P_mirar()->tipo != T_DEDENT && _P_mirar()->tipo != T_EOF) {
            if (_P_mirar()->tipo == T_NL) { _P_avanzar(); continue; }
            if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); break; }
            char _pn[256]; strcpy(_pn, _P_mirar()->val);
            _P_avanzar();
            _P_esperar(T_COLON);
            if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); break; }
            char _pt[256]; strcpy(_pt, _P_mirar()->val);
            _P_avanzar();
            struct Parametro* pp=(struct Parametro*)calloc(1,sizeof(struct Parametro));
            pp->tipo=_P_cs("Parametro"); pp->nombre=_P_cs(_pn); pp->tipo_param=_P_cs(_pt); pp->es_transferencia=0;
            *ccur=(struct ListaParametro*)_P_mk_list((struct Nodo*)pp,NULL); ccur=&(*ccur)->cola;
        }
        _P_esperar(T_DEDENT);
        struct DefinicionEstructura* n = (struct DefinicionEstructura*)calloc(1,sizeof(struct DefinicionEstructura));
        n->tipo=_P_cs("DefinicionEstructura"); n->nombre=_P_cs(_snm); n->campos=campos;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IF) {
        _P_avanzar();
        struct Nodo* cond=_P_expr();
        _P_esperar(T_COLON);
        struct ListaNodo* cpo=_P_bloque();
        struct ListaNodo* sino = NULL;
        if (_P_mirar()->tipo == T_ELSE) { _P_avanzar(); _P_esperar(T_COLON); sino=_P_bloque(); }
        struct SentenciaSi* n = (struct SentenciaSi*)calloc(1,sizeof(struct SentenciaSi));
        n->tipo=_P_cs("SentenciaSi"); n->condicion=cond;
        n->cuerpo=cpo; n->cuerpo_sino=sino;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_WHILE) {
        _P_avanzar();
        struct Nodo* cond=_P_expr();
        _P_esperar(T_COLON);
        struct ListaNodo* cpo=_P_bloque();
        struct SentenciaMientras* n = (struct SentenciaMientras*)calloc(1,sizeof(struct SentenciaMientras));
        n->tipo=_P_cs("SentenciaMientras"); n->condicion=cond; n->cuerpo=cpo;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_RET) {
        _P_avanzar();
        struct Nodo* expr = NULL;
        if (_P_mirar()->tipo == T_ARROW) { _P_avanzar(); expr=_P_expr(); }
        else if (_P_mirar()->tipo != T_NL && _P_mirar()->tipo != T_DEDENT && _P_mirar()->tipo != T_EOF) { expr=_P_expr(); }
        struct SentenciaRetornar* n = (struct SentenciaRetornar*)calloc(1,sizeof(struct SentenciaRetornar));
        n->tipo=_P_cs("SentenciaRetornar"); n->expr=expr;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_SPAWN) { _P_avanzar();
        struct Nodo* ll=_P_expr();
        struct SentenciaLanzar* n = (struct SentenciaLanzar*)calloc(1,sizeof(struct SentenciaLanzar));
        n->tipo=_P_cs("SentenciaLanzar"); n->llamada=ll;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_RECOVER) { _P_avanzar();
        struct Nodo* ac=_P_expr(); _P_esperar(T_COLON);
        struct Nodo* pb=_P_expr();
        struct SentenciaRecuperar* n = (struct SentenciaRecuperar*)calloc(1,sizeof(struct SentenciaRecuperar));
        n->tipo=_P_cs("SentenciaRecuperar"); n->accion_critica=ac; n->plan_b=pb;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_LISTEN) { _P_avanzar();
        struct Nodo* cn=_P_expr(); _P_esperar(T_ARROW);
        struct Nodo* rp=_P_expr();
        struct SentenciaEscuchar* n = (struct SentenciaEscuchar*)calloc(1,sizeof(struct SentenciaEscuchar));
        n->tipo=_P_cs("SentenciaEscuchar"); n->canal=cn; n->respuesta=rp;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_BREAK) { _P_avanzar();
        struct SentenciaRomper* n = (struct SentenciaRomper*)calloc(1,sizeof(struct SentenciaRomper));
        n->tipo=_P_cs("SentenciaRomper");
        return (struct Nodo*)n;
    }
    if (t->tipo == T_CONTINUE) { _P_avanzar();
        struct SentenciaSiguiente* n = (struct SentenciaSiguiente*)calloc(1,sizeof(struct SentenciaSiguiente));
        n->tipo=_P_cs("SentenciaSiguiente");
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IMPORT) { _P_avanzar();
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _imp[256]; strcpy(_imp, _P_mirar()->val); int _iml = (int)strlen(_imp);
        _P_avanzar();
        while (_P_mirar()->tipo == T_DOT) { _P_avanzar(); if (_P_mirar()->tipo != T_IDENT) break; strcat(_imp,"."); strcat(_imp,_P_mirar()->val); _P_avanzar(); }
        struct SentenciaImportar* n = (struct SentenciaImportar*)calloc(1,sizeof(struct SentenciaImportar));
        n->tipo=_P_cs("SentenciaImportar"); n->ruta=_P_cs(_imp);
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IMPORTAR_C) { _P_avanzar();
        if (_P_mirar()->tipo != T_STR) { _P_sinc_skip(); return NULL; }
        char _hc[256]; strcpy(_hc, _P_mirar()->val);
        int _hsys = (_hc[0]=='<' && _hc[strlen(_hc)-1]=='>');
        if(_hsys){{ memmove(_hc,_hc+1,strlen(_hc)-2); _hc[strlen(_hc)-2]=0; }}
        _P_avanzar();
        struct ImportarC* n = (struct ImportarC*)calloc(1,sizeof(struct ImportarC));
        n->tipo=_P_cs("ImportarC"); n->ruta=_P_cs(_hc); n->es_sistema=_hsys;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_EXTERNO) { _P_avanzar();
        if (_P_mirar()->tipo != T_FUNC) { _P_sinc_skip(); return NULL; }
        _P_avanzar();
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _enm[256]; strcpy(_enm, _P_mirar()->val);
        _P_avanzar();
        _P_esperar(T_LPAREN);
        struct ListaParametro* eparams = NULL;
        struct ListaParametro** epcur = &eparams;
        if (_P_mirar()->tipo != T_RPAREN) {
            while (1) {
                if (_P_mirar()->tipo != T_IDENT) break;
                char _epn[256]; strcpy(_epn, _P_mirar()->val);
                _P_avanzar();
                _P_esperar(T_COLON);
                if (_P_mirar()->tipo != T_IDENT) break;
                char _ept[256]; strcpy(_ept, _P_mirar()->val);
                _P_avanzar();
                while (_P_mirar()->tipo == T_MUL) { strcat(_ept,"*"); _P_avanzar(); }
                struct Parametro* epp=(struct Parametro*)calloc(1,sizeof(struct Parametro));
                epp->tipo=_P_cs("Parametro"); epp->nombre=_P_cs(_epn); epp->tipo_param=_P_cs(_ept); epp->es_transferencia=0;
                *epcur=(struct ListaParametro*)_P_mk_list((struct Nodo*)epp,NULL); epcur=&(*epcur)->cola;
                if (_P_mirar()->tipo != T_COMMA) break;
                _P_avanzar();
            }
        }
        _P_esperar(T_RPAREN); _P_esperar(T_ARROW);
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _ert[256]; strcpy(_ert, _P_mirar()->val);
        _P_avanzar();
        struct DeclaracionExterna* n = (struct DeclaracionExterna*)calloc(1,sizeof(struct DeclaracionExterna));
        n->tipo=_P_cs("DeclaracionExterna"); n->nombre=_P_cs(_enm);
        n->parametros=eparams; n->tipo_retorno=_P_cs(_ert);
        return (struct Nodo*)n;
    }
    if (t->tipo == T_INSEGURO) { _P_avanzar();
        _P_esperar(T_COLON);
        struct ListaNodo* cpo=_P_bloque();
        struct BloqueInseguro* n = (struct BloqueInseguro*)calloc(1,sizeof(struct BloqueInseguro));
        n->tipo=_P_cs("BloqueInseguro"); n->cuerpo=cpo;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IDENT && _P_tpos + 1 < _P_ntks && _P_tks[_P_tpos + 1].tipo == T_ASSIGN) {
        char _vn[256]; strcpy(_vn, t->val);
        _P_avanzar(); _P_avanzar();
        struct Nodo* val=_P_expr();
        struct AsignacionVariable* n = (struct AsignacionVariable*)calloc(1,sizeof(struct AsignacionVariable));
        n->tipo=_P_cs("AsignacionVariable");
        n->nombre=_P_cs(_vn); n->expresion=val;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IDENT && _P_tpos + 1 < _P_ntks && _P_tks[_P_tpos + 1].tipo == T_DOT) {
        char _vn[256]; strcpy(_vn, t->val);
        _P_avanzar(); _P_avanzar();
        if (_P_mirar()->tipo == T_IDENT) {
            char _cn[256]; strcpy(_cn, _P_mirar()->val);
            if (_P_tpos + 1 < _P_ntks && _P_tks[_P_tpos + 1].tipo == T_ASSIGN) {
                _P_avanzar(); _P_avanzar();
                struct Nodo* val=_P_expr();
                struct Identificador* obj = (struct Identificador*)calloc(1,sizeof(struct Identificador));
                obj->tipo=_P_cs("Identificador"); obj->nombre=_P_cs(_vn);
                struct AsignacionCampo* n = (struct AsignacionCampo*)calloc(1,sizeof(struct AsignacionCampo));
                n->tipo=_P_cs("AsignacionCampo");
                n->objeto=(struct Nodo*)obj; n->nombre_campo=_P_cs(_cn); n->expresion=val;
                return (struct Nodo*)n;
            }
        }
    }
    { struct Nodo* e=_P_expr();
        struct SentenciaExpr* n = (struct SentenciaExpr*)calloc(1,sizeof(struct SentenciaExpr));
        n->tipo=_P_cs("SentenciaExpr"); n->expr=e;
        return (struct Nodo*)n;
    }
}
static struct Nodo* _P_expr() { return _P_logica(); }

static struct Nodo* _P_logica() {
    struct Nodo* izq=_P_comp();
    while (1) {
        int tt=_P_mirar()->tipo;
        if (tt!=T_AND&&tt!=T_OR) break;
        _P_avanzar();
        struct Nodo* der=_P_comp();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=_P_cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=_P_cs(tt==T_AND?"&&":"||");
        izq=(struct Nodo*)n;
    }
    return izq;
}

static struct Nodo* _P_comp() {
    struct Nodo* izq=_P_suma();
    while (1) {
        int tt=_P_mirar()->tipo;
        if (tt!=T_EQ&&tt!=T_NE&&tt!=T_LT&&tt!=T_GT&&tt!=T_LE&&tt!=T_GE) break;
        _P_avanzar();
        struct Nodo* der=_P_suma();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=_P_cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        {char _b[4]={0,0,0,0};if(tt==T_EQ){_b[0]='=';_b[1]='=';}
        else if(tt==T_NE){_b[0]='!';_b[1]='=';}
        else if(tt==T_LE){_b[0]='<';_b[1]='=';}
        else if(tt==T_GE){_b[0]='>';_b[1]='=';}
        else if(tt==T_LT){_b[0]='<';}else{_b[0]='>';}
        n->operador->lexema=_P_cs(_b);}
        izq=(struct Nodo*)n;
    }
    return izq;
}
static struct Nodo* _P_suma() {
    struct Nodo* izq=_P_term();
    while (_P_mirar()->tipo==T_PLUS||_P_mirar()->tipo==T_MINUS) {
        int tt=_P_mirar()->tipo; _P_avanzar();
        struct Nodo* der=_P_term();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=_P_cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=_P_cs(tt==T_PLUS?"+":"-");
        izq=(struct Nodo*)n;
    }
    return izq;
}
static struct Nodo* _P_term() {
    struct Nodo* izq=_P_una();
    while (_P_mirar()->tipo==T_MUL||_P_mirar()->tipo==T_DIV||_P_mirar()->tipo==T_MOD) {
        int tt=_P_mirar()->tipo; _P_avanzar();
        struct Nodo* der=_P_una();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=_P_cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=_P_cs(tt==T_MUL?"*":tt==T_DIV?"/":"%");
        izq=(struct Nodo*)n;
    }
    return izq;
}
static struct Nodo* _P_una() {
    if (_P_mirar()->tipo==T_MINUS||_P_mirar()->tipo==T_PLUS) {
        int tt=_P_mirar()->tipo; _P_avanzar();
        struct Nodo* e=_P_una();
        struct OpUnaria* n=(struct OpUnaria*)calloc(1,sizeof(struct OpUnaria));
        n->tipo=_P_cs("OpUnaria"); n->expr=e;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=_P_cs(tt==T_PLUS?"+":"-");
        return (struct Nodo*)n;
    }
    if (_P_mirar()->tipo==T_NOT) {
        int tt=_P_mirar()->tipo; _P_avanzar();
        struct Nodo* e=_P_una();
        struct OpUnaria* n=(struct OpUnaria*)calloc(1,sizeof(struct OpUnaria));
        n->tipo=_P_cs("OpUnaria"); n->expr=e;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=_P_cs("!");
        return (struct Nodo*)n;
    }
    if (_P_mirar()->tipo==T_AMPERSAND) {
        _P_avanzar();
        struct Nodo* e=_P_una();
        struct ExprObtenerDireccion* n=(struct ExprObtenerDireccion*)calloc(1,sizeof(struct ExprObtenerDireccion));
        n->tipo=_P_cs("ExprObtenerDireccion"); n->expr=e;
        return (struct Nodo*)n;
    }
    if (_P_mirar()->tipo==T_MUL) {
        _P_avanzar();
        struct Nodo* e=_P_una();
        struct ExprDereferencia* n=(struct ExprDereferencia*)calloc(1,sizeof(struct ExprDereferencia));
        n->tipo=_P_cs("ExprDereferencia"); n->expr=e;
        return (struct Nodo*)n;
    }
    return _P_prim();
}
static struct Nodo* _P_prim() {
    _P_Token* t=_P_mirar();
    if (t->tipo==T_NUM) {
        struct LiteralNumero* n=(struct LiteralNumero*)calloc(1,sizeof(struct LiteralNumero));
        n->tipo=_P_cs("LiteralNumero"); n->valor=atoi(t->val);
        _P_avanzar(); return (struct Nodo*)n;
    }
    if (t->tipo==T_STR) {
        struct LiteralCadena* n=(struct LiteralCadena*)calloc(1,sizeof(struct LiteralCadena));
        n->tipo=_P_cs("LiteralCadena"); n->valor=_P_cs(t->val);
        _P_avanzar(); return (struct Nodo*)n;
    }
    if (t->tipo==T_TRUE) {
        _P_avanzar();
        struct LiteralNumero* n=(struct LiteralNumero*)calloc(1,sizeof(struct LiteralNumero));
        n->tipo=_P_cs("LiteralNumero"); n->valor=1;
        return (struct Nodo*)n;
    }
    if (t->tipo==T_FALSE) {
        _P_avanzar();
        struct LiteralNumero* n=(struct LiteralNumero*)calloc(1,sizeof(struct LiteralNumero));
        n->tipo=_P_cs("LiteralNumero"); n->valor=0;
        return (struct Nodo*)n;
    }
    if (t->tipo==T_IDENT) {
        char _nm[256]; strcpy(_nm, t->val);
        _P_avanzar();
        if (_P_mirar()->tipo==T_LPAREN) {
            _P_avanzar();
            struct ListaNodo* args=NULL; struct ListaNodo** acur=&args;
            if (_P_mirar()->tipo!=T_RPAREN) {
                while (1) {
                    if (_P_mirar()->tipo==T_ARROW) {
                        _P_avanzar();
                        struct Nodo* ae=_P_expr();
                        struct ArgumentoTransferido* at=(struct ArgumentoTransferido*)calloc(1,sizeof(struct ArgumentoTransferido));
                        at->tipo=_P_cs("ArgumentoTransferido"); at->expr=ae;
                        *acur=_P_mk_list((struct Nodo*)at,NULL);
                    } else { *acur=_P_mk_list(_P_expr(),NULL); }
                    acur=&(*acur)->cola;
                    if (_P_mirar()->tipo!=T_COMMA) break;
                    _P_avanzar();
                }
            }
            _P_esperar(T_RPAREN);
            if(strcmp(_nm,"log")==0) {
                struct LogLlamada* n=(struct LogLlamada*)calloc(1,sizeof(struct LogLlamada));
                n->tipo=_P_cs("LogLlamada"); n->argumentos=args;
                return (struct Nodo*)n;
            }
            struct LlamadaFuncion* n=(struct LlamadaFuncion*)calloc(1,sizeof(struct LlamadaFuncion));
            n->tipo=_P_cs("LlamadaFuncion"); n->nombre=_P_cs(_nm); n->argumentos=args;
            return (struct Nodo*)n;
        }
        if (_P_mirar()->tipo==T_DOT) {
            _P_avanzar();
            if (_P_mirar()->tipo==T_IDENT) {
                struct Identificador* obj=(struct Identificador*)calloc(1,sizeof(struct Identificador));
                obj->tipo=_P_cs("Identificador"); obj->nombre=_P_cs(_nm);
                strcpy(_nm, _P_mirar()->val); _P_avanzar();
                if (_P_mirar()->tipo==T_LPAREN) {
                    free(obj);
                    _P_avanzar();
                    struct ListaNodo* args=NULL; struct ListaNodo** acur=&args;
                    if (_P_mirar()->tipo!=T_RPAREN) {
                        while (1) {
                            if (_P_mirar()->tipo==T_ARROW) {
                                _P_avanzar();
                                struct Nodo* ae=_P_expr();
                                struct ArgumentoTransferido* at=(struct ArgumentoTransferido*)calloc(1,sizeof(struct ArgumentoTransferido));
                                at->tipo=_P_cs("ArgumentoTransferido"); at->expr=ae;
                                *acur=_P_mk_list((struct Nodo*)at,NULL);
                            } else { *acur=_P_mk_list(_P_expr(),NULL); }
                            acur=&(*acur)->cola;
                            if (_P_mirar()->tipo!=T_COMMA) break;
                            _P_avanzar();
                        }
                    }
                    _P_esperar(T_RPAREN);
                    struct LlamadaFuncion* n=(struct LlamadaFuncion*)calloc(1,sizeof(struct LlamadaFuncion));
                    n->tipo=_P_cs("LlamadaFuncion"); n->nombre=_P_cs(_nm); n->argumentos=args;
                    return (struct Nodo*)n;
                }
                struct ExprAccesoCampo* n=(struct ExprAccesoCampo*)calloc(1,sizeof(struct ExprAccesoCampo));
                n->tipo=_P_cs("ExprAccesoCampo"); n->objeto=(struct Nodo*)obj; n->nombre_campo=_P_cs(_nm);
                return (struct Nodo*)n;
            }
        }
        struct Identificador* n=(struct Identificador*)calloc(1,sizeof(struct Identificador));
        n->tipo=_P_cs("Identificador"); n->nombre=_P_cs(_nm);
        return (struct Nodo*)n;
    }
    if (t->tipo==T_LPAREN) { _P_avanzar(); struct Nodo* e=_P_expr(); _P_esperar(T_RPAREN); return e; }
    fprintf(stderr,"[PARSER] L%d:%d: expresion inesperada token=%d\n",t->linea,t->col,t->tipo);
    exit(1);
}
static struct Programa _P_programa() {
    struct ListaNodo* lst=NULL; struct ListaNodo** cur=&lst;
    while (_P_mirar()->tipo!=T_EOF) {
        if (_P_mirar()->tipo==T_NL||_P_mirar()->tipo==T_DEDENT) { _P_avanzar(); continue; }
        struct Nodo* st=_P_sentencia();
        if (st) { *cur=_P_mk_list(st,NULL); cur=&(*cur)->cola; }
    }
    struct Programa p; memset(&p,0,sizeof(p));
    p.tipo=_P_cs("Programa"); p.sentencias=lst;
    return p;
}
struct Programa parsear(CadenaSegura fuente) {
    _P_ntks = 0; _P_tpos = 0; _P_p_err = 0; _P_nivel_pila = 0;
    _P_pila_indent[0] = 0;
    _P_tokenizar(fuente.datos, fuente.longitud);
    _P_procesar_indentacion_final();
    struct Programa _prog = _P_programa();
    return _prog;
}

// --- Generador de C ---
// --- AST Walker ---
static int _G_indent = 0;
static FILE* _G_out = NULL;
static char _G_vn[1024][64];
static char _G_vt[1024][64];
static int _G_nv = 0;
static char _G_ret_type[64];
static char _G_extern_names[64][64];
static char _G_extern_params[64][256];
static int _G_nextern = 0;

static void _G_reset() { _G_nv = 0; }
static int _G_find(const char* n) { for(int i=0;i<_G_nv;i++) if(strcmp(_G_vn[i],n)==0) return i; return -1; }
static const char* _G_decl(const char* n, const char* t) {
    int i=_G_find(n); if(i>=0) return _G_vt[i];
    if(_G_nv<1024){ strcpy(_G_vn[_G_nv],n); strcpy(_G_vt[_G_nv],t); _G_nv++; }
    return t;
}

static void _G_emit(const char* s) {
    for(int i=0;i<_G_indent;i++) fprintf(_G_out,"    ");
    fprintf(_G_out,"%s\n",s);
}

static void _G_cp(char* d, CadenaSegura cs) { memcpy(d,cs.datos,cs.longitud); d[cs.longitud]=0; }

static const char* _G_tex(struct Nodo* n) {
    if(!n) return "int";
    const char* t=n->tipo.datos;
    if(strcmp(t,"LiteralNumero")==0) return "int";
    if(strcmp(t,"LiteralCadena")==0) return "CadenaSegura";
    if(strcmp(t,"Identificador")==0) { struct Identificador* i=(struct Identificador*)n; char m[256]; _G_cp(m,i->nombre); int j=_G_find(m); return j>=0?_G_vt[j]:"int"; }
    if(strcmp(t,"OpBinaria")==0||strcmp(t,"OpUnaria")==0) return "int";
    if(strcmp(t,"LlamadaFuncion")==0) {
        struct LlamadaFuncion* l=(struct LlamadaFuncion*)n;
        char m[256]; _G_cp(m,l->nombre);
        if(strcmp(m,"_argc")==0) return "int";
        if(strcmp(m,"_argv")==0||strcmp(m,"leer")==0||strcmp(m,"leer_linea")==0||strcmp(m,"concat")==0) return "CadenaSegura";
        if(strcmp(m,"abrir")==0) return "Canal";
        if(strcmp(m,"cerrar")==0||strcmp(m,"salir")==0||strcmp(m,"escribir")==0||strcmp(m,"escribir_linea")==0) return "void";
        if(strcmp(m,"reserva")==0||strcmp(m,"suma")==0||strcmp(m,"producto")==0||strcmp(m,"relu")==0
   ||strcmp(m,"crear_tensor")==0||strcmp(m,"suma_tensor")==0||strcmp(m,"producto_punto")==0) return "Tensor";
        if(strcmp(m,"tokenizar")==0) return "int";
        if(strcmp(m,"parsear")==0) return "struct Programa";
        if(strcmp(m,"generar")==0) return "int";
        if(strcmp(m,"libera")==0) return "void";
        if(strcmp(m,"texto_a_entero")==0) return "int";
        if(strcmp(m,"texto_a_decimal")==0) return "float";
        if(strcmp(m,"decimal_a_texto")==0) return "CadenaSegura";
        return "int";
    }
    if(strcmp(t,"ExprAccesoCampo")==0||strcmp(t,"ArgumentoTransferido")==0) return "int";
    if(strcmp(t,"ExprTensor")==0) return "Tensor";
    if(strcmp(t,"ExprObtenerDireccion")==0) return "int*";
    if(strcmp(t,"ExprDereferencia")==0) return "int";
    return "int";
}

static void _G_ea(struct Nodo* n, char* b, int sz);
static void _G_vl(struct ListaNodo* l);
static void _G_v(struct Nodo* n);

static int _G_extern_needs_datos(const char* fn, int argidx) {
    for(int _ei=0;_ei<_G_nextern;_ei++){
        if(strcmp(_G_extern_names[_ei],fn)==0){
            int _ec=0,_epos=0;
            char _eb[256]; strcpy(_eb,_G_extern_params[_ei]);
            while(_eb[_epos]){
                int _estart=_epos;
                while(_eb[_epos]&&_eb[_epos]!=',') _epos++;
                _eb[_epos]=0;
                if(_ec==argidx) return strcmp(_eb+_estart,"char*")==0;
                _ec++; _epos++;
            }
            return 0;
        }
    }
    return 0;
}
static void _G_vl(struct ListaNodo* l) { while(l){ _G_v(l->cabeza); l=l->cola; } }

static void _G_ea(struct Nodo* n, char* b, int sz) {
    char i[512],d[512],o[512],m[256];
    if(!n){ snprintf(b,sz,"0"); return; }
    const char* t=n->tipo.datos;
    if(strcmp(t,"LiteralNumero")==0){ struct LiteralNumero* x=(struct LiteralNumero*)n; snprintf(b,sz,"%d",x->valor); return; }
    if(strcmp(t,"LiteralCadena")==0){ struct LiteralCadena* x=(struct LiteralCadena*)n; snprintf(b,sz,"(CadenaSegura){.longitud=%d,.datos=\"%.*s\"}",x->valor.longitud,x->valor.longitud,x->valor.datos); return; }
    if(strcmp(t,"Identificador")==0){ struct Identificador* x=(struct Identificador*)n; char _tmp_nm[256]; _G_cp(_tmp_nm,x->nombre); if(strcmp(_tmp_nm,"nulo")==0) strcpy(b,"NULL"); else strcpy(b,_tmp_nm); return; }
    if(strcmp(t,"OpBinaria")==0){ struct OpBinaria* x=(struct OpBinaria*)n; _G_ea(x->izquierdo,i,512); _G_ea(x->derecho,d,512); char _o[16]; _G_cp(_o,x->operador->lexema); snprintf(b,sz,"(%s %s %s)",i,_o,d); return; }
    if(strcmp(t,"OpUnaria")==0){ struct OpUnaria* x=(struct OpUnaria*)n; _G_ea(x->expr,i,512); char _o[16]; _G_cp(_o,x->operador->lexema); snprintf(b,sz,"(%s%s)",_o,i); return; }
    if(strcmp(t,"LlamadaFuncion")==0){
        struct LlamadaFuncion* x=(struct LlamadaFuncion*)n; _G_cp(m,x->nombre);
        { char* _p=m; while(*_p){ if(*_p=='.') *_p='_'; _p++; } }
        int _coer = (strcmp(m,"escribir")==0||strcmp(m,"escribir_linea")==0||strcmp(m,"abrir")==0||strcmp(m,"concat")==0);
        char a[4096]=""; int p=0; int aidx=0; struct ListaNodo* c=x->argumentos;
        while(c){ if(p>0){ a[p++]=','; a[p++]=' '; }
            _G_ea(c->cabeza,i,512);
            int _dos = _G_extern_needs_datos(m,aidx);
            if(_dos){ snprintf(o,sizeof(o),"(%s).datos",i); strcpy(i,o); }
            if(_coer){ const char* _at = _G_tex(c->cabeza);
                if(strcmp(_at,"int")==0){ char _w[1024]; snprintf(_w,sizeof(_w),"entero_a_texto(%s)",i); int k=0; while(_w[k]) a[p++]=_w[k++]; }
                else if(strcmp(_at,"float")==0){ char _w[1024]; snprintf(_w,sizeof(_w),"decimal_a_texto(%s)",i); int k=0; while(_w[k]) a[p++]=_w[k++]; }
                else{ int k=0; while(i[k]) a[p++]=i[k++]; }
            }else{ int k=0; while(i[k]) a[p++]=i[k++]; }
            c=c->cola; aidx++;
        }
        a[p]=0; snprintf(b,sz,"%s(%s)",m,a); return;
    }
    if(strcmp(t,"ExprAccesoCampo")==0){ struct ExprAccesoCampo* x=(struct ExprAccesoCampo*)n; _G_ea(x->objeto,o,512); _G_cp(m,x->nombre_campo); const char* _ot=_G_tex(x->objeto); int _isp=(strlen(_ot)>0&&_ot[strlen(_ot)-1]=='*'); snprintf(b,sz,"%s%s%s",o,_isp?"->":".",m); return; }
    if(strcmp(t,"ExprTensor")==0){ struct ExprTensor* x=(struct ExprTensor*)n; _G_ea(x->filas,i,512); _G_ea(x->columnas,d,512); snprintf(b,sz,"(Tensor){.filas=%s,.columnas=%s,.datos=(float*)calloc(%s*%s,sizeof(float))}",i,d,i,d); return; }
    if(strcmp(t,"ArgumentoTransferido")==0){ struct ArgumentoTransferido* x=(struct ArgumentoTransferido*)n; _G_ea(x->expr,b,sz); return; }
    if(strcmp(t,"ExprObtenerDireccion")==0){ struct ExprObtenerDireccion* x=(struct ExprObtenerDireccion*)n; _G_ea(x->expr,i,512); snprintf(b,sz,"(&%s)",i); return; }
    if(strcmp(t,"ExprDereferencia")==0){ struct ExprDereferencia* x=(struct ExprDereferencia*)n; _G_ea(x->expr,i,512); snprintf(b,sz,"(*%s)",i); return; }
    snprintf(b,sz,"/*?*/");
}

static void _G_v_log(struct LogLlamada* n) {
    char f[4096]=""; int fp=0,ap=0,fi=1; char b[512]; char pr[4096]="";
    struct ListaNodo* c=n->argumentos;
    while(c){ if(!fi){ f[fp++]=' '; } fi=0; f[fp++]='%'; f[fp++]='s';
        _G_ea(c->cabeza,b,512); if(ap>0){ pr[ap++]=','; pr[ap++]=' '; } int k=0; while(b[k]) pr[ap++]=b[k++]; c=c->cola;
    }
    f[fp]=0; pr[ap]=0; char ln[4096];
    if(ap>0) snprintf(ln,sizeof(ln),"printf(\"%s\\n\",%s);",f,pr);
    else snprintf(ln,sizeof(ln),"printf(\"%s\\n\");",f);
    _G_emit(ln);
}

static const char* _G_mt(const char* st) {
    static char _mtb[64];
    char _base[64]; strcpy(_base,st);
    int _mlen = strlen(_base);
    int _isptr = (_mlen>0 && _base[_mlen-1]=='*');
    if(_isptr) _base[_mlen-1]=0;
    const char* _r=NULL;
    if(strcmp(_base,"entero")==0||strcmp(_base,"int")==0) _r="int";
    else if(strcmp(_base,"texto")==0||strcmp(_base,"cadena")==0) _r="CadenaSegura";
    else if(strcmp(_base,"nulo")==0||strcmp(_base,"vacio")==0) _r="void";
    else if(strcmp(_base,"decimal")==0||strcmp(_base,"real")==0) _r="float";
    else if(strcmp(_base,"logico")==0||strcmp(_base,"booleano")==0) _r="int";
    else if(strcmp(_base,"Canal")==0||strcmp(_base,"canal")==0) _r="Canal";
    else if(strcmp(_base,"Tensor")==0||strcmp(_base,"tensor")==0) _r="Tensor";
    else if(strcmp(_base,"void")==0) _r="void";
    else if(strcmp(_base,"char")==0) _r="char";
    else if(strcmp(_base,"double")==0) _r="double";
    if(!_r) return NULL;
    if(_isptr){ snprintf(_mtb,sizeof(_mtb),"%s*",_r); return _mtb; }
    return _r;
}
static void _G_vest(struct DefinicionEstructura* n) {
    char ln[4096];
    snprintf(ln,sizeof(ln),"typedef struct %s {",n->nombre.datos); _G_emit(ln);
    _G_indent++;
    struct ListaParametro* c=n->campos;
    while(c){ struct Parametro* p=(struct Parametro*)c->cabeza; char pn[256]; _G_cp(pn,p->nombre); char pt[256]; _G_cp(pt,p->tipo_param); const char* ct=_G_mt(pt); if(ct){ snprintf(ln,sizeof(ln),"%s %s;",ct,pn); }else{ snprintf(ln,sizeof(ln),"struct %s* %s;",pt,pn); } _G_emit(ln); c=c->cola; }
    _G_indent--; snprintf(ln,sizeof(ln),"} %s;",n->nombre.datos); _G_emit(ln);
    snprintf(ln,sizeof(ln),"static inline struct %s %s_nuevo() {",n->nombre.datos,n->nombre.datos); _G_emit(ln);
    _G_indent++; snprintf(ln,sizeof(ln),"struct %s _r={0}; return _r;",n->nombre.datos); _G_emit(ln);
    _G_indent--; _G_emit("}");
}

static void _G_v(struct Nodo* n) {
    if(!n) return;
    char b[4096],b2[4096],m[256],v[4096];
    const char* t=n->tipo.datos;
    if(strcmp(t,"DefinicionFuncion")==0){
        _G_reset();
        struct DefinicionFuncion* f=(struct DefinicionFuncion*)n; _G_cp(m,f->nombre);
        { char* _p=m; while(*_p){ if(*_p=='.') *_p='_'; _p++; } }
        if(strcmp(m,"escribir")==0||strcmp(m,"escribir_linea")==0||strcmp(m,"leer_linea")==0||strcmp(m,"abrir")==0||strcmp(m,"leer")==0||strcmp(m,"cerrar")==0||strcmp(m,"crear_tensor")==0||strcmp(m,"suma_tensor")==0||strcmp(m,"producto_punto")==0||strcmp(m,"relu")==0||strcmp(m,"reserva")==0||strcmp(m,"libera")==0||strcmp(m,"suma")==0||strcmp(m,"producto")==0||strcmp(m,"math_crear_tensor")==0||strcmp(m,"math_suma_tensor")==0||strcmp(m,"math_producto_punto")==0||strcmp(m,"math_relu")==0||strcmp(m,"mem_reserva")==0||strcmp(m,"mem_libera")==0||strcmp(m,"math_suma")==0||strcmp(m,"math_producto")==0||strcmp(m,"texto_a_entero")==0||strcmp(m,"texto_a_decimal")==0||strcmp(m,"decimal_a_texto")==0) return;
        char ps[4096]="void"; int pp=0,fi=1; struct ListaParametro* pc=f->parametros;
        while(pc){ struct Parametro* p=(struct Parametro*)pc->cabeza; char pn[256]; _G_cp(pn,p->nombre); char pt[256]; _G_cp(pt,p->tipo_param);
            if(fi){ pp=0; fi=0; }else{ ps[pp++]=','; ps[pp++]=' '; }
            const char* _ct=_G_mt(pt);
            char _tb[64]; if(_ct){ strcpy(_tb,_ct); }else{ snprintf(_tb,sizeof(_tb),"struct %s",pt); } _ct=_tb;
            int k=0; while(_ct[k]) ps[pp++]=_ct[k++]; ps[pp++]=' '; k=0; while(pn[k]) ps[pp++]=pn[k++];
            _G_decl(pn,_ct); pc=pc->cola;
        }
        ps[pp]=0; char rt[64]; _G_cp(rt,f->tipo_retorno);
        {
            const char* _ct=_G_mt(rt);
            if(_ct){ snprintf(b,sizeof(b),"%s %s(%s)",_ct,m,ps); strcpy(_G_ret_type,_ct); }
            else{ snprintf(b,sizeof(b),"struct %s %s(%s)",rt,m,ps); snprintf(_G_ret_type,sizeof(_G_ret_type),"struct %s",rt); }
        }
        _G_emit(b); _G_emit("{"); _G_indent++; _G_vl(f->cuerpo); _G_indent--; _G_emit("}"); return;
    }
    if(strcmp(t,"SentenciaSi")==0){
        struct SentenciaSi* s=(struct SentenciaSi*)n; _G_ea(s->condicion,b,4096);
        snprintf(b2,sizeof(b2),"if (%s) {",b); _G_emit(b2); _G_indent++; _G_vl(s->cuerpo); _G_indent--;
        if(s->cuerpo_sino){ _G_emit("} else {"); _G_indent++; _G_vl(s->cuerpo_sino); _G_indent--; }
        _G_emit("}"); return;
    }
    if(strcmp(t,"SentenciaMientras")==0){
        struct SentenciaMientras* s=(struct SentenciaMientras*)n; _G_ea(s->condicion,b,4096);
        snprintf(b2,sizeof(b2),"while (%s) {",b); _G_emit(b2); _G_indent++; _G_vl(s->cuerpo); _G_indent--; _G_emit("}"); return;
    }
    if(strcmp(t,"AsignacionVariable")==0){
        struct AsignacionVariable* a=(struct AsignacionVariable*)n; _G_cp(m,a->nombre); _G_ea(a->expresion,v,4096);
        const char* vt=_G_tex(a->expresion);
        if(_G_find(m)<0){ _G_decl(m,vt); snprintf(b,sizeof(b),"%s %s = %s;",vt,m,v); }
        else snprintf(b,sizeof(b),"%s = %s;",m,v);
        _G_emit(b); return;
    }
    if(strcmp(t,"AsignacionCampo")==0){
        struct AsignacionCampo* a=(struct AsignacionCampo*)n; _G_ea(a->objeto,b,4096); _G_cp(m,a->nombre_campo); _G_ea(a->expresion,v,4096);
        const char* _ot=_G_tex(a->objeto); int _isp=(strlen(_ot)>0&&_ot[strlen(_ot)-1]=='*');
        snprintf(b2,sizeof(b2),"%s%s%s = %s;",b,_isp?"->":".",m,v); _G_emit(b2); return;
    }
    if(strcmp(t,"SentenciaRetornar")==0){
        struct SentenciaRetornar* r=(struct SentenciaRetornar*)n;
        if(r->expr){ _G_ea(r->expr,v,4096);
            if(strcmp(v,"nulo")==0||strcmp(v,"0")==0||strcmp(v,"NULL")==0){ if(_G_ret_type[0]&&strcmp(_G_ret_type,"void")!=0){ snprintf(b,sizeof(b),"return (%s){0};",_G_ret_type); }else snprintf(b,sizeof(b),"return;"); }
            else snprintf(b,sizeof(b),"return %s;",v);
        }else snprintf(b,sizeof(b),"return;");
        _G_emit(b); return;
    }
    if(strcmp(t,"SentenciaExpr")==0){ struct SentenciaExpr* e=(struct SentenciaExpr*)n; if(e->expr){ if(strcmp(e->expr->tipo.datos,"LogLlamada")==0){ _G_v_log((struct LogLlamada*)e->expr); } else { _G_ea(e->expr,v,4096); snprintf(b,sizeof(b),"%s;",v); _G_emit(b); } } return; }
    if(strcmp(t,"LogLlamada")==0){ _G_v_log((struct LogLlamada*)n); return; }
    if(strcmp(t,"SentenciaRomper")==0){ _G_emit("break;"); return; }
    if(strcmp(t,"SentenciaSiguiente")==0){ _G_emit("continue;"); return; }
    if(strcmp(t,"SentenciaLanzar")==0){ struct SentenciaLanzar* l=(struct SentenciaLanzar*)n; char fn[256]=""; char ab[512]=""; int ha=0; if(strcmp(l->llamada->tipo.datos,"LlamadaFuncion")==0){ struct LlamadaFuncion* lf=(struct LlamadaFuncion*)l->llamada; _G_cp(fn,lf->nombre); if(lf->argumentos){ _G_ea(lf->argumentos->cabeza,ab,512); ha=1; } }else{ _G_ea(l->llamada,fn,256); ha=1; } if(ha){ snprintf(b,sizeof(b),"synapse_lanzar_hilo((void*(*)(void*))%s,(void*)(intptr_t)(%s));",fn,ab); }else{ snprintf(b,sizeof(b),"synapse_lanzar_hilo((void*(*)(void*))%s,NULL);",fn); } _G_emit(b); return; }
    if(strcmp(t,"SentenciaRecuperar")==0){ struct SentenciaRecuperar* r=(struct SentenciaRecuperar*)n; _G_ea(r->accion_critica,b,4096); _G_ea(r->plan_b,v,4096); _G_emit("{"); _G_indent++; snprintf(b2,sizeof(b2),"if(%s!=0){%s;}",b,v); _G_emit(b2); _G_indent--; _G_emit("}"); return; }
    if(strcmp(t,"SentenciaEscuchar")==0){ struct SentenciaEscuchar* e=(struct SentenciaEscuchar*)n; _G_ea(e->canal,b,4096); _G_ea(e->respuesta,v,4096); snprintf(b2,sizeof(b2),"/* escuchar: %s -> %s */",b,v); _G_emit(b2); return; }
    if(strcmp(t,"DefinicionEstructura")==0){ _G_vest((struct DefinicionEstructura*)n); return; }
    if(strcmp(t,"SentenciaImportar")==0){ struct SentenciaImportar* i=(struct SentenciaImportar*)n; _G_cp(b,i->ruta); snprintf(b2,sizeof(b2),"/* importar %s */",b); _G_emit(b2); return; }
    if(strcmp(t,"ImportarC")==0){ struct ImportarC* x=(struct ImportarC*)n; _G_cp(m,x->ruta); if(x->es_sistema){ snprintf(b,sizeof(b),"#include <%s>",m); }else{ snprintf(b,sizeof(b),"#include \"%s\"",m); } _G_emit(b); return; }
    if(strcmp(t,"DeclaracionExterna")==0){
        struct DeclaracionExterna* x=(struct DeclaracionExterna*)n;
        char _enm[256]; _G_cp(_enm,x->nombre);
        strcpy(_G_extern_names[_G_nextern],_enm);
        char _ebuf[256]=""; int _ep=0;
        struct ListaParametro* _epc=(struct ListaParametro*)x->parametros;
        while(_epc){
            struct Parametro* p=(struct Parametro*)_epc->cabeza;
            if(_ep>0){ _ebuf[_ep++]=','; }
            char _ept[256]; _G_cp(_ept,p->tipo_param);
            int _ek=0; while(_ept[_ek]) _ebuf[_ep++]=_ept[_ek++];
            _epc=_epc->cola;
        }
        _ebuf[_ep]=0;
        strcpy(_G_extern_params[_G_nextern],_ebuf);
        _G_nextern++;
        /* C declaration comes from #include via importar_c */
        return;
    }
    if(strcmp(t,"BloqueInseguro")==0){ struct BloqueInseguro* x=(struct BloqueInseguro*)n; _G_emit("{ /* unsafe */"); _G_indent++; _G_vl(x->cuerpo); _G_indent--; _G_emit("}"); return; }
    _G_emit("/* ??? */");
}

int generar(struct Programa programa, CadenaSegura ruta) {
    char sal[1024]; int sl=ruta.longitud;
    if(sl>4&&ruta.datos[sl-4]=='.'&&(ruta.datos[sl-3]=='s'||ruta.datos[sl-3]=='S')&&(ruta.datos[sl-2]=='y'||ruta.datos[sl-2]=='Y')&&(ruta.datos[sl-1]=='n'||ruta.datos[sl-1]=='N')){
        memcpy(sal,ruta.datos,sl-4); sal[sl-4]='.'; sal[sl-3]='c'; sal[sl-2]=0;
    }else snprintf(sal,sizeof(sal),"%.*s.c",ruta.longitud,ruta.datos);
    _G_out=fopen(sal,"w"); if(!_G_out){ fprintf(stderr,"Error: no se puede crear %s\n",sal); return 1; }
    fprintf(_G_out,"// Generado por Synapse (auto-hospedado)\n");
    fprintf(_G_out,"#include <stdio.h>\n#include <stdlib.h>\n#include <stdint.h>\n#include <string.h>\n#include <pthread.h>\n");
    fprintf(_G_out,"typedef struct {int longitud;const char* datos;} CadenaSegura;\n");
    fprintf(_G_out,"typedef struct {uint32_t filas;uint32_t columnas;float* datos;} Tensor;\n");
    fprintf(_G_out,"typedef struct {FILE* stream;int es_valido;int es_virtual;const char* virtual_data;int virtual_len;} Canal;\n");
    fprintf(_G_out,"#define POOL_BLOQUES 64\n#define TAMANO_BLOQUE 4096\n");
    fprintf(_G_out,"#define nulo ((void*)0)\n");
    fprintf(_G_out,"// --- Declaraciones extern del runtime precompilado (synapse_rt.o) ---\n");
    fprintf(_G_out,"extern void escribir(CadenaSegura contenido);\n");
    fprintf(_G_out,"extern void escribir_linea(CadenaSegura contenido);\n");
    fprintf(_G_out,"extern CadenaSegura leer_linea(void);\n");
    fprintf(_G_out,"extern Canal abrir(CadenaSegura ruta, CadenaSegura modo);\n");
    fprintf(_G_out,"extern CadenaSegura leer(Canal canal);\n");
    fprintf(_G_out,"extern void cerrar(Canal canal);\n");
    fprintf(_G_out,"extern Tensor crear_tensor(int filas, int columnas);\n");
    fprintf(_G_out,"extern Tensor suma_tensor(Tensor a, Tensor b);\n");
    fprintf(_G_out,"extern Tensor producto_punto(Tensor a, Tensor b);\n");
    fprintf(_G_out,"extern Tensor relu(Tensor a);\n");
    fprintf(_G_out,"extern Tensor reserva(int tamano);\n");
    fprintf(_G_out,"extern void libera(Tensor bloque);\n");
    fprintf(_G_out,"extern Tensor suma(Tensor a, Tensor b);\n");
    fprintf(_G_out,"extern Tensor producto(Tensor a, Tensor b);\n");
    fprintf(_G_out,"extern int texto_a_entero(CadenaSegura str);\n");
    fprintf(_G_out,"extern float texto_a_decimal(CadenaSegura str);\n");
    fprintf(_G_out,"extern CadenaSegura decimal_a_texto(float n);\n");
    fprintf(_G_out,"extern CadenaSegura entero_a_texto(int n);\n");
    fprintf(_G_out,"extern void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);\n");
    fprintf(_G_out,"extern void synapse_esperar_hilos(void);\n");
    fprintf(_G_out,"extern void pool_init(uint32_t total_blocks, uint32_t block_size);\n");
    fprintf(_G_out,"extern void pool_free(void* ptr);\n");
    fprintf(_G_out,"static int _g_argc;\nstatic char** _g_argv;\nint _argc(){return _g_argc;}\n");
    fprintf(_G_out,"CadenaSegura _argv(int i){if(i<0||i>=_g_argc)return (CadenaSegura){0,(char*)\"\"};return (CadenaSegura){.longitud=(int)strlen(_g_argv[i]),.datos=_g_argv[i]};}\n");
    fprintf(_G_out,"void salir(int c){exit(c);}\n");
    fprintf(_G_out,"CadenaSegura concat(CadenaSegura a,CadenaSegura b){int _tl=a.longitud+b.longitud;char* _buf=(char*)malloc(_tl+1);memcpy(_buf,a.datos,a.longitud);memcpy(_buf+a.longitud,b.datos,b.longitud);_buf[_tl]=0;CadenaSegura _r={.longitud=_tl,.datos=_buf};return _r;}\n");
    // Forward declarations
    struct ListaNodo* c=programa.sentencias;
    while(c){ if(c->cabeza&&strcmp(c->cabeza->tipo.datos,"DefinicionEstructura")==0){ struct DefinicionEstructura* d=(struct DefinicionEstructura*)c->cabeza; fprintf(_G_out,"struct %s;\n",d->nombre.datos); } c=c->cola; }
    // Function prototypes
    c=programa.sentencias;
    while(c){ if(c->cabeza&&strcmp(c->cabeza->tipo.datos,"DefinicionFuncion")==0){ struct DefinicionFuncion* f=(struct DefinicionFuncion*)c->cabeza; char _fn[256]; _G_cp(_fn,f->nombre); { char* _p=_fn; while(*_p){ if(*_p=='.') *_p='_'; _p++; } } if(strcmp(_fn,"escribir")==0||strcmp(_fn,"escribir_linea")==0||strcmp(_fn,"leer_linea")==0||strcmp(_fn,"abrir")==0||strcmp(_fn,"leer")==0||strcmp(_fn,"cerrar")==0||strcmp(_fn,"crear_tensor")==0||strcmp(_fn,"suma_tensor")==0||strcmp(_fn,"producto_punto")==0||strcmp(_fn,"relu")==0||strcmp(_fn,"reserva")==0||strcmp(_fn,"libera")==0||strcmp(_fn,"suma")==0||strcmp(_fn,"producto")==0||strcmp(_fn,"math_crear_tensor")==0||strcmp(_fn,"math_suma_tensor")==0||strcmp(_fn,"math_producto_punto")==0||strcmp(_fn,"math_relu")==0||strcmp(_fn,"mem_reserva")==0||strcmp(_fn,"mem_libera")==0||strcmp(_fn,"math_suma")==0||strcmp(_fn,"math_producto")==0||strcmp(_fn,"texto_a_entero")==0||strcmp(_fn,"texto_a_decimal")==0||strcmp(_fn,"decimal_a_texto")==0) { c=c->cola; continue; } char _ps[4096]="void"; int _pp=0,_fi=1; struct ListaParametro* _pc=f->parametros; while(_pc){ struct Parametro* p=(struct Parametro*)_pc->cabeza; char _pn[256]; _G_cp(_pn,p->nombre); char _pt[256]; _G_cp(_pt,p->tipo_param); if(_fi){ _pp=0; _fi=0; }else{ _ps[_pp++]=','; _ps[_pp++]=' '; } const char* _ct=_G_mt(_pt); char _tb[64]; if(_ct){ strcpy(_tb,_ct); }else{ snprintf(_tb,sizeof(_tb),"struct %s",_pt); } _ct=_tb; int _k=0; while(_ct[_k]) _ps[_pp++]=_ct[_k++]; _ps[_pp++]=' '; _k=0; while(_pn[_k]) _ps[_pp++]=_pn[_k++]; _pc=_pc->cola; } _ps[_pp]=0; char _rt[64]; _G_cp(_rt,f->tipo_retorno); const char* _rct=_G_mt(_rt); if(_rct){ fprintf(_G_out,"%s %s(%s);\n",_rct,_fn,_ps); }else{ fprintf(_G_out,"struct %s %s(%s);\n",_rt,_fn,_ps); } } c=c->cola; }
    _G_indent=0; c=programa.sentencias;
    while(c){ _G_v(c->cabeza); c=c->cola; }
    // main()
    _G_emit("int main(int argc, char** argv) {");
    _G_indent++;
    _G_emit("int _g_argc=argc;");
    _G_emit("char** _g_argv=argv;");
    _G_emit("pool_init(POOL_BLOQUES, TAMANO_BLOQUE);");
    _G_emit("principal();");
    _G_emit("synapse_esperar_hilos();");
    _G_emit("return 0;");
    _G_indent--;
    _G_emit("}");
    fclose(_G_out);
    char cmd[2048];
    char out_exe[1024];
    int slen = (int)strlen(sal);
    if (slen > 2 && sal[slen-2] == '.' && sal[slen-1] == 'c') {
        memcpy(out_exe, sal, slen - 2);
        out_exe[slen - 2] = 0;
        strcat(out_exe, ".exe");
    } else {
        snprintf(out_exe, sizeof(out_exe), "%s.exe", sal);
    }
    snprintf(cmd, sizeof(cmd), "gcc \"%s\" \"C:\\Synapse\\lib\\synapse_rt.o\" -o \"%s\" -lpthread -lm", sal, out_exe);
    int rc = system(cmd);
    if (rc != 0) {
        fprintf(stderr, "[LINKER ERROR] gcc fallo con codigo %d\n", rc);
        exit(1);
    }
    fprintf(stderr, "OK: %s\n", out_exe);
    return 0;
}
void _volcar_nodo(struct Nodo* nodo, int nivel) {
    if (!nodo) { printf("(null)\n"); return; }
    for (int _i = 0; _i < nivel; _i++) printf("  ");
    printf("[%s]\n", nodo->tipo.datos);
    if (strcmp(nodo->tipo.datos, "Token") == 0) {
        printf("  tipo: %d\n", ((struct Token*)nodo)->tipo);
        printf("  lexema: %s\n", ((struct Token*)nodo)->lexema.datos);
        printf("  linea: %d\n", ((struct Token*)nodo)->linea);
        printf("  columna: %d\n", ((struct Token*)nodo)->columna);
    }
    else if (strcmp(nodo->tipo.datos, "ListaNodo") == 0) {
        _volcar_nodo(((struct ListaNodo*)nodo)->cabeza, nivel + 1);
        { struct ListaNodo* _cur = ((struct ListaNodo*)nodo)->cola; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
    }
    else if (strcmp(nodo->tipo.datos, "Programa") == 0) {
        printf("  tipo: %s\n", ((struct Programa*)nodo)->tipo.datos);
        { struct ListaNodo* _cur = ((struct Programa*)nodo)->sentencias; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
    }
    else if (strcmp(nodo->tipo.datos, "Identificador") == 0) {
        printf("  tipo: %s\n", ((struct Identificador*)nodo)->tipo.datos);
        printf("  nombre: %s\n", ((struct Identificador*)nodo)->nombre.datos);
    }
    else if (strcmp(nodo->tipo.datos, "LiteralNumero") == 0) {
        printf("  tipo: %s\n", ((struct LiteralNumero*)nodo)->tipo.datos);
        printf("  valor: %d\n", ((struct LiteralNumero*)nodo)->valor);
    }
    else if (strcmp(nodo->tipo.datos, "LiteralCadena") == 0) {
        printf("  tipo: %s\n", ((struct LiteralCadena*)nodo)->tipo.datos);
        printf("  valor: %s\n", ((struct LiteralCadena*)nodo)->valor.datos);
    }
    else if (strcmp(nodo->tipo.datos, "OpBinaria") == 0) {
        printf("  tipo: %s\n", ((struct OpBinaria*)nodo)->tipo.datos);
        _volcar_nodo(((struct OpBinaria*)nodo)->izquierdo, nivel + 1);
        _volcar_nodo(((struct OpBinaria*)nodo)->operador, nivel + 1);
        _volcar_nodo(((struct OpBinaria*)nodo)->derecho, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "OpUnaria") == 0) {
        printf("  tipo: %s\n", ((struct OpUnaria*)nodo)->tipo.datos);
        _volcar_nodo(((struct OpUnaria*)nodo)->operador, nivel + 1);
        _volcar_nodo(((struct OpUnaria*)nodo)->expr, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "LlamadaFuncion") == 0) {
        printf("  tipo: %s\n", ((struct LlamadaFuncion*)nodo)->tipo.datos);
        printf("  nombre: %s\n", ((struct LlamadaFuncion*)nodo)->nombre.datos);
        { struct ListaNodo* _cur = ((struct LlamadaFuncion*)nodo)->argumentos; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
    }
    else if (strcmp(nodo->tipo.datos, "ExprAccesoCampo") == 0) {
        printf("  tipo: %s\n", ((struct ExprAccesoCampo*)nodo)->tipo.datos);
        printf("  nombre_campo: %s\n", ((struct ExprAccesoCampo*)nodo)->nombre_campo.datos);
        _volcar_nodo(((struct ExprAccesoCampo*)nodo)->objeto, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "AsignacionVariable") == 0) {
        printf("  tipo: %s\n", ((struct AsignacionVariable*)nodo)->tipo.datos);
        printf("  nombre: %s\n", ((struct AsignacionVariable*)nodo)->nombre.datos);
        _volcar_nodo(((struct AsignacionVariable*)nodo)->expresion, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "AsignacionCampo") == 0) {
        printf("  tipo: %s\n", ((struct AsignacionCampo*)nodo)->tipo.datos);
        printf("  nombre_campo: %s\n", ((struct AsignacionCampo*)nodo)->nombre_campo.datos);
        _volcar_nodo(((struct AsignacionCampo*)nodo)->objeto, nivel + 1);
        _volcar_nodo(((struct AsignacionCampo*)nodo)->expresion, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "SentenciaSi") == 0) {
        printf("  tipo: %s\n", ((struct SentenciaSi*)nodo)->tipo.datos);
        _volcar_nodo(((struct SentenciaSi*)nodo)->condicion, nivel + 1);
        { struct ListaNodo* _cur = ((struct SentenciaSi*)nodo)->cuerpo; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
        { struct ListaNodo* _cur = ((struct SentenciaSi*)nodo)->cuerpo_sino; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
    }
    else if (strcmp(nodo->tipo.datos, "SentenciaMientras") == 0) {
        printf("  tipo: %s\n", ((struct SentenciaMientras*)nodo)->tipo.datos);
        _volcar_nodo(((struct SentenciaMientras*)nodo)->condicion, nivel + 1);
        { struct ListaNodo* _cur = ((struct SentenciaMientras*)nodo)->cuerpo; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
    }
    else if (strcmp(nodo->tipo.datos, "SentenciaRetornar") == 0) {
        printf("  tipo: %s\n", ((struct SentenciaRetornar*)nodo)->tipo.datos);
        _volcar_nodo(((struct SentenciaRetornar*)nodo)->expr, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "SentenciaExpr") == 0) {
        printf("  tipo: %s\n", ((struct SentenciaExpr*)nodo)->tipo.datos);
        _volcar_nodo(((struct SentenciaExpr*)nodo)->expr, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "LogLlamada") == 0) {
        printf("  tipo: %s\n", ((struct LogLlamada*)nodo)->tipo.datos);
        { struct ListaNodo* _cur = ((struct LogLlamada*)nodo)->argumentos; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
    }
    else if (strcmp(nodo->tipo.datos, "Parametro") == 0) {
        printf("  tipo: %s\n", ((struct Parametro*)nodo)->tipo.datos);
        printf("  nombre: %s\n", ((struct Parametro*)nodo)->nombre.datos);
        printf("  tipo_param: %s\n", ((struct Parametro*)nodo)->tipo_param.datos);
        printf("  es_transferencia: %d\n", ((struct Parametro*)nodo)->es_transferencia);
    }
    else if (strcmp(nodo->tipo.datos, "ListaParametro") == 0) {
        _volcar_nodo(((struct ListaParametro*)nodo)->cabeza, nivel + 1);
        { struct ListaParametro* _cur = ((struct ListaParametro*)nodo)->cola; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
    }
    else if (strcmp(nodo->tipo.datos, "DefinicionFuncion") == 0) {
        printf("  tipo: %s\n", ((struct DefinicionFuncion*)nodo)->tipo.datos);
        printf("  nombre: %s\n", ((struct DefinicionFuncion*)nodo)->nombre.datos);
        printf("  tipo_retorno: %s\n", ((struct DefinicionFuncion*)nodo)->tipo_retorno.datos);
        { struct ListaParametro* _cur = ((struct DefinicionFuncion*)nodo)->parametros; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
        { struct ListaNodo* _cur = ((struct DefinicionFuncion*)nodo)->cuerpo; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
    }
    else if (strcmp(nodo->tipo.datos, "DefinicionEstructura") == 0) {
        printf("  tipo: %s\n", ((struct DefinicionEstructura*)nodo)->tipo.datos);
        printf("  nombre: %s\n", ((struct DefinicionEstructura*)nodo)->nombre.datos);
        { struct ListaParametro* _cur = ((struct DefinicionEstructura*)nodo)->campos; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
    }
    else if (strcmp(nodo->tipo.datos, "SentenciaRomper") == 0) {
        printf("  tipo: %s\n", ((struct SentenciaRomper*)nodo)->tipo.datos);
    }
    else if (strcmp(nodo->tipo.datos, "SentenciaSiguiente") == 0) {
        printf("  tipo: %s\n", ((struct SentenciaSiguiente*)nodo)->tipo.datos);
    }
    else if (strcmp(nodo->tipo.datos, "SentenciaLanzar") == 0) {
        printf("  tipo: %s\n", ((struct SentenciaLanzar*)nodo)->tipo.datos);
        _volcar_nodo(((struct SentenciaLanzar*)nodo)->llamada, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "SentenciaRecuperar") == 0) {
        printf("  tipo: %s\n", ((struct SentenciaRecuperar*)nodo)->tipo.datos);
        _volcar_nodo(((struct SentenciaRecuperar*)nodo)->accion_critica, nivel + 1);
        _volcar_nodo(((struct SentenciaRecuperar*)nodo)->plan_b, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "SentenciaEscuchar") == 0) {
        printf("  tipo: %s\n", ((struct SentenciaEscuchar*)nodo)->tipo.datos);
        _volcar_nodo(((struct SentenciaEscuchar*)nodo)->canal, nivel + 1);
        _volcar_nodo(((struct SentenciaEscuchar*)nodo)->respuesta, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "ExprTensor") == 0) {
        printf("  tipo: %s\n", ((struct ExprTensor*)nodo)->tipo.datos);
        _volcar_nodo(((struct ExprTensor*)nodo)->filas, nivel + 1);
        _volcar_nodo(((struct ExprTensor*)nodo)->columnas, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "ExprIndice") == 0) {
        printf("  tipo: %s\n", ((struct ExprIndice*)nodo)->tipo.datos);
        _volcar_nodo(((struct ExprIndice*)nodo)->expr, nivel + 1);
        _volcar_nodo(((struct ExprIndice*)nodo)->indice, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "ArgumentoTransferido") == 0) {
        printf("  tipo: %s\n", ((struct ArgumentoTransferido*)nodo)->tipo.datos);
        _volcar_nodo(((struct ArgumentoTransferido*)nodo)->expr, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "SentenciaImportar") == 0) {
        printf("  tipo: %s\n", ((struct SentenciaImportar*)nodo)->tipo.datos);
        printf("  ruta: %s\n", ((struct SentenciaImportar*)nodo)->ruta.datos);
    }
    else if (strcmp(nodo->tipo.datos, "ExprObtenerDireccion") == 0) {
        printf("  tipo: %s\n", ((struct ExprObtenerDireccion*)nodo)->tipo.datos);
        _volcar_nodo(((struct ExprObtenerDireccion*)nodo)->expr, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "ExprDereferencia") == 0) {
        printf("  tipo: %s\n", ((struct ExprDereferencia*)nodo)->tipo.datos);
        _volcar_nodo(((struct ExprDereferencia*)nodo)->expr, nivel + 1);
    }
    else if (strcmp(nodo->tipo.datos, "ImportarC") == 0) {
        printf("  tipo: %s\n", ((struct ImportarC*)nodo)->tipo.datos);
        printf("  ruta: %s\n", ((struct ImportarC*)nodo)->ruta.datos);
        printf("  es_sistema: %d\n", ((struct ImportarC*)nodo)->es_sistema);
    }
    else if (strcmp(nodo->tipo.datos, "DeclaracionExterna") == 0) {
        printf("  tipo: %s\n", ((struct DeclaracionExterna*)nodo)->tipo.datos);
        printf("  nombre: %s\n", ((struct DeclaracionExterna*)nodo)->nombre.datos);
        printf("  tipo_retorno: %s\n", ((struct DeclaracionExterna*)nodo)->tipo_retorno.datos);
        { struct ListaParametro* _cur = ((struct DeclaracionExterna*)nodo)->parametros; while (_cur) { _volcar_nodo(_cur->cabeza, nivel + 1); _cur = _cur->cola; } }
    }
    else { printf("  (tipo desconocido)\n"); }
}

void volcar_ast(struct Nodo* nodo, int nivel) { _volcar_nodo(nodo, nivel); }

int crear_analizador(struct Programa programa) {
    return 0;
}

void analizar(int analizador) {
    return;
}

void ejecutar_dump(CadenaSegura ruta) {
    Canal canal = abrir(ruta, (CadenaSegura){ .longitud = 1, .datos = "r" });
    CadenaSegura fuente = leer(canal);
    cerrar(canal);
    struct Programa programa = parsear(fuente);
    volcar_ast((&programa), 0);
    /* ADVERTENCIA: canal 'canal' no fue cerrado explicitamente */
    if (canal.stream) { fclose(canal.stream); canal.es_valido = 0; }
    free((void*)fuente.datos);
}

void principal(void) {
    if ((_argc() < 2)) {
        printf("Uso: main <archivo.syn> [--dump-ast]\n");
        salir(1);
    }
    CadenaSegura ruta = _argv(1);
    int modo_dump = ((_argc() >= 3) && (strcmp(_argv(2).datos, (CadenaSegura){ .longitud = 10, .datos = "--dump-ast" }.datos) == 0));
    if (modo_dump) {
        ejecutar_dump(ruta);
        salir(0);
    }
    printf("Compilando: %s\n", (ruta).datos);
    Canal canal = abrir((CadenaSegura){ .longitud = 32, .datos = "librerias/compiler/ast_nodes.syn" }, (CadenaSegura){ .longitud = 1, .datos = "r" });
    CadenaSegura lib_ast = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){ .longitud = 29, .datos = "librerias/compiler/parser.syn" }, (CadenaSegura){ .longitud = 1, .datos = "r" });
    CadenaSegura lib_parse = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){ .longitud = 32, .datos = "librerias/compiler/generator.syn" }, (CadenaSegura){ .longitud = 1, .datos = "r" });
    CadenaSegura lib_gen = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){ .longitud = 20, .datos = "librerias/std/io.syn" }, (CadenaSegura){ .longitud = 1, .datos = "r" });
    CadenaSegura lib_io = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){ .longitud = 22, .datos = "librerias/std/math.syn" }, (CadenaSegura){ .longitud = 1, .datos = "r" });
    CadenaSegura lib_math = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){ .longitud = 21, .datos = "librerias/std/mem.syn" }, (CadenaSegura){ .longitud = 1, .datos = "r" });
    CadenaSegura lib_mem = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){ .longitud = 28, .datos = "src/analizador_semantico.syn" }, (CadenaSegura){ .longitud = 1, .datos = "r" });
    CadenaSegura lib_semantico = leer(canal);
    cerrar(canal);
    canal = abrir(ruta, (CadenaSegura){ .longitud = 1, .datos = "r" });
    CadenaSegura fuente = leer(canal);
    cerrar(canal);
    CadenaSegura fuente_completa = concat(concat(concat(concat(concat(concat(concat(lib_ast, lib_parse), lib_gen), lib_io), lib_math), lib_mem), lib_semantico), fuente);
    struct Programa programa = parsear(fuente_completa);
    int analizador = crear_analizador(programa);
    analizar(analizador);
    int errores = generar(programa, ruta);
    if ((errores > 0)) {
        printf("Error: %d %s\n", errores, ((CadenaSegura){ .longitud = 8, .datos = "fallo(s)" }).datos);
        salir(errores);
    }
    printf("OK: %s\n", (ruta).datos);
    /* ADVERTENCIA: canal 'canal' no fue cerrado explicitamente */
    if (canal.stream) { fclose(canal.stream); canal.es_valido = 0; }
    free((void*)lib_semantico.datos);
    free((void*)lib_mem.datos);
    free((void*)fuente.datos);
    free((void*)lib_math.datos);
    free((void*)lib_ast.datos);
    free((void*)lib_io.datos);
    free((void*)lib_parse.datos);
    free((void*)lib_gen.datos);
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    principal();
    synapse_esperar_hilos();
    return 0;
}