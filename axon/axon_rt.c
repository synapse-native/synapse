// axon_rt.c — Axon package manager runtime
//
// Fase 6.1: TOML, TAR, SHA-256, Ed25519, SemVer, lock.
// Manual 8 §4.3-4.4 (gestor de paquetes Axon); Manual 6 §6.1 (path
// traversal protection en extracción TAR).
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
// SemVer helpers (static — local to this TU)
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

        // Optional: [dependencias] section — no validation required
        // Optional: [parametros] section — no validation required
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
 *   2. Si no está, HTTP download (host, puerto, ruta → .tar)
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
        fprintf(stderr, "[Axon] Download: %s → %s\n", ruta_http, tar_path);
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
        fprintf(stderr, "[Axon] ERR_TAR: fallo extracción de %s\n", tar_path);
        return -1;
    }
    fprintf(stderr, "[Axon] Paquete instalado: %s v%s → %s\n", paquete, version, extract_dir);
    return 0;
}
