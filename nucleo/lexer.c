// salida_metal.c - Generado por Synapse Compilador
// Lenguaje: Synapse v1.0 (#lang: es)
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <string.h>
#include <assert.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

typedef struct { uint32_t filas; uint32_t columnas; float* datos; int es_mapeado; } Tensor;

typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;

#define nulo ((void*)0)

// --- OO AST node types (correct, from hola.c) ---
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
struct ImportarC;
struct DeclaracionExterna;
struct BloqueInseguro;
struct ExprObtenerDireccion;
struct ExprDereferencia;

typedef struct Token { int tipo; CadenaSegura lexema; int linea; int columna; } Token;
typedef struct Nodo { CadenaSegura tipo; } Nodo;
typedef struct ListaNodo { struct Nodo* cabeza; struct ListaNodo* cola; } ListaNodo;
typedef struct Programa { CadenaSegura tipo; struct ListaNodo* sentencias; } Programa;
typedef struct Identificador { CadenaSegura tipo; CadenaSegura nombre; } Identificador;
typedef struct LiteralNumero { CadenaSegura tipo; int valor; } LiteralNumero;
typedef struct LiteralCadena { CadenaSegura tipo; CadenaSegura valor; } LiteralCadena;
typedef struct OpBinaria { CadenaSegura tipo; struct Nodo* izquierdo; struct Token* operador; struct Nodo* derecho; } OpBinaria;
typedef struct OpUnaria { CadenaSegura tipo; struct Token* operador; struct Nodo* expr; } OpUnaria;
typedef struct LlamadaFuncion { CadenaSegura tipo; CadenaSegura nombre; struct ListaNodo* argumentos; } LlamadaFuncion;
typedef struct ExprAccesoCampo { CadenaSegura tipo; struct Nodo* objeto; CadenaSegura nombre_campo; } ExprAccesoCampo;
typedef struct AsignacionVariable { CadenaSegura tipo; CadenaSegura nombre; struct Nodo* expresion; } AsignacionVariable;
typedef struct AsignacionCampo { CadenaSegura tipo; struct Nodo* objeto; CadenaSegura nombre_campo; struct Nodo* expresion; } AsignacionCampo;
typedef struct SentenciaSi { CadenaSegura tipo; struct Nodo* condicion; struct ListaNodo* cuerpo; struct ListaNodo* cuerpo_sino; } SentenciaSi;
typedef struct SentenciaMientras { CadenaSegura tipo; struct Nodo* condicion; struct ListaNodo* cuerpo; } SentenciaMientras;
typedef struct SentenciaRetornar { CadenaSegura tipo; struct Nodo* expr; } SentenciaRetornar;
typedef struct SentenciaExpr { CadenaSegura tipo; struct Nodo* expr; } SentenciaExpr;
typedef struct LogLlamada { CadenaSegura tipo; struct ListaNodo* argumentos; } LogLlamada;
typedef struct Parametro { CadenaSegura tipo; CadenaSegura nombre; CadenaSegura tipo_param; int es_transferencia; } Parametro;
typedef struct ListaParametro { struct Parametro* cabeza; struct ListaParametro* cola; } ListaParametro;
typedef struct DefinicionFuncion { CadenaSegura tipo; CadenaSegura nombre; struct ListaParametro* parametros; CadenaSegura tipo_retorno; struct ListaNodo* cuerpo; } DefinicionFuncion;
typedef struct DefinicionEstructura { CadenaSegura tipo; CadenaSegura nombre; struct ListaParametro* campos; } DefinicionEstructura;
typedef struct SentenciaRomper { CadenaSegura tipo; } SentenciaRomper;
typedef struct SentenciaSiguiente { CadenaSegura tipo; } SentenciaSiguiente;
typedef struct SentenciaLanzar { CadenaSegura tipo; struct Nodo* llamada; } SentenciaLanzar;
typedef struct SentenciaRecuperar { CadenaSegura tipo; struct Nodo* accion_critica; struct Nodo* plan_b; } SentenciaRecuperar;
typedef struct SentenciaEscuchar { CadenaSegura tipo; struct Nodo* canal; struct Nodo* respuesta; } SentenciaEscuchar;
typedef struct ExprTensor { CadenaSegura tipo; struct Nodo* filas; struct Nodo* columnas; } ExprTensor;
typedef struct ExprIndice { CadenaSegura tipo; struct Nodo* expr; struct Nodo* indice; } ExprIndice;
typedef struct ArgumentoTransferido { CadenaSegura tipo; struct Nodo* expr; } ArgumentoTransferido;
typedef struct SentenciaImportar { CadenaSegura tipo; CadenaSegura ruta; } SentenciaImportar;
typedef struct ImportarC { CadenaSegura tipo; CadenaSegura ruta; int es_sistema; } ImportarC;
typedef struct DeclaracionExterna { CadenaSegura tipo; CadenaSegura nombre; struct Parametro* parametros; CadenaSegura tipo_retorno; } DeclaracionExterna;
typedef struct BloqueInseguro { CadenaSegura tipo; struct Nodo* cuerpo; } BloqueInseguro;
typedef struct ExprObtenerDireccion { CadenaSegura tipo; struct Nodo* expr; } ExprObtenerDireccion;
typedef struct ExprDereferencia { CadenaSegura tipo; struct Nodo* expr; } ExprDereferencia;

