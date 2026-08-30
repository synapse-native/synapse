// runtime/core/axon.h â€” Axon: HTTP download + TAR extraction + SHA-256 Lock
// D-9(d) corte 11: extraÃ­do de synapse_rt.c (modularizaciÃ³n, patrÃ³n toml.c R64)
// Manual 6 Â§6.1 (path traversal protection en extracciÃ³n TAR); regla 13 + canon D-9(d).
// Consumido por nucleo/principal.syn (asm blocks) y tests/*.c.
#ifndef SYNAPSE_AXON_H
#define SYNAPSE_AXON_H

#include "synapse_rt_types.h"

CadenaSegura _syn_sha256_hex(CadenaSegura datos);
CadenaSegura _syn_sha256_archivo(const char* ruta);
int _syn_http_get_archivo(CadenaSegura host, int puerto, CadenaSegura ruta, const char* salida_ruta);
int _syn_tar_extraer(const char* tar_ruta, const char* salida_dir);
int _syn_axon_verificar_lock(const char* paquete, const char* version, const char* archivo_ruta, const char* lock_ruta);
int _syn_axon_verificar_firma(const char* tar_ruta, const char* sig_ruta, const char* clave_publica_hex);
void _syn_axon_limpiar_toml(void* n);
int _syn_axon_buscar_local(const char* paquete, const char* version, char* tar_path, int tar_sz, char* extract_dir, int ext_sz);
int _syn_axon_escribir_lock(const char* paquete, const char* version, const char* hash_sha256);

#endif /* SYNAPSE_AXON_H */

// R84 — Serialización binaria de valores (Manual 6 §5.2; tabla Manual 5 §6.3)
// Nombres del manual: serializar_valor / deserializar_valor (convención _syn_axon_).
// ESTRUCTURA (0x08) no soportada por la API genérica (sin esquema en manuales).
#define AXON_T_ENTERO8   0x00
#define AXON_T_ENTERO16  0x01
#define AXON_T_ENTERO32  0x02
#define AXON_T_ENTERO64  0x03
#define AXON_T_DECIMAL32 0x04
#define AXON_T_DECIMAL64 0x05
#define AXON_T_TEXTO     0x06
#define AXON_T_TENSOR    0x07
#define AXON_T_LISTA     0x09
#define AXON_T_MAPA      0x0A
#define AXON_T_NULO      0xC0
#define AXON_T_FALSO     0xC2
#define AXON_T_VERDADERO 0xC3

typedef struct AxonValor AxonValor;
typedef struct { size_t n; AxonValor* elems; } AxonLista;
typedef struct { char* clave; AxonValor* valor; } AxonPar;
typedef struct { size_t n; AxonPar* pares; } AxonMapa;
struct AxonValor {
    int tipo;
    union {
        int64_t  entero;
        double   decimal;
        char*    texto;
        Tensor*  tensor;
        AxonLista lista;
        AxonMapa  mapa;
    } dato;
};

void _syn_axon_serializar_valor(const void* valor, int tipo, uint8_t** buffer, size_t* len);
void* _syn_axon_deserializar_valor(const uint8_t* buffer, size_t len, int* tipo);
void _syn_axon_liberar_valor(void* valor);
