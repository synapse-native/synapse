// axon_rt.c â€” Axon package manager runtime
//
// Fase 6.1: TOML, TAR, SHA-256, Ed25519, SemVer, lock.
// Manual 8 Â§4.3-4.4 (gestor de paquetes Axon); Manual 6 Â§6.1 (path
// traversal protection en extracciÃ³n TAR).
//
// This file contains the Axon-specific functions. Shared runtime
// functions (TOML parse, SHA-256, TAR, HTTP, lock, Ed25519 verify)
// come from the modular runtime via extern declarations. This file
// adds Axon-specific signing, key generation, and combined
// package verification.
//
// Compilar: gcc -c axon/axon_rt.c -o axon_rt.o -I. -Iruntime/core
// Linkear: gcc programa.c synapse_rt.o synapse_rt_memory.o
//          synapse_rt_concurrency.o axon_rt.o tweetnacl.o -o programa -lpthread

#include "synapse_rt_types.h"
#include "axon/tweetnacl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

// ============================================================
// TOML types (local definition, same layout as synapse_rt.c)
// ============================================================
typedef struct ParToml ParToml;
typedef struct NodoToml NodoToml;

struct ParToml {
    CadenaSegura clave;
    NodoToml* valor;
};

struct NodoToml {
    int tipo;           // -1=Error, 0=Nulo, 1=Tabla, 2=Cadena, 3=TablaEnLinea
    CadenaSegura valor_str;
    ParToml* pares;
    int longitud;
};

// ============================================================
// Extern: functions provided by modular runtime (synapse_rt.c)
// ============================================================
extern NodoToml _toml_parse(CadenaSegura entrada);
extern void _toml_nodo_liberar(NodoToml n);
extern NodoToml _toml_object_get(NodoToml nodo, CadenaSegura clave);

// ============================================================
// Extern: SHA-256 (provided by synapse_rt.c / runtime/core/cripto.c)
// ============================================================
extern CadenaSegura _syn_sha256_hex(CadenaSegura datos);
extern CadenaSegura _syn_sha256_archivo(const char* ruta);
extern CadenaSegura _syn_sha256_texto(CadenaSegura datos);

// ============================================================
// Extern: Ed25519 verify (provided by runtime/core/cripto.c)
// ============================================================
extern int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);

// ============================================================
// Extern: TAR extraction, HTTP download, lock (runtime/core/axon.c)
// ============================================================
extern int _syn_tar_extraer(const char* tar_ruta, const char* salida_dir);
extern int _syn_http_get_archivo(CadenaSegura host, int puerto, CadenaSegura ruta, const char* salida_ruta);
extern int _syn_axon_verificar_lock(const char* paquete, const char* version, const char* archivo_ruta, const char* lock_ruta);
extern int _syn_axon_verificar_firma(const char* tar_ruta, const char* sig_ruta, const char* clave_publica_hex);
extern int _syn_axon_escribir_lock(const char* paquete, const char* version, const char* hash_sha256);
extern int _syn_axon_buscar_local(const char* paquete, const char* version,
                                   char* tar_path, int tar_sz,
                                   char* extract_dir, int ext_sz);

// ============================================================
// SemVer helpers (static â€” local to this TU)
// ============================================================

/* _syn_parse_ver: parse "x.y.z" version string into components */
static int _syn_parse_ver(const char* v, int* maj, int* min, int* pat) {
    *maj = 0; *min = 0; *pat = 0;  // init before sscanf (partial match = 0 for rest)
    if (!v || !*v) return 0;
    return sscanf(v, "%d.%d.%d", maj, min, pat) >= 1;
}

/* _syn_semver_match: SemVer constraint matching.
 * Supports: exact, ^caret, ~tilde constraints.
 * Retorna: 1 si la version cumple la constraint, 0 en caso contrario.
 */