// Constantes del pool de memoria (definidas en synapse_rt.c)
#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096

// Constantes de tags para uniones etiquetadas (ADTs)
#define TAG_OK 0
#define TAG_ERR 1
#define TAG_ALGUNO 0
#define TAG_NINGUNO 1

// --- Helpers de serialización primitiva para canales (Zero-Copy) ---
static inline void* _synapse_box_int(int v) { return (void*)(intptr_t)v; }
static inline int _synapse_unbox_int(void* p) { return (int)(intptr_t)p; }
static inline void* _synapse_box_float(float v) {
    float* _p = (float*)malloc(sizeof(float));
    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en _synapse_box_float\n"); exit(1); }
    *_p = v;
    return (void*)_p;
}
static inline float _synapse_unbox_float(void* p) {
    float _v = *(float*)p;
    free(p);
    return _v;
}

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
extern void _syn_texto_liberar(CadenaSegura s);

// --- Declaraciones extern de canales (CanalConcurrencia) ---
typedef struct { int es_ok; union { void* ok_valor; const char* err_mensaje; } datos; } Resultado_T;
typedef struct CanalConcurrencia CanalConcurrencia;
extern CanalConcurrencia* canal_crear(uint32_t capacidad);
extern void canal_enviar(CanalConcurrencia* canal, void* paquete);
extern void* canal_recibir(CanalConcurrencia* canal);
extern void canal_destruir(CanalConcurrencia* canal);
extern void cerrar_canal(CanalConcurrencia* canal);
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

struct TokenLex;
struct LexerEstado;

int str_len(CadenaSegura s);
int str_char(CadenaSegura s, int i);
int str_char_at(int ptr, int i);
int str_eq(CadenaSegura a, CadenaSegura b);
int str_len_ptr(int ptr);
int keyword_token(CadenaSegura palabra);
int es_digito(int c);
int es_letra(int c);
int es_alnum(int c);
void lexer_push_token(struct LexerEstado lex, int tipo, int linea, int columna);
void lexer_error(struct LexerEstado lex, CadenaSegura mensaje, int linea, int columna);
void lexer_detectar_idioma(struct LexerEstado lex);
void lexer_procesar_indentacion(struct LexerEstado lex, int ptr_linea, int len_linea);
void lexer_tokenizar_linea(struct LexerEstado lex, int ptr_texto, int len_texto);
int tokenizar(CadenaSegura fuente);

#define T_IF (1)
#define T_ELSE (2)
#define T_FUNCION (3)
#define T_RETORNAR (4)
#define T_LANZAR (5)
#define T_RECUPERAR (6)
#define T_ESCUCHAR (7)
#define T_MIENTRAS (8)
#define T_IMPORTAR (9)
#define T_ESTRUCTURA (10)
#define T_ROMPER (11)
#define T_SIGUIENTE (12)
#define T_PUNTO (13)
#define T_Y (14)
#define T_O (15)
#define T_NO (16)
#define T_VERDADERO (17)
#define T_FALSO (18)
#define T_IDENTIFICADOR (19)
#define T_NUMERO (20)
#define T_FLOTANTE (21)
#define T_CADENA (22)
#define T_MAYOR (23)
#define T_MENOR (24)
#define T_IGUAL (25)
#define T_DISTINTO (26)
#define T_MENOR_IGUAL (27)
#define T_MAYOR_IGUAL (28)
#define T_ASIGNAR (29)
#define T_MAS (30)
#define T_MENOS (31)
#define T_POR (32)
#define T_DIV (33)
#define T_MOD (34)
#define T_FLECHA (35)
#define T_COINCIDIR (36)
#define T_FLECHA_DER (37)
#define T_PAREN_IZQ (38)
#define T_PAREN_DER (39)
#define T_DOSPUNTOS (40)
#define T_COMA (41)
#define T_NUEVALINEA (42)
#define T_INDENTAR (43)
#define T_DESINDENTAR (44)
#define T_AMPERSAND (45)
#define T_INSEGURO (46)
#define T_IMPORTAR_C (47)
#define T_EXTERNO (48)
#define T_FLECHA_IZQ (49)
#define T_REQUIERE (50)
#define T_GARANTIZA (51)
#define T_CANAL (52)
#define T_ASM (53)
#define T_CONSTANTE (54)
#define T_PUNTOCOMA (55)
#define T_PARA (56)
#define T_FIN (57)
#define T_ERROR (58)
typedef struct TokenLex {
    int tipo;
    int linea;
    int columna;
    CadenaSegura valor;
} TokenLex;

