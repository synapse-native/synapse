// cumple Manual 1 5: generador con PGO
// cumple Manual 8 4.1: compilador nativo S2
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
#define verdadero 1
#define falso 0

// --- OO AST node types ---
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
struct DeclaracionVariable;
struct BloqueInseguro;
struct ExprObtenerDireccion;
struct ExprDereferencia;

typedef struct Token { int tipo; CadenaSegura lexema; int linea; int columna; } Token;
typedef struct Nodo { CadenaSegura tipo; } Nodo;
typedef struct ListaNodo { struct Nodo* cabeza; struct ListaNodo* cola; } ListaNodo;
typedef struct Programa { CadenaSegura tipo; struct ListaNodo* sentencias; } Programa;

#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096

#define _GEN_TMP_SIZE (4096)
#include "librerias/embedded_libs.h"

char _gen_tmp_buf[4096];

char _G_emit_buf[1048576];
int _G_emit_pos = 0;
FILE* _G_fp = NULL;

extern int _G_indent;

const char* _G_mt(const char* st);
void _G_vest(struct DefinicionEstructura* n);

#define TAG_OK 0
#define TAG_ERR 1
#define TAG_ALGUNO 0
#define TAG_NINGUNO 1

// --- Helpers de serialización primitiva ---
static inline void* _synapse_box_int(int v) { return (void*)(intptr_t)v; }
static inline int _synapse_unbox_int(void* p) { return (int)(intptr_t)p; }
static inline void* _synapse_box_float(float v) {
    float* _p = (float*)malloc(sizeof(float));
    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo\\n"); exit(1); }
    *_p = v;
    return (void*)_p;
}
static inline float _synapse_unbox_float(void* p) {
    float _v = *(float*)p;
    free(p);
    return _v;
}

extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void pool_free(void* ptr);
extern void* pool_alloc(size_t size);
extern void pool_destroy(void);
extern void escribir(CadenaSegura contenido);
extern void escribir_linea(CadenaSegura contenido);
extern CadenaSegura leer_linea(void);
extern Canal abrir(CadenaSegura ruta, CadenaSegura modo);
extern CadenaSegura leer(Canal canal);
extern void cerrar_archivo(Canal canal);
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

typedef struct { int es_ok; union {
void* ok_valor; const char* err_mensaje;
} datos; } Resultado_T;
typedef struct CanalConcurrencia CanalConcurrencia;
extern CanalConcurrencia* canal_crear(uint32_t capacidad);
extern void canal_enviar(CanalConcurrencia* canal, void* paquete);
extern void* canal_recibir(CanalConcurrencia* canal);
extern void canal_destruir(CanalConcurrencia* canal);
extern void cerrar(CanalConcurrencia* canal);
// --- Deteccion SIMD unificada (delegada al runtime synapse_rt.o) ---
extern void _simd_detectar(void);

// --- Contratos (requiere/garantiza) ---
#ifdef SYNAPSE_RELEASE
#define assert_contrato(expr, msg) ((void)0)
#else
#define assert_contrato(expr, msg) \
    do { if (!(expr)) { \
        fprintf(stderr, "CONTRATO: %s en %%s:%%d\\n", \
                msg, __FILE__, __LINE__); \
        exit(1); }} while(0)
#endif

int _g_argc;
char** _g_argv;
int _argc() { return _g_argc; }

CadenaSegura _argv(int i) {
    if (i < 0 || i >= _g_argc) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_g_argv[i]), .datos = _g_argv[i] };
}

void salir(int codigo) { exit(codigo); }

CadenaSegura concat(CadenaSegura a, CadenaSegura b) {
    int _tl = a.longitud + b.longitud;
    char* _buf = (char*)malloc(_tl + 1);
    if (!_buf) { fprintf(stderr,"Error: malloc fallo en concat()\\n"); exit(1); }
    memcpy(_buf, a.datos, a.longitud);
    memcpy(_buf + a.longitud, b.datos, b.longitud);
    _buf[_tl] = 0;
    return (CadenaSegura){_tl, _buf};
}

int pgo_estado_administrar(int modo);
void pgo_inicializar(void);
int pgo_nuevo_contador(void);
int pgo_total_contadores(void);
int pgo_emitir_contadores_funcion(struct GeneradorCEst est, int num_ctrs);
void pgo_emitir_incremento_bb(struct GeneradorCEst est);
void pgo_emitir_incremento_id(struct GeneradorCEst est, int id);
void pgo_emitir_volcado(struct GeneradorCEst est, int num_ctrs);
void pgo_registrar_atexit(struct GeneradorCEst est);
void pgo_finalizar(struct GeneradorCEst est);
void pgo_instrumentar_if_true(struct GeneradorCEst est);
void pgo_instrumentar_if_false(struct GeneradorCEst est);
void pgo_instrumentar_while_body(struct GeneradorCEst est);
void pgo_instrumentar_for_body(struct GeneradorCEst est);