int _syn_semver_match(const char* constraint, const char* version) {
    if (!constraint || !*constraint || !version || !*version) return 0;

    int cmaj = 0, cmin = 0, cpat = 0;
    int vmaj = 0, vmin = 0, vpat = 0;

    char prefix = constraint[0];
    const char* cver = constraint;
    if (prefix == '^' || prefix == '~') {
        cver = constraint + 1;
    } else {
        prefix = 0;  // exact match
    }

    if (!_syn_parse_ver(cver, &cmaj, &cmin, &cpat)) return 0;
    if (!_syn_parse_ver(version, &vmaj, &vmin, &vpat)) return 0;

    if (prefix == '^') {
        // Caret: compatible releases.
        int upper_maj = cmaj, upper_min = cmin, upper_pat = cpat;
        if (cmaj > 0) {
            upper_maj = cmaj + 1; upper_min = 0; upper_pat = 0;
        } else if (cmin > 0) {
            upper_min = cmin + 1; upper_pat = 0;
        } else {
            upper_pat = cpat + 1;
        }
        long long lower = (long long)cmaj * 1000000 + cmin * 1000 + cpat;
        long long upper = (long long)upper_maj * 1000000 + upper_min * 1000 + upper_pat;
        long long actual = (long long)vmaj * 1000000 + vmin * 1000 + vpat;
        return (actual >= lower && actual < upper) ? 1 : 0;
    }

    if (prefix == '~') {
        // Tilde: patch-level. ~1.2.3 means >=1.2.3 and <1.3.0
        if (vmaj != cmaj) return 0;
        if (vmin != cmin) return 0;
        return (vpat >= cpat) ? 1 : 0;
    }

    // Exact version
    return (cmaj == vmaj && cmin == vmin && cpat == vpat) ? 1 : 0;
}

// ============================================================
// Axon: manifest validation
// ============================================================

/* _syn_axon_validar_manifiesto: valida que un archivo TOML contenga
 * la estructura minima de manifiesto Axon ([paquete] con nombre, version,
 * autor, tipo, punto_entrada).
 * Retorna: 0 si es valido, -1 si hay error.
 */
int _syn_axon_validar_manifiesto(const char* toml_path) {
    FILE* f = fopen(toml_path, "rb");
    if (!f) {
        fprintf(stderr, "[Axon] ERR_MANIFEST: no se pudo abrir %s\n", toml_path);
        return -1;
    }
    fseek(f, 0, SEEK_END);
    long fsz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (fsz <= 0) { fclose(f); return -1; }
    char* buf = (char*)malloc((size_t)fsz + 1);
    if (!buf) { fclose(f); return -1; }
    size_t nread = fread(buf, 1, (size_t)fsz, f);
    fclose(f);
    if ((long)nread != fsz) { free(buf); return -1; }
    buf[fsz] = 0;

    CadenaSegura input = { .longitud = (int)fsz, .datos = buf };
    NodoToml root = _toml_parse(input);
    free(buf);

    if (root.tipo < 0) {
        fprintf(stderr, "[Axon] ERR_MANIFEST: error de parseo en %s\n", toml_path);
        if (root.valor_str.datos) free((void*)root.valor_str.datos);
        return -1;
    }

    int has_paquete = 0, has_nombre = 0, has_version = 0, has_autor = 0;
    int has_tipo = 0, has_punto_entrada = 0;
    int valid = 1;

    for (int i = 0; i < root.longitud; i++) {
        ParToml* sec = &root.pares[i];
        int slen = sec->clave.longitud;
        const char* sname = sec->clave.datos;

        if (slen == 7 && memcmp(sname, "paquete", 7) == 0) {
            has_paquete = 1;
            NodoToml* paq = sec->valor;
            if (paq->tipo == 1 || paq->tipo == 3) {
                for (int j = 0; j < paq->longitud; j++) {
                    ParToml* fld = &paq->pares[j];
                    int flen = fld->clave.longitud;
                    const char* fname = fld->clave.datos;
                    if (flen == 6 && memcmp(fname, "nombre", 6) == 0) {
                        has_nombre = 1;
                    } else if (flen == 7 && memcmp(fname, "version", 7) == 0) {
                        has_version = 1;
                    } else if (flen == 5 && memcmp(fname, "autor", 5) == 0) {
                        has_autor = 1;
                    } else if (flen == 5 && memcmp(fname, "tipo", 5) == 0) {
                        has_tipo = 1;
                    } else if (flen == 13 && memcmp(fname, "punto_entrada", 13) == 0) {
                        has_punto_entrada = 1;
                    }
                }
            }
        }

        // Optional: [dependencias] section â€” no validation required
        // Optional: [parametros] section â€” no validation required
    }

    if (!has_paquete) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta seccion [paquete]\n"); valid = 0; }
    if (!has_nombre) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta 'nombre' en [paquete]\n"); valid = 0; }
    if (!has_version) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta 'version' en [paquete]\n"); valid = 0; }
    if (!has_autor) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta 'autor' en [paquete]\n"); valid = 0; }
    if (!has_tipo) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta 'tipo' en [paquete]\n"); valid = 0; }
    if (!has_punto_entrada) { fprintf(stderr, "[Axon] ERR_MANIFEST: falta 'punto_entrada' en [paquete]\n"); valid = 0; }

    _toml_nodo_liberar(root);
    return valid ? 0 : -1;
}