static inline struct TokenLex TokenLex_nuevo() {
    struct TokenLex _r = {0};
    return _r;
}

int str_len(CadenaSegura s) {
    { /* unsafe */
        int r = 0;
        r = s.longitud;
        int _ret_75 = r;
        return _ret_75;
    }
}

int str_char(CadenaSegura s, int i) {
    { /* unsafe */
        int r = 0;
        r = (i >= 0 && i < s.longitud) ? (unsigned char)s.datos[i] : 0;
        int _ret_81 = r;
        return _ret_81;
    }
}

int str_char_at(int ptr, int i) {
    { /* unsafe */
        int r = 0;
        r = (unsigned char)((const char*)ptr)[i];
        int _ret_87 = r;
        return _ret_87;
    }
}

int str_eq(CadenaSegura a, CadenaSegura b) {
    { /* unsafe */
        int r = 0;
        if (a.longitud != b.longitud) { r = 0; } else { r = 1; for (int _si = 0; _si < a.longitud; _si++) { if (a.datos[_si] != b.datos[_si]) { r = 0; break; } } };
        int _ret_93 = r;
        return _ret_93;
    }
}

int str_len_ptr(int ptr) {
    { /* unsafe */
        int r = 0;
        r = (int)strlen((const char*)ptr);
        int _ret_99 = r;
        return _ret_99;
    }
}

int keyword_token(CadenaSegura palabra) {
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 2, .datos = "si" }) == 1)) {
        int _ret_104 = T_IF;
        return _ret_104;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 4, .datos = "sino" }) == 1)) {
        int _ret_106 = T_ELSE;
        return _ret_106;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 7, .datos = "funcion" }) == 1)) {
        int _ret_108 = T_FUNCION;
        return _ret_108;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 8, .datos = "retornar" }) == 1)) {
        int _ret_110 = T_RETORNAR;
        return _ret_110;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 6, .datos = "lanzar" }) == 1)) {
        int _ret_112 = T_LANZAR;
        return _ret_112;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 9, .datos = "recuperar" }) == 1)) {
        int _ret_114 = T_RECUPERAR;
        return _ret_114;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 8, .datos = "escuchar" }) == 1)) {
        int _ret_116 = T_ESCUCHAR;
        return _ret_116;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 8, .datos = "mientras" }) == 1)) {
        int _ret_118 = T_MIENTRAS;
        return _ret_118;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 8, .datos = "importar" }) == 1)) {
        int _ret_120 = T_IMPORTAR;
        return _ret_120;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 6, .datos = "romper" }) == 1)) {
        int _ret_122 = T_ROMPER;
        return _ret_122;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 9, .datos = "siguiente" }) == 1)) {
        int _ret_124 = T_SIGUIENTE;
        return _ret_124;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 10, .datos = "estructura" }) == 1)) {
        int _ret_126 = T_ESTRUCTURA;
        return _ret_126;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 1, .datos = "y" }) == 1)) {
        int _ret_128 = T_Y;
        return _ret_128;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 1, .datos = "o" }) == 1)) {
        int _ret_130 = T_O;
        return _ret_130;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 2, .datos = "no" }) == 1)) {
        int _ret_132 = T_NO;
        return _ret_132;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 9, .datos = "verdadero" }) == 1)) {
        int _ret_134 = T_VERDADERO;
        return _ret_134;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 5, .datos = "falso" }) == 1)) {
        int _ret_136 = T_FALSO;
        return _ret_136;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 8, .datos = "inseguro" }) == 1)) {
        int _ret_138 = T_INSEGURO;
        return _ret_138;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 10, .datos = "importar_c" }) == 1)) {
        int _ret_140 = T_IMPORTAR_C;
        return _ret_140;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 7, .datos = "externo" }) == 1)) {
        int _ret_142 = T_EXTERNO;
        return _ret_142;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 9, .datos = "coincidir" }) == 1)) {
        int _ret_144 = T_COINCIDIR;
        return _ret_144;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 8, .datos = "requiere" }) == 1)) {
        int _ret_146 = T_REQUIERE;
        return _ret_146;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 9, .datos = "garantiza" }) == 1)) {
        int _ret_148 = T_GARANTIZA;
        return _ret_148;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 5, .datos = "canal" }) == 1)) {
        int _ret_150 = T_CANAL;
        return _ret_150;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 3, .datos = "asm" }) == 1)) {
        int _ret_152 = T_ASM;
        return _ret_152;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 9, .datos = "constante" }) == 1)) {
        int _ret_154 = T_CONSTANTE;
        return _ret_154;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = 4, .datos = "para" }) == 1)) {
        int _ret_156 = T_PARA;
        return _ret_156;
    }
    int _ret_157 = 0;
    return _ret_157;
}