int pgo_estado_administrar(int modo) {
    int r;
    r = 0;
    { /* unsafe */
        // PGO: Administrador de estado unico;
        static int _pgo_syn_id = 0;
        static int _pgo_syn_total = 0;
        if (modo == 0) {
            // Inicializar: resetear contadores;
            _pgo_syn_id = 0;
            _pgo_syn_total = 0;
            r = -1;
        } else if (modo == 1) {
            // Siguiente: asignar y retornar ID;
            r = _pgo_syn_id;
            _pgo_syn_id = _pgo_syn_id + 1;
            _pgo_syn_total = _pgo_syn_id;
        } else if (modo == 2) {
            // Total: retornar contador actual;
            r = _pgo_syn_total;
        }
    }
    int _ret_66 = r;
    return _ret_66;
}

void pgo_inicializar(void) {
    int _;
    _ = pgo_estado_administrar(0);
}

int pgo_nuevo_contador(void) {
    int _ret_82 = pgo_estado_administrar(1);
    return _ret_82;
}

int pgo_total_contadores(void) {
    int _ret_89 = pgo_estado_administrar(2);
    return _ret_89;
}

int pgo_emitir_contadores_funcion(struct GeneradorCEst est, int num_ctrs) {
    int id_base;
    id_base = pgo_nuevo_contador();
    { /* unsafe */
        // PGO: Emitir contadores estaticos para funcion;
        int _base = id_base;
        int _n = num_ctrs;
        char _tmp[256];
        gen_emitir_str(est, "    /* [PGO] contadores de funcion */");
        for (int _i = 0; _i < _n; _i++) {
            snprintf(_tmp, 256, "    static uint64_t __pgo_counter_%d = 0;", _base + _i);
            gen_emitir_str(est, _tmp);
        }
    }
    int _ret_121 = id_base;
    return _ret_121;
}

void pgo_emitir_incremento_bb(struct GeneradorCEst est) {
    int id_ctr;
    id_ctr = pgo_nuevo_contador();
    { /* unsafe */
        // PGO: Emitir incremento en frontera de bloque basico;
        int _id = id_ctr;
        char _tmp[128];
        snprintf(_tmp, 128, "    __pgo_counter_%d++;  /* [PGO] */", _id);
        gen_emitir_str(est, _tmp);
    }
}

void pgo_emitir_incremento_id(struct GeneradorCEst est, int id) {
    { /* unsafe */
        // PGO: Emitir incremento para contador especifico;
        int _id = id;
        char _tmp[128];
        snprintf(_tmp, 128, "    __pgo_counter_%d++;  /* [PGO] */", _id);
        gen_emitir_str(est, _tmp);
    }
}

void pgo_emitir_volcado(struct GeneradorCEst est, int num_ctrs) {
    { /* unsafe */
        // PGO: Emitir funcion de volcado de contadores;
        int _total = num_ctrs;
        char _tmp[512];

        gen_emitir_str(est, "");
        gen_emitir_str(est, "// ================================================");
        gen_emitir_str(est, "// PGO: Volcado automatico de contadores");
        gen_emitir_str(est, "// ================================================");
        gen_emitir_str(est, "static int _pgo_ya_volcado = 0;");
        gen_emitir_str(est, "void __pgo_dump(void) {");
        gen_emitir_str(est, "    if (_pgo_ya_volcado) return;");
        gen_emitir_str(est, "    _pgo_ya_volcado = 1;");
        gen_emitir_str(est, "    FILE* _pf = fopen(\"synapse.profdata\", \"a\");");
        gen_emitir_str(est, "    if (!_pf) return;");
        gen_emitir_str(est, "    // Cabecera: version y total de contadores");
        snprintf(_tmp, 512, "    fprintf(_pf, \"synapse_pgo_v1 %%d\\\\n\", %d);", _total);
        gen_emitir_str(est, _tmp);
        gen_emitir_str(est, "    // Volcar cada contador");
        // Emitir declaraciones externas y fprintf para cada contador;
        for (int _i = 0; _i < _total; _i++) {
            snprintf(_tmp, 512, "    extern uint64_t __pgo_counter_%d;", _i);
            gen_emitir_str(est, _tmp);
        }
        for (int _i = 0; _i < _total; _i++) {
            snprintf(_tmp, 512, "    fprintf(_pf, \"%%llu\\\\n\", __pgo_counter_%d);", _i);
            gen_emitir_str(est, _tmp);
        }
        gen_emitir_str(est, "    fclose(_pf);");
        gen_emitir_str(est, "}");
        gen_emitir_str(est, "");
    }
}

void pgo_registrar_atexit(struct GeneradorCEst est) {
    { /* unsafe */
        gen_emitir_str(est, "    atexit(__pgo_dump);  /* [PGO] Registro de volcado */");
    }
}

void pgo_finalizar(struct GeneradorCEst est) {
    int total;
    total = pgo_total_contadores();
    if ((total > 0)) {
        pgo_emitir_volcado(est, total);
        pgo_registrar_atexit(est);
    }
}

void pgo_instrumentar_if_true(struct GeneradorCEst est) {
    pgo_emitir_incremento_bb(est);
}

void pgo_instrumentar_if_false(struct GeneradorCEst est) {
    pgo_emitir_incremento_bb(est);
}

void pgo_instrumentar_while_body(struct GeneradorCEst est) {
    pgo_emitir_incremento_bb(est);
}

void pgo_instrumentar_for_body(struct GeneradorCEst est) {
    pgo_emitir_incremento_bb(est);
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    synapse_esperar_hilos();
    pool_destroy();
    return 0;
}