// ============================================================
// Ed25519 signing (Axon-specific, uses tweetnacl directly)
// ============================================================

/* _syn_ed25519_generar_par: generate Ed25519 keypair.
 * Writes 32-byte public key to pk_out and 64-byte secret key to sk_out.
 * Both buffers must be at least 32/64 bytes.
 * Retorna: 0 OK, -1 error.
 */
int _syn_ed25519_generar_par(unsigned char* pk_out, unsigned char* sk_out) {
    if (!pk_out || !sk_out) return -1;
    return crypto_sign_ed25519_keypair(pk_out, sk_out);
}

/* _syn_ed25519_firmar: sign a message with Ed25519 secret key.
 * Allocates a 64-byte signature buffer (*out_len = 64).
 * Caller must free the returned buffer.
 * Retorna: pointer to 64-byte signature, or NULL on error.
 */
unsigned char* _syn_ed25519_firmar(CadenaSegura mensaje,
                                    const unsigned char* clave_secreta,
                                    unsigned long long* out_len) {
    if (!mensaje.datos || !clave_secreta || !out_len) return NULL;
    *out_len = 0;
    unsigned long long smlen = 0;
    unsigned char* sm = (unsigned char*)malloc((size_t)(mensaje.longitud + 64));
    if (!sm) return NULL;
    int rc = crypto_sign_ed25519(sm, &smlen,
                                (const unsigned char*)mensaje.datos,
                                (unsigned long long)mensaje.longitud,
                                clave_secreta);
    if (rc != 0) { free(sm); return NULL; }
    // signature is the first 64 bytes
    unsigned char* sig = (unsigned char*)malloc(64);
    if (!sig) { free(sm); return NULL; }
    memcpy(sig, sm, 64);
    *out_len = 64;
    free(sm);
    return sig;
}

// ============================================================
// Axon: combined package verification (SHA-256 + Ed25519 + lock)
// ============================================================

/* _syn_axon_verificar_paquete: download (or use local) + verify a package.
 * Steps:
 *   1. Buscar localmente (cache/oficiales/AXON_PATH)
 *   2. Si no estÃ¡, HTTP download (host, puerto, ruta â†’ .tar)
 *   3. Verify SHA-256 hash against expected (or compute + write lock)
 *   4. Verify Ed25519 signature (if clave_publica_hex provided)
 *   5. Extract TAR (con path traversal protection)
 * Returns: 0 OK, -1 error.
 */