int es_digito(int c) {
    if ((c >= 48)) {
        if ((c <= 57)) {
            int _ret_163 = 1;
            return _ret_163;
        }
    }
    int _ret_164 = 0;
    return _ret_164;
}

int es_letra(int c) {
    if ((c >= 65)) {
        if ((c <= 90)) {
            int _ret_169 = 1;
            return _ret_169;
        }
    }
    if ((c >= 97)) {
        if ((c <= 122)) {
            int _ret_172 = 1;
            return _ret_172;
        }
    }
    if ((c == 95)) {
        int _ret_174 = 1;
        return _ret_174;
    }
    int _ret_175 = 0;
    return _ret_175;
}

int es_alnum(int c) {
    if ((es_digito(c) == 1)) {
        int _ret_179 = 1;
        return _ret_179;
    }
    if ((es_letra(c) == 1)) {
        int _ret_181 = 1;
        return _ret_181;
    }
    int _ret_182 = 0;
    return _ret_182;
}

#define MAX_TOKENS (16384)
#define MAX_INDENT (64)
typedef struct LexerEstado {
    int ptr_fuente;
    int len_fuente;
    int posicion;
    int linea_actual;
    int columna_actual;
    struct TokenLex* tokens;
    int total_tokens;
    int pila_indent[64];
    int nivel_pila;
    int hay_error;
    CadenaSegura error_mensaje;
    int error_linea;
    int error_columna;
} LexerEstado;

static inline struct LexerEstado LexerEstado_nuevo() {
    struct LexerEstado _r = {0};
    return _r;
}

void lexer_push_token(struct LexerEstado lex, int tipo, int linea, int columna) {
    { /* unsafe */
        if (lex.total_tokens >= 16384) return;
        lex.tokens[lex.total_tokens].tipo = tipo;
        lex.tokens[lex.total_tokens].linea = linea;
        lex.tokens[lex.total_tokens].columna = columna;
        lex.total_tokens = lex.total_tokens + 1;
    }
}

void lexer_error(struct LexerEstado lex, CadenaSegura mensaje, int linea, int columna) {
    lex.hay_error = 1;
    lex.error_mensaje = mensaje;
    lex.error_linea = linea;
    lex.error_columna = columna;
}

void lexer_detectar_idioma(struct LexerEstado lex) {
    { /* unsafe */
        int r = 0;
        r = (lex.len_fuente >= 7 && ((const char*)lex.ptr_fuente)[0] == '#' && ((const char*)lex.ptr_fuente)[1] == 'l' && ((const char*)lex.ptr_fuente)[2] == 'a' && ((const char*)lex.ptr_fuente)[3] == 'n' && ((const char*)lex.ptr_fuente)[4] == 'g' && ((const char*)lex.ptr_fuente)[5] == ':') ? 1 : 0;
        if ((r == 0)) {
            lexer_error(lex, (CadenaSegura){ .longitud = 48, .datos = "Falta declaracion de idioma #lang: en la linea 1" }, 1, 0);
        }
    }
}