int _syn_axon_verificar_paquete(const char* paquete, const char* version,
                                 const char* host, int puerto, const char* ruta_http,
                                 const char* hash_esperado,
                                 const char* clave_publica_hex) {
    char tar_path[512];
    char extract_dir[512];

    // 1. Try local first
    int local_rc = _syn_axon_buscar_local(paquete, version, tar_path, sizeof(tar_path),
                                           extract_dir, sizeof(extract_dir));
    if (local_rc < 0) {
        // Not found locally: download via HTTP
        if (!host || !ruta_http) {
            fprintf(stderr, "[Axon] ERR_FETCH: paquete '%s' no encontrado local y no hay host HTTP\n", paquete);
            return -1;
        }
        CadenaSegura h = { .longitud = (int)strlen(host), .datos = host };
        CadenaSegura rp = { .longitud = (int)strlen(ruta_http), .datos = ruta_http };
        snprintf(tar_path, sizeof(tar_path), ".axon_cache/%s.tar", paquete);
        int dl_rc = _syn_http_get_archivo(h, puerto, rp, tar_path);
        if (dl_rc != 0) {
            fprintf(stderr, "[Axon] ERR_FETCH: fallo download HTTP para '%s'\n", paquete);
            return -1;
        }
        fprintf(stderr, "[Axon] Download: %s â†’ %s\n", ruta_http, tar_path);
    } else {
        fprintf(stderr, "[Axon] Local: encontrado (rc=%d) en %s\n", local_rc, tar_path);
    }

    // 2. Verify SHA-256
    if (hash_esperado && *hash_esperado) {
        int vrc = _syn_axon_verificar_lock(paquete, version, tar_path, "axon.lock");
        if (vrc != 0) {
            fprintf(stderr, "[Axon] ERR_AXON_COMPROMISED: hash mismatch para '%s'\n", paquete);
            return -1;
        }
    } else {
        // No expected hash: write to lock
        CadenaSegura hash = _syn_sha256_archivo(tar_path);
        if (hash.longitud == 0) {
            fprintf(stderr, "[Axon] ERR_HASH: no se pudo calcular SHA-256 de %s\n", tar_path);
            return -1;
        }
        _syn_axon_escribir_lock(paquete, version, hash.datos);
        free((void*)hash.datos);
    }

    // 3. Verify Ed25519 signature (if public key provided)
    if (clave_publica_hex && *clave_publica_hex) {
        char sig_path[512];
        snprintf(sig_path, sizeof(sig_path), "%s.sig", tar_path);
        int src = _syn_axon_verificar_firma(tar_path, sig_path, clave_publica_hex);
        if (src != 0) {
            fprintf(stderr, "[Axon] ERR_AXON_COMPROMISED: firma Ed25519 invalida para '%s'\n", paquete);
            return -1;
        }
        fprintf(stderr, "[Axon] Signature verificada: %s\n", paquete);
    }

    // 4. Extract TAR (path traversal protection inside)
    int trc = _syn_tar_extraer(tar_path, extract_dir);
    if (trc != 0) {
        fprintf(stderr, "[Axon] ERR_TAR: fallo extracciÃ³n de %s\n", tar_path);
        return -1;
    }
    fprintf(stderr, "[Axon] Paquete instalado: %s v%s â†’ %s\n", paquete, version, extract_dir);
    return 0;
}

// ============================================================
// R84 ï¿½ Serializaciï¿½n binaria de valores (Manual 6 ï¿½5.2;
// tabla de tipos Manual 5 ï¿½6.3 / Manual 6 ï¿½5.1)
//
// Codificaciï¿½n auto-descriptiva: cada valor va precedido por su byte de tipo.
// Enteros: serializar_valor emite el ancho solicitado en `tipo` (p.ej. el
// ejemplo del Manual 5 ï¿½6.3 usa 0x02+4B para 42); deserializar_valor acepta
// cualquier ancho y devuelve AXON_T_ENTERO64 normalizado.
// ESTRUCTURA (0x08) no se implementa en la API genï¿½rica: los manuales no
// definen esquema de campos ("serializaciï¿½n secuencial" requiere metadatos).
// ============================================================

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
    int tipo;            // AXON_T_*
    union {
        int64_t  entero;          // 0x00-0x03 (normalizado a 64 bits)
        double   decimal;         // 0x04 (float), 0x05 (double)
        char*    texto;           // 0x06 (NUL-terminado, malloc)
        Tensor*  tensor;          // 0x07
        AxonLista lista;          // 0x09
        AxonMapa  mapa;           // 0x0A
    } dato;
};

static void _ax_put_u32be(uint8_t* p, uint32_t v) {
    p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >> 8);  p[3] = (uint8_t)v;
}
static uint32_t _ax_get_u32be(const uint8_t* p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}
static void _ax_put_u64be(uint8_t* p, uint64_t v) {
    for (int i = 0; i < 8; i++) p[i] = (uint8_t)(v >> (56 - 8 * i));
}
static uint64_t _ax_get_u64be(const uint8_t* p) {
    uint64_t v = 0;
    for (int i = 0; i < 8; i++) v = (v << 8) | p[i];
    return v;
}