void lexer_procesar_indentacion(struct LexerEstado lex, int ptr_linea, int len_linea) {
    { /* unsafe */
        int espacios = 0;
        while (espacios < len_linea && ((const char*)ptr_linea)[espacios] == ' ') { espacios = espacios + 1; };
        if ((espacios < len_linea)) {
            int r = 0;
            r = (((const char*)ptr_linea)[espacios] == '	') ? 1 : 0;
            if ((r == 1)) {
                lexer_error(lex, (CadenaSegura){ .longitud = 25, .datos = "Tabulador prohibido E-101" }, lex.linea_actual, (espacios + 1));
                return;
            }
        }
        if (((espacios % 4) != 0)) {
            lexer_error(lex, (CadenaSegura){ .longitud = 43, .datos = "Indentacion debe ser multiplo de 4 espacios" }, lex.linea_actual, 0);
            return;
        }
        int nivel = (espacios / 4);
        int tope = 0;
        tope = (lex.nivel_pila > 0) ? lex.pila_indent[lex.nivel_pila - 1] : 0;
        if ((nivel > tope)) {
            lex.pila_indent[lex.nivel_pila] = nivel;
            lex.nivel_pila = lex.nivel_pila + 1;
            lexer_push_token(lex, T_INDENTAR, lex.linea_actual, 0);
        }
        if ((nivel < tope)) {
            while ((nivel < tope)) {
                lex.nivel_pila = lex.nivel_pila - 1;
                tope = (lex.nivel_pila > 0) ? lex.pila_indent[lex.nivel_pila - 1] : 0;
                lexer_push_token(lex, T_DESINDENTAR, lex.linea_actual, 0);
            }
        }
    }
}

void lexer_tokenizar_linea(struct LexerEstado lex, int ptr_texto, int len_texto) {
    int i = 0;
    int r = 1;
    while ((r == 1)) {
        { /* unsafe */
            r = (i < len_texto) ? 1 : 0;
            if ((r == 0)) {
                break;
            }
            int c = 0;
            c = (unsigned char)((const char*)ptr_texto)[i];
            if ((c == 32)) {
                i = i + 1;
                continue;
            }
            if ((c == 47)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 47)) {
                        return;
                    }
                }
            }
            if ((c == 34)) {
                i = i + 1;
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((c == 92)) {
                        i = i + 1;
                    } else {
                        if ((c == 34)) {
                            break;
                        }
                    }
                    i = i + 1;
                }
                i = i + 1;
                continue;
            }
            if ((c == 39)) {
                i = i + 1;
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((c == 92)) {
                        i = i + 1;
                    } else {
                        if ((c == 39)) {
                            break;
                        }
                    }
                    i = i + 1;
                }
                i = i + 1;
                continue;
            }
            if ((c >= 48)) {
                if ((c <= 57)) {
                    while ((i < len_texto)) {
                        c = (unsigned char)((const char*)ptr_texto)[i];
                        if ((c < 48)) {
                            break;
                        }
                        if ((c > 57)) {
                            break;
                        }
                        i = i + 1;
                    }
                    continue;
                }
            }
            if ((es_letra(c) == 1)) {
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((es_alnum(c) == 0)) {
                        if ((c != 95)) {
                            break;
                        }
                    }
                    i = i + 1;
                }
                continue;
            }
            if ((c == 43)) {
                lexer_push_token(lex, T_MAS, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 45)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 62)) {
                        lexer_push_token(lex, T_FLECHA, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                    if ((c == 60)) {
                        lexer_push_token(lex, T_FLECHA_IZQ, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                }
                lexer_push_token(lex, T_MENOS, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 61)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 62)) {
                        lexer_push_token(lex, T_FLECHA_DER, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                    if ((c == 61)) {
                        lexer_push_token(lex, T_IGUAL, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                }
                lexer_push_token(lex, T_ASIGNAR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 33)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(lex, T_DISTINTO, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                }
                i = i + 1;
                continue;
            }
            if ((c == 60)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(lex, T_MENOR_IGUAL, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                }
                lexer_push_token(lex, T_MENOR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 62)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(lex, T_MAYOR_IGUAL, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                }
                lexer_push_token(lex, T_MAYOR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 42)) {
                lexer_push_token(lex, T_POR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 47)) {
                lexer_push_token(lex, T_DIV, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 37)) {
                lexer_push_token(lex, T_MOD, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 40)) {
                lexer_push_token(lex, T_PAREN_IZQ, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 41)) {
                lexer_push_token(lex, T_PAREN_DER, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 58)) {
                lexer_push_token(lex, T_DOSPUNTOS, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 44)) {
                lexer_push_token(lex, T_COMA, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 46)) {
                lexer_push_token(lex, T_PUNTO, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 38)) {
                lexer_push_token(lex, T_AMPERSAND, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 59)) {
                lexer_push_token(lex, T_PUNTOCOMA, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            lexer_error(lex, (CadenaSegura){ .longitud = 19, .datos = "Caracter inesperado" }, lex.linea_actual, (i + 1));
            i = i + 1;
        }
        continue;
    }
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

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    synapse_esperar_hilos();
    return 0;
}