// Tamano serializado de un valor (para reservar el buffer de una pasada)
// Puntero al dato crudo segun el tipo del AxonValor (para recursion)
static const void* _ax_dato(const AxonValor* e) {
    switch (e->tipo) {
    case AXON_T_TEXTO:  return e->dato.texto;
    case AXON_T_TENSOR: return e->dato.tensor;
    case AXON_T_LISTA:  return &e->dato.lista;
    case AXON_T_MAPA:   return &e->dato.mapa;
    default:            return &e->dato.entero;
    }
}

static size_t _ax_sizeof_valor(int tipo, const void* v) {
    switch (tipo) {
    case AXON_T_NULO: case AXON_T_FALSO: case AXON_T_VERDADERO: return 1;
    case AXON_T_ENTERO8:   return 2;
    case AXON_T_ENTERO16:  return 3;
    case AXON_T_ENTERO32:  return 5;
    case AXON_T_ENTERO64:  return 9;
    case AXON_T_DECIMAL32: return 5;
    case AXON_T_DECIMAL64: return 9;
    case AXON_T_TEXTO:     return 5 + strlen((const char*)v);
    case AXON_T_TENSOR: {
        const Tensor* t = (const Tensor*)v;
        return 1 + 8 + (size_t)t->filas * t->columnas * 4;
    }
    case AXON_T_LISTA: {
        const AxonLista* l = (const AxonLista*)v;
        size_t s = 1 + 4;
        for (size_t i = 0; i < l->n; i++)
            s += _ax_sizeof_valor(l->elems[i].tipo, _ax_dato(&l->elems[i]));
        return s;
    }
    case AXON_T_MAPA: {
        const AxonMapa* m = (const AxonMapa*)v;
        size_t s = 1 + 4;
        for (size_t i = 0; i < m->n; i++) {
            s += _ax_sizeof_valor(AXON_T_TEXTO, m->pares[i].clave);
            s += _ax_sizeof_valor(m->pares[i].valor->tipo, _ax_dato(m->pares[i].valor));
        }
        return s;
    }
    default: return 0; // 0x08 estructura y desconocidos no soportados
    }
}

static uint8_t* _ax_escribir_valor(uint8_t* p, int tipo, const void* v) {
    *p++ = (uint8_t)tipo;
    switch (tipo) {
    case AXON_T_NULO: break;
    case AXON_T_FALSO: break;
    case AXON_T_VERDADERO: break;
    case AXON_T_ENTERO8:
        *p++ = (uint8_t)(*(const int64_t*)v & 0xFF);
        break;
    case AXON_T_ENTERO16: {
        uint16_t x = (uint16_t)(*(const int64_t*)v & 0xFFFF);
        p[0] = (uint8_t)(x >> 8); p[1] = (uint8_t)x; p += 2;
        break;
    }
    case AXON_T_ENTERO32:
        _ax_put_u32be(p, (uint32_t)(*(const int64_t*)v & 0xFFFFFFFFu)); p += 4;
        break;
    case AXON_T_ENTERO64:
        _ax_put_u64be(p, (uint64_t)*(const int64_t*)v); p += 8;
        break;
    case AXON_T_DECIMAL32: {
        float f = (float)*(const double*)v;
        uint32_t bits; memcpy(&bits, &f, 4);
        _ax_put_u32be(p, bits); p += 4;
        break;
    }
    case AXON_T_DECIMAL64: {
        uint64_t bits; memcpy(&bits, v, 8);
        _ax_put_u64be(p, bits); p += 8;
        break;
    }
    case AXON_T_TEXTO: {
        size_t lon = strlen((const char*)v);
        _ax_put_u32be(p, (uint32_t)lon); p += 4;
        memcpy(p, v, lon); p += lon;
        break;
    }
    case AXON_T_TENSOR: {
        const Tensor* t = (const Tensor*)v;
        _ax_put_u32be(p, t->filas);  p += 4;
        _ax_put_u32be(p, t->columnas); p += 4;
        for (size_t i = 0; i < (size_t)t->filas * t->columnas; i++) {
            uint32_t bits; memcpy(&bits, &t->datos[i], 4);
            _ax_put_u32be(p, bits); p += 4;
        }
        break;
    }
    case AXON_T_LISTA: {
        const AxonLista* l = (const AxonLista*)v;
        _ax_put_u32be(p, (uint32_t)l->n); p += 4;
        for (size_t i = 0; i < l->n; i++)
            p = _ax_escribir_valor(p, l->elems[i].tipo, _ax_dato(&l->elems[i]));
        break;
    }
    case AXON_T_MAPA: {
        const AxonMapa* m = (const AxonMapa*)v;
        _ax_put_u32be(p, (uint32_t)m->n); p += 4;
        for (size_t i = 0; i < m->n; i++) {
            p = _ax_escribir_valor(p, AXON_T_TEXTO, m->pares[i].clave);
            p = _ax_escribir_valor(p, m->pares[i].valor->tipo, _ax_dato(m->pares[i].valor));
        }
        break;
    }
    default: break;
    }
    return p;
}

void _syn_axon_serializar_valor(const void* valor, int tipo,
                                 uint8_t** buffer, size_t* len) {
    *buffer = NULL; *len = 0;
    size_t sz = _ax_sizeof_valor(tipo, valor);
    if (sz == 0) return;
    uint8_t* buf = (uint8_t*)malloc(sz);
    if (!buf) return;
    uint8_t* fin = _ax_escribir_valor(buf, tipo, valor);
    *buffer = buf; *len = (size_t)(fin - buf);
}

// Deserializaciï¿½n recursiva; consume bytes avanzando el cursor.
static const uint8_t* _ax_leer_valor(const uint8_t* p, const uint8_t* fin,
                                      AxonValor* out);

static const uint8_t* _ax_leer_valor(const uint8_t* p, const uint8_t* fin,
                                      AxonValor* out) {
    if (p >= fin) return NULL;
    int tipo = *p++;
    out->tipo = tipo;
    memset(&out->dato, 0, sizeof(out->dato));
    switch (tipo) {
    case AXON_T_NULO: case AXON_T_FALSO: case AXON_T_VERDADERO:
        out->dato.entero = (tipo == AXON_T_VERDADERO);
        return p;
    case AXON_T_ENTERO8:  if (fin - p < 1) return NULL;
        out->dato.entero = (int64_t)(int8_t)*p++; return p;
    case AXON_T_ENTERO16: if (fin - p < 2) return NULL;
        out->dato.entero = (int16_t)((p[0] << 8) | p[1]); p += 2; return p;
    case AXON_T_ENTERO32: if (fin - p < 4) return NULL;
        out->dato.entero = (int32_t)_ax_get_u32be(p); p += 4; return p;
    case AXON_T_ENTERO64: if (fin - p < 8) return NULL;
        out->dato.entero = (int64_t)_ax_get_u64be(p); p += 8; return p;
    case AXON_T_DECIMAL32: if (fin - p < 4) return NULL; {
        uint32_t bits = _ax_get_u32be(p); float f;
        memcpy(&f, &bits, 4);
        out->tipo = AXON_T_DECIMAL64;
        out->dato.decimal = (double)f; p += 4; return p;
    }
    case AXON_T_DECIMAL64: if (fin - p < 8) return NULL; {
        uint64_t bits = _ax_get_u64be(p);
        memcpy(&out->dato.decimal, &bits, 8);
        p += 8; return p;
    }
    case AXON_T_TEXTO: if (fin - p < 4) return NULL; {
        uint32_t lon = _ax_get_u32be(p); p += 4;
        if ((size_t)(fin - p) < lon) return NULL;
        char* s = (char*)malloc(lon + 1);
        if (!s) return NULL;
        memcpy(s, p, lon); s[lon] = 0;
        out->dato.texto = s; p += lon; return p;
    }
    case AXON_T_TENSOR: if (fin - p < 8) return NULL; {
        Tensor* t = (Tensor*)calloc(1, sizeof(Tensor));
        if (!t) return NULL;
        t->filas = _ax_get_u32be(p); p += 4;
        t->columnas = _ax_get_u32be(p); p += 4;
        size_t n = (size_t)t->filas * t->columnas;
        if ((size_t)(fin - p) < n * 4) { free(t); return NULL; }
        t->datos = (float*)malloc(n * 4);
        if (!t->datos) { free(t); return NULL; }
        for (size_t i = 0; i < n; i++) {
            uint32_t bits = _ax_get_u32be(p); p += 4;
            memcpy(&t->datos[i], &bits, 4);
        }
        t->es_mapeado = 0;
        out->dato.tensor = t; return p;
    }
    case AXON_T_LISTA: if (fin - p < 4) return NULL; {
        uint32_t n = _ax_get_u32be(p); p += 4;
        out->dato.lista.n = 0;
        out->dato.lista.elems = n ? (AxonValor*)calloc(n, sizeof(AxonValor)) : NULL;
        for (uint32_t i = 0; i < n; i++) {
            p = _ax_leer_valor(p, fin, &out->dato.lista.elems[i]);
            if (!p) return NULL;
            out->dato.lista.n++;
        }
        return p;
    }
    case AXON_T_MAPA: if (fin - p < 4) return NULL; {
        uint32_t n = _ax_get_u32be(p); p += 4;
        out->dato.mapa.n = 0;
        out->dato.mapa.pares = n ? (AxonPar*)calloc(n, sizeof(AxonPar)) : NULL;
        for (uint32_t i = 0; i < n; i++) {
            AxonValor k;
            p = _ax_leer_valor(p, fin, &k);
            if (!p || k.tipo != AXON_T_TEXTO) return NULL;
            out->dato.mapa.pares[i].clave = k.dato.texto;
            AxonValor* v = (AxonValor*)malloc(sizeof(AxonValor));
            if (!v) return NULL;
            p = _ax_leer_valor(p, fin, v);
            if (!p) return NULL;
            out->dato.mapa.pares[i].valor = v;
            out->dato.mapa.n++;
        }
        return p;
    }
    default:
        return NULL; // 0x08 estructura y tipos desconocidos
    }
}

void* _syn_axon_deserializar_valor(const uint8_t* buffer, size_t len, int* tipo) {
    if (!buffer || len == 0 || !tipo) return NULL;
    AxonValor* v = (AxonValor*)malloc(sizeof(AxonValor));
    if (!v) return NULL;
    const uint8_t* fin = buffer + len;
    if (!_ax_leer_valor(buffer, fin, v)) {
        free(v);
        return NULL;
    }
    *tipo = v->tipo;
    return v;
}

// Libera SOLO los recursos apuntados por el valor (no la propia struct).
// Necesario porque los elementos de una lista son interiores al array.
static void _ax_liberar_contenido(AxonValor* v) {
    switch (v->tipo) {
    case AXON_T_TEXTO: free(v->dato.texto); break;
    case AXON_T_TENSOR: free(v->dato.tensor->datos); free(v->dato.tensor); break;
    case AXON_T_LISTA:
        for (size_t i = 0; i < v->dato.lista.n; i++)
            _ax_liberar_contenido(&v->dato.lista.elems[i]);
        free(v->dato.lista.elems);
        break;
    case AXON_T_MAPA:
        for (size_t i = 0; i < v->dato.mapa.n; i++) {
            free(v->dato.mapa.pares[i].clave);
            if (v->dato.mapa.pares[i].valor) {
                _ax_liberar_contenido(v->dato.mapa.pares[i].valor);
                free(v->dato.mapa.pares[i].valor);
            }
        }
        free(v->dato.mapa.pares);
        break;
    default: break;
    }
}

void _syn_axon_liberar_valor(void* valor) {
    AxonValor* v = (AxonValor*)valor;
    if (!v) return;
    _ax_liberar_contenido(v);
    free(v);
}

// ============================================================
// 5.3. Handshake Ed25519 (Zero-Trust) + crypto_kx session key
// (Manual 6 §5.3)
//
// Flujo:
//   1. Cliente envía HELLO = [nonce(32)] [pk(32)] [firma(64)]
//   2. Servidor verifica firma Ed25519 sobre el nonce
//   3. Si válido, servidor responde HELLO_RESP firmado
//   4. Se deriva clave_sesion via crypto_kx (X25519 + SHA-512 KDF)
// ============================================================

/* _syn_crypto_kx_generar_par: Generate X25519 keypair for crypto_kx
 * (Manual 6 §5.3 paso 4). Uses crypto_scalarmult_base (Curve25519)
 * — equivalent to libsodium crypto_kx_keypair.
 * Writes 32-byte clave_publica to pk_out and 32-byte clave_secreta to sk_out.
 * Retorna: 0 OK, -1 error.
 */
int _syn_crypto_kx_generar_par(unsigned char* pk_out, unsigned char* sk_out) {
    if (!pk_out || !sk_out) return -1;
    // Generar clave secreta aleatoria (32 bytes)
    for (int i = 0; i < 32; i++) {
        sk_out[i] = (unsigned char)(rand() & 0xFF);
    }
    // Clamping RFC 7748: limpiar bits bajo/alto del escalar
    sk_out[0]  &= 248;  // clear bottom 3 bits
    sk_out[31] &=  1;   // clear top bit
    sk_out[31] |=  64;  // set second-highest bit
    // Derivar clave pública: pk = sk * base_point (crypto_kx)
    return crypto_scalarmult_base(pk_out, sk_out);
}

/* _syn_crypto_kx_secreto_compartido: Compute shared secret via X25519
 * (crypto_scalarmult) — Diffie-Hellman para crypto_kx.
 * Retorna: 0 OK, -1 error.
 */
int _syn_crypto_kx_secreto_compartido(unsigned char* shared_out,
                                       const unsigned char* clave_publica,
                                       const unsigned char* clave_secreta) {
    if (!shared_out || !clave_publica || !clave_secreta) return -1;
    return crypto_scalarmult(shared_out, clave_secreta, clave_publica);
}

/* _syn_crypto_kx_derivar_clave_sesion: Derive session key (clave_sesion)
 * from shared secret via SHA-512 KDF (Manual 6 §5.3 paso 4).
 * clave_sesion = first 32 bytes of SHA-512(shared_secret).
 * Retorna: 0 OK, -1 error.
 */
int _syn_crypto_kx_derivar_clave_sesion(unsigned char* clave_sesion_out,
                                         const unsigned char* shared,
                                         int shared_len) {
    if (!clave_sesion_out || !shared || shared_len < 32) return -1;
    unsigned char hash[64];
    crypto_hash(hash, shared, shared_len);
    memcpy(clave_sesion_out, hash, 32);
    return 0;
}

/* _syn_handshake_hello_enviar: Build HELLO message for zero-trust handshake.
 * Manual 6 §5.3: [nonce (32)] [clave_publica (32)] [firma (64)] = 128 bytes.
 * The nonce is signed with Ed25519 (firma) to prove ownership of clave_secreta.
 * Retorna: tamaño del HELLO (128) o -1 en error.
 */
int _syn_handshake_hello_enviar(unsigned char* hello_out, int hello_sz,
                                 const unsigned char* nonce,
                                 const unsigned char* clave_publica,
                                 const unsigned char* clave_secreta) {
    if (hello_sz < 128) return -1;
    memset(hello_out, 0, hello_sz);
    // [nonce (32 bytes)]
    memcpy(hello_out, nonce, 32);
    // [clave_publica (32 bytes)]
    memcpy(hello_out + 32, clave_publica, 32);
    // [firma (64 bytes)]: Ed25519 sign over nonce
    unsigned long long sig_len = 0;
    crypto_sign(hello_out + 64, &sig_len, nonce, 32, clave_secreta);
    // HELLO = 32 (nonce) + 32 (pk) + 64 (firma) = 128 bytes
    return 128;
}

/* _syn_handshake_hello_verificar: Verify a HELLO message.
 * Checks the Ed25519 firma over the nonce using clave_publica_del_cliente.
 * Retorna: 0 si válido, -1 si inválido.
 */
int _syn_handshake_hello_verificar(const unsigned char* hello, int hello_len,
                                    const unsigned char* clave_publica) {
    if (hello_len < 128 || !hello || !clave_publica) return -1;
    // nonce = hello[0..31], firma = hello[64..127]
    // crypto_sign_open verifica: sm = firma || nonce
    unsigned char sm[96];
    memcpy(sm, hello + 64, 64);     // firma (64 bytes)
    memcpy(sm + 64, hello, 32);     // nonce como mensaje (32 bytes)
    unsigned long long msg_len = 0;
    unsigned char verified_msg[32];
    if (crypto_sign_open(verified_msg, &msg_len, sm, 96, clave_publica) == 0) {
        if (msg_len == 32 && memcmp(verified_msg, hello, 32) == 0) {
            return 0;  // HELLO válido
        }
    }
    return -1;  // HELLO inválido
}
