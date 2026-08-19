// synapse_rt.c — Synapse runtime (modular: types, memory, concurrency)
// Compilar: gcc -c synapse_rt.c -o synapse_rt.o
// Linkear con: synapse_rt_memory.o synapse_rt_concurrency.o

#include "synapse_rt_types.h"
#include "runtime/core/tensor.h"  // D-9(d): std.math/std.tensor/std.simd extraidos a tensor.c
#include "runtime/core/cluster.h"  // D-9(d): std.cluster (M8.1-M8.6) extraido a cluster.c
#include "runtime/core/debug.h"  // D-9(d): debug (M9.0-M9.4) extraido a debug.c
#include "runtime/core/network.h"  // D-9(d): std.net (networking) extraido a network.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <pthread.h>
#include <time.h>
#include "librerias/embedded_libs.h"
#include "axon/tweetnacl.h"

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <windows.h>
  #include <direct.h>
  #include <wincrypt.h>
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <unistd.h>
  #include <sys/mman.h>
  #include <sys/stat.h>
  #include <fcntl.h>
#endif
// -----------------------------------------------------------
// (Canal abrir/leer/cerrar + librerias virtuales movidos a runtime/core/io.c en F3-2;
//  externs _syn_abrir/_syn_leer/_syn_escribir/_syn_escribir_linea/_syn_leer_linea
//  definidos alli tambien — std/io.syn ya enlaza)
// (std.net movido a runtime/core/network.c en D-9(d) corte 6)
// (std.json movido a runtime/core/json.c en D-9(d) corte 7)

#include "runtime/core/json.h"  // D-9(d) corte 7: std.json extraido a json.c
#include "runtime/core/cripto.h"  // D-9(d) corte 8: std.cripto extraido a cripto.c
#include "runtime/core/toml.h"  // D-9(d) corte 9: std.toml extraido a toml.c
#include "runtime/core/tiempo.h"  // D-9(d) corte 10: std.tiempo extraido a tiempo.c
#include "runtime/core/http.h"  // D-9(d) corte 10: std.http extraido a http.c

// --- std.conv ---

int64_t texto_a_entero(CadenaSegura str) {
    if (str.datos == NULL || str.longitud == 0) return 0;
    return (int64_t)strtoll(str.datos, NULL, 10);
}

double texto_a_decimal(CadenaSegura str) {
    if (str.datos == NULL || str.longitud == 0) return 0.0;
    return strtod(str.datos, NULL);
}

CadenaSegura decimal_a_texto(double n) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%f", n);
    char* data = (char*)malloc(len + 1);
    if (!data) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en decimal_a_texto\n"); exit(1); }
    memcpy(data, buf, len + 1);
    return (CadenaSegura){ .longitud = len, .datos = data };
}

// A5.1 (D-7): entero -> int64_t (Manual 2 S4.1 L267-268). Ensayo de runtime:
// %lld con cast (long long) para portabilidad; salida identica para valores
// pequenos, sin truncar en rangos 32->64 bits. Los mapeos se migran en A5.2.
CadenaSegura entero_a_texto(int64_t n) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%lld", (long long)n);
    char* data = (char*)malloc(len + 1);
    if (!data) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en entero_a_texto\n"); exit(1); }
    memcpy(data, buf, len + 1);
    return (CadenaSegura){ .longitud = len, .datos = data };
}
// ============================================================
// std.toml — TOML Parser (Subset para Axon) extraido a
// runtime/core/toml.c (D-9(d) corte 9, patron json.c R42).
// ============================================================

// --- Cache types (matching _synapse_shared.h for linker) ---
typedef struct CacheEntry {
    CadenaSegura clave;
    CadenaSegura archivo_fuente;
    CadenaSegura archivo_objeto;
    CadenaSegura hash_fuente;
    CadenaSegura hashes_deps;
    CadenaSegura flags_compilacion;
    CadenaSegura version_compilador;
    int timestamp;
    int tamano_bytes;
} CacheEntry;

typedef struct CacheStats {
    int total_entradas;
    int hits;
    int misses;
    int tamano_total_bytes;
    int hits_ultima_ejecucion;
    int misses_ultima_ejecucion;
} CacheStats;

typedef struct CampoToml {
    int tipo;
    CadenaSegura valor_str;
    int valor_ent;
} CampoToml;


// ============================================================
// std.tiempo + std.http extraidos a runtime/core/tiempo.c y
// runtime/core/http.c (D-9(d) corte 10, patron toml.c R64).
// ============================================================

// --- std.ai (GGUF Reader / Memory Mapping) ---
// D-9(d) corte 3: bloque std.ai (GGUF/BPE/ModeloContexto/inferencia/oraculos)
// extraido a runtime/core/modelo.c (texto byte-identico, patron tensor.c R35).

// --- Cache-to-TOML helpers (externo stubs from cache.syn) ---
// (NO parte del corte std.ai: pertenece a nucleo/cache.syn, tipos en este archivo.)

struct NodoToml toml_desde_entrada(struct CacheEntry entry) {
    (void)entry;
    struct NodoToml doc = {0};
    doc.tipo = 1; doc.pares = NULL; doc.longitud = 0; doc.valor_str = (CadenaSegura){0, ""};
    return doc;
}

struct NodoToml toml_desde_stats(struct CacheStats entry) {
    (void)entry;
    struct NodoToml doc = {0};
    doc.tipo = 1; doc.pares = NULL; doc.longitud = 0; doc.valor_str = (CadenaSegura){0, ""};
    return doc;
}

CadenaSegura a_texto(struct NodoToml doc) {
    // Convert NodoToml to TOML text string
    // Minimal stub: returns empty string
    (void)doc;
    return (CadenaSegura){0, ""};
}

struct NodoToml actualizar_indice(struct NodoToml doc, struct CacheEntry entry) {
    // Update TOML index document with a new entry
    // Minimal stub: returns doc unchanged
    (void)entry;
    return doc;
}

// ============================================================================
// ============================================================
// Axon — HTTP download + TAR extraction + SHA-256 Lock
// ============================================================

// --- SHA-256 raw (binary digest to hex string) ---
// Returns hex string (heap-allocated), caller must free.
CadenaSegura _syn_sha256_hex(CadenaSegura datos) {
    SHA256_CTX ctx;
    uint8_t digest[SHA256_DIGEST_SIZE];
    sha256_init(&ctx);
    sha256_update(&ctx, (const uint8_t*)datos.datos, (size_t)datos.longitud);
    sha256_final(&ctx, digest);
    char hex[65];
    for (int i = 0; i < SHA256_DIGEST_SIZE; i++) {
        snprintf(hex + i * 2, 3, "%02x", digest[i]);
    }
    hex[64] = 0;
    char* data = (char*)malloc(65);
    if (!data) return (CadenaSegura){0, ""};
    memcpy(data, hex, 65);
    return (CadenaSegura){ .longitud = 64, .datos = data };
}

// --- Reusable: SHA-256 hash of a file on disk ---
// Returns hex string (heap-allocated), or empty string on failure.
CadenaSegura _syn_sha256_archivo(const char* ruta) {
    FILE* f = fopen(ruta, "rb");
    if (!f) return (CadenaSegura){0, ""};
    SHA256_CTX ctx;
    sha256_init(&ctx);
    uint8_t buf[8192];
    size_t n;
    while ((n = fread(buf, 1, sizeof(buf), f)) > 0) {
        sha256_update(&ctx, buf, n);
    }
    fclose(f);
    uint8_t digest[SHA256_DIGEST_SIZE];
    sha256_final(&ctx, digest);
    char hex[65];
    for (int i = 0; i < SHA256_DIGEST_SIZE; i++) {
        snprintf(hex + i * 2, 3, "%02x", digest[i]);
    }
    hex[64] = 0;
    char* data = (char*)malloc(65);
    if (!data) return (CadenaSegura){0, ""};
    memcpy(data, hex, 65);
    return (CadenaSegura){ .longitud = 64, .datos = data };
}

// --- HTTP GET: download URL content into a file on disk ---
// Returns 0 on success, -1 on failure.
// Writes response body to the specified output path.
int _syn_http_get_archivo(CadenaSegura host, int puerto, CadenaSegura ruta, const char* salida_ruta) {
    int fd = _syn_socket();
    if (fd < 0) return -1;
    if (_syn_conectar(fd, host.datos, puerto) < 0) {
        _syn_cerrar_socket(fd);
        return -1;
    }
    char req[4096];
    snprintf(req, sizeof(req),
        "GET %s HTTP/1.0\r\n"
        "Host: %s\r\n"
        "User-Agent: Synapse-Axon/2.0\r\n"
        "Connection: close\r\n"
        "\r\n",
        ruta.datos, host.datos);
    _syn_enviar(fd, req, (int)strlen(req));

    // Read response: skip headers, write body to file
    char buf[4096];
    int total = 0;
    int header_done = 0;
    FILE* out = fopen(salida_ruta, "wb");
    if (!out) { _syn_cerrar_socket(fd); return -1; }

    while (1) {
        int n = _syn_recibir(fd, buf, sizeof(buf) - 1);
        if (n <= 0) break;
        buf[n] = 0;
        total += n;

        if (!header_done) {
            char* body = strstr(buf, "\r\n\r\n");
            if (body) {
                header_done = 1;
                body += 4;
                int body_len = n - (int)(body - buf);
                if (body_len > 0) fwrite(body, 1, (size_t)body_len, out);
            }
        } else {
            fwrite(buf, 1, (size_t)n, out);
        }
    }
    fclose(out);
    _syn_cerrar_socket(fd);
    return header_done ? 0 : -1;
}

// --- POSIX TAR extraction (header-only, no compression) ---
// Extracts files from a .tar archive into the output directory.
// Returns 0 on success, -1 on failure.
// TAR format: 512-byte blocks, headers in ASCII octal.
int _syn_tar_extraer(const char* tar_ruta, const char* salida_dir) {
    FILE* f = fopen(tar_ruta, "rb");
    if (!f) return -1;

    // Create output directory
    char mkdir_cmd[1024];
#ifdef _WIN32
    snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir \"%s\" 2>nul", salida_dir);
#else
    snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir -p \"%s\" 2>/dev/null", salida_dir);
#endif
    system(mkdir_cmd);

    uint8_t block[512];
    int result = 0;

    while (1) {
        size_t n = fread(block, 1, 512, f);
        if (n < 512) break;  // EOF or partial block

        // Check for end-of-archive (two zero blocks)
        if (block[0] == 0) {
            // Skip second zero block
            fread(block, 1, 512, f);
            break;
        }

        // Parse header fields from octal ASCII
        char name[256];
        char size_str[13];
        char typeflag;
        char prefix[156];

        memcpy(name, block, 100); name[100] = 0;
        memcpy(size_str, block + 124, 12); size_str[12] = 0;
        typeflag = block[156];
        memcpy(prefix, block + 345, 155); prefix[155] = 0;

        // --- Path traversal protection (Manual 6 §6.1) ---
        // Reject absolute paths and directory escapes ("../" or "/.." components)
        int _pt_traversal = 0;
        if (name[0] == '/' || prefix[0] == '/') { _pt_traversal = 1; }
        // Check for ".." as a PATH COMPONENT (not substring - avoids foo..bar false positives)
        if (!_pt_traversal) {
            const char* _checks[] = {name, prefix, NULL};
            for (int _ci = 0; _checks[_ci] && !_pt_traversal; _ci++) {
                const char* _p = _checks[_ci];
                int _len = (int)strlen(_p);
                // Check start: "../"
                if (_len >= 3 && _p[0] == '.' && _p[1] == '.' && _p[2] == '/') { _pt_traversal = 1; }
                // Check middle: "/../"
                if (!_pt_traversal) {
                    for (int _si = 1; _si < _len - 3; _si++) {
                        if (_p[_si] == '/' && _p[_si+1] == '.' && _p[_si+2] == '.' && _p[_si+3] == '/') {
                            _pt_traversal = 1; break;
                        }
                    }
                }
                // Check end: "/.."
                if (!_pt_traversal && _len >= 3 && _p[_len-3] == '/' && _p[_len-2] == '.' && _p[_len-1] == '.') {
                    _pt_traversal = 1;
                }
                // Check exact: ".."
                if (!_pt_traversal && _len == 2 && _p[0] == '.' && _p[1] == '.') { _pt_traversal = 1; }
            }
        }
        if (_pt_traversal) {
            fprintf(stderr, "[Axon] ERR_AXON_COMPROMISED: path traversal detectado en TAR: %s/%s\n", prefix, name);
            fclose(f);
            return -1;
        }

        // Build full path (prefix + "/" + name)
        char full_path[512];
        if (prefix[0]) {
            snprintf(full_path, sizeof(full_path), "%s/%s", salida_dir, prefix);
            // Ensure subdirectory exists
#ifdef _WIN32
            snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir \"%s\" 2>nul", full_path);
#else
            snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir -p \"%s\" 2>/dev/null", full_path);
#endif
            system(mkdir_cmd);
            snprintf(full_path, sizeof(full_path), "%s/%s/%s", salida_dir, prefix, name);
        } else {
            snprintf(full_path, sizeof(full_path), "%s/%s", salida_dir, name);
        }

        // Parse file size (octal string to long)
        unsigned long file_size = 0;
        for (int i = 0; size_str[i] && i < 12; i++) {
            if (size_str[i] >= '0' && size_str[i] <= '7') {
                file_size = file_size * 8 + (unsigned long)(size_str[i] - '0');
            } else break;
        }

        // Calculate data blocks (rounded up to 512)
        unsigned long data_blocks = (file_size + 511) / 512;

        if (typeflag == '0' || typeflag == '\0') {  // Regular file
            FILE* out = fopen(full_path, "wb");
            if (out) {
                unsigned long remaining = file_size;
                for (unsigned long bi = 0; bi < data_blocks; bi++) {
                    uint8_t data_block[512];
                    size_t dn = fread(data_block, 1, 512, f);
                    if (dn < 512) break;
                    size_t to_write = remaining > 512 ? 512 : remaining;
                    fwrite(data_block, 1, to_write, out);
                    remaining -= to_write;
                }
                fclose(out);
            } else {
                // Skip data blocks if can't open output
                fseek(f, (long)(data_blocks * 512), SEEK_CUR);
            }
        } else if (typeflag == '5') {  // Directory
#ifdef _WIN32
            snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir \"%s\" 2>nul", full_path);
#else
            snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir -p \"%s\" 2>/dev/null", full_path);
#endif
            system(mkdir_cmd);
        } else {
            // Unknown type, skip data blocks
            fseek(f, (long)(data_blocks * 512), SEEK_CUR);
        }
    }

    fclose(f);
    return result;
}

// --- Axon Lock: verify downloaded package against axon.lock ---
// axon.lock format (TOML):
//   [lock]
//   "paquete" = { version = "1.0.0", hash = "sha256:9f86d..." }
//
// Returns 0 on match, -1 on mismatch (caller should abort with ERR_AXON_COMPROMISED).
int _syn_axon_verificar_lock(const char* paquete, const char* version, const char* archivo_ruta, const char* lock_ruta) {
    // 1. Read existing axon.lock
    FILE* f = fopen(lock_ruta, "rb");
    if (!f) {
        // No lock file exists: create one
        CadenaSegura hash = _syn_sha256_archivo(archivo_ruta);
        if (hash.longitud == 0) return -1;
        f = fopen(lock_ruta, "wb");
        if (!f) { free((void*)hash.datos); return -1; }
        fprintf(f, "[lock]\n\"%s\" = { version = \"%s\", hash = \"sha256:%s\" }\n", paquete, version, hash.datos);
        fclose(f);
        fprintf(stderr, "[Axon] Lock creado: %s\n", lock_ruta);
        free((void*)hash.datos);
        return 0;
    }

    // 2. Lock exists: read and parse it
    fseek(f, 0, SEEK_END);
    long fsz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* content = (char*)malloc((size_t)fsz + 1);
    if (!content) { fclose(f); return -1; }
    fread(content, 1, (size_t)fsz, f);
    fclose(f);
    content[fsz] = 0;

    // Simple TOML parsing: find sha256:... hash for this package
    char search_key[256];
    snprintf(search_key, sizeof(search_key), "\"%s\"", paquete);
    char* pkg_start = strstr(content, search_key);
    if (!pkg_start) {
        // Package not in lock: append it
        free(content);
        CadenaSegura hash = _syn_sha256_archivo(archivo_ruta);
        if (hash.longitud == 0) return -1;
        f = fopen(lock_ruta, "ab");
        if (!f) { free((void*)hash.datos); return -1; }
        fprintf(f, "\"%s\" = { version = \"%s\", hash = \"sha256:%s\" }\n", paquete, version, hash.datos);
        fclose(f);
        free((void*)hash.datos);
        return 0;
    }

    // Find hash field
    char* hash_field = strstr(pkg_start, "sha256:");
    if (!hash_field) { free(content); return -1; }
    hash_field += 7;  // skip "sha256:"
    char expected_hash[65];
    int hi = 0;
    while (hi < 64 && hash_field[hi] && hash_field[hi] != '"' && hash_field[hi] != '}' && hash_field[hi] != ' ' && hash_field[hi] != '\n') {
        expected_hash[hi] = hash_field[hi];
        hi++;
    }
    expected_hash[hi] = 0;
    free(content);

    // 3. Compute actual hash of downloaded file
    CadenaSegura actual_hash = _syn_sha256_archivo(archivo_ruta);
    if (actual_hash.longitud == 0) return -1;

    // 4. Compare (save hash string BEFORE free)
    int match = (strcmp(expected_hash, actual_hash.datos) == 0);

    if (!match) {
        char _actual_hex[65];
        strncpy(_actual_hex, actual_hash.datos, 64);
        _actual_hex[64] = 0;
        free((void*)actual_hash.datos);
        fprintf(stderr, "[Axon] ERR_AXON_COMPROMISED: hash mismatch for '%s'\n", paquete);
        fprintf(stderr, "  Esperado: sha256:%s\n", expected_hash);
        fprintf(stderr, "  Obtenido: sha256:%s\n", _actual_hex);
        remove(archivo_ruta);
        return -1;
    }

    free((void*)actual_hash.datos);
    fprintf(stderr, "[Axon] Hash verificado: sha256:%s\n", expected_hash);
    return 0;
}

// --- Axon: Ed25519 signature verification ---
int _syn_axon_verificar_firma(const char* tar_ruta, const char* sig_ruta, const char* clave_publica_hex) {
    // 1. Read tar file (mensaje)
    FILE* f = fopen(tar_ruta, "rb");
    if (!f) return -1;
    fseek(f, 0, SEEK_END);
    long tar_sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (tar_sz < 0) { fclose(f); return -1; }
    size_t alloc_sz = (size_t)(tar_sz > 0 ? tar_sz : 1);
    unsigned char* buf = (unsigned char*)malloc(alloc_sz);
    if (!buf) { fclose(f); return -1; }
    if (tar_sz > 0) fread(buf, 1, (size_t)tar_sz, f);
    fclose(f);
    CadenaSegura mensaje = { .longitud = (int)tar_sz, .datos = (char*)buf };

    // 2. Read sig file (expect 64 bytes binary Ed25519 signature)
    f = fopen(sig_ruta, "rb");
    if (!f) { free(buf); return -1; }
    fseek(f, 0, SEEK_END);
    long sig_sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sig_sz < 64) { fclose(f); free(buf); return -1; }
    unsigned char sig[64];
    size_t sig_rd = fread(sig, 1, 64, f);
    fclose(f);
    if (sig_rd < 64) { free(buf); return -1; }
    CadenaSegura firma = { .longitud = 64, .datos = (char*)sig };

    // 3. Convert hex public key (64 hex chars) to 32 bytes
    int pk_hex_len = (int)strlen(clave_publica_hex);
    if (pk_hex_len < 64) { free(buf); return -1; }
    unsigned char pk[32];
    for (int i = 0; i < 32; i++) {
        unsigned int byte_val;
        char hex_pair[3] = { clave_publica_hex[i*2], clave_publica_hex[i*2+1], 0 };
        if (sscanf(hex_pair, "%x", &byte_val) != 1) { free(buf); return -1; }
        pk[i] = (unsigned char)byte_val;
    }
    CadenaSegura clave_publica = { .longitud = 32, .datos = (char*)pk };

    // 4. Verify Ed25519 signature (calls _syn_ed25519_verificar defined above)
    int rc = _syn_ed25519_verificar(mensaje, firma, clave_publica);

    free(buf);  // sig and pk are stack-allocated
    return rc;  // 0 = signature valid, -1 = invalid
}

// Axon TOML cleanup wrapper (takes pointer, calls _toml_nodo_liberar by value)
void _syn_axon_limpiar_toml(void* n) {
    if (!n) return;
    _toml_nodo_liberar(*(NodoToml*)n);
}

// --- Axon: busqueda local (offline-first resolution) ---
// Returns:
//  0 = package already installed (extract_dir/principal.syn exists)
//  1 = package tar available in .axon_cache/
//  2 = package tar available in paquetes_oficiales/<ver>/
//  3+ = package found via AXON_PATH environment variable
// -1 = not found locally
int _syn_axon_buscar_local(const char* paquete, const char* version,
                           char* tar_path, int tar_sz,
                           char* extract_dir, int ext_sz) {
    // 0. Pre-set extract_dir regardless (needed by caller)
    snprintf(extract_dir, ext_sz, "axon_modules/%s", paquete);

    // 1. Check installed: axon_modules/<pkg>/principal.syn
    char chk[1024];
    snprintf(chk, sizeof(chk), "%s/principal.syn", extract_dir);
    FILE* f = fopen(chk, "rb");
    if (f) { fclose(f); fprintf(stderr, "[Axon] Local: ya instalado en %s\n", extract_dir); return 0; }

    // 2. Check .axon_cache/<pkg>.tar
    snprintf(tar_path, tar_sz, ".axon_cache/%s.tar", paquete);
    f = fopen(tar_path, "rb");
    if (f) { fclose(f); fprintf(stderr, "[Axon] Local: cache encontrado %s\n", tar_path); return 1; }

    // 3. Check paquetes_oficiales/<pkg>/<ver>.tar
    snprintf(tar_path, tar_sz, "paquetes_oficiales/%s/%s.tar", paquete, version);
    f = fopen(tar_path, "rb");
    if (f) { fclose(f); fprintf(stderr, "[Axon] Local: oficial %s\n", tar_path); return 2; }

    // 4. Check AXON_PATH env var directories (semicolon-separated)
    const char* axon_path = getenv("AXON_PATH");
    if (axon_path && axon_path[0]) {
        char path_copy[4096];
        strncpy(path_copy, axon_path, sizeof(path_copy)-1);
        path_copy[sizeof(path_copy)-1] = '\0';
        char* save;
        char* tok = strtok_r(path_copy, ";", &save);
        int origin = 3;
        while (tok) {
            snprintf(tar_path, tar_sz, "%s/%s/%s.tar", tok, paquete, version);
            f = fopen(tar_path, "rb");
            if (f) { fclose(f); fprintf(stderr, "[Axon] Local: AXON_PATH %s\n", tar_path); return origin; }
            tok = strtok_r(NULL, ";", &save);
            origin++;
        }
    }

    return -1; // not found
}

// --- Axon: escribir lock (append mode, crea entrada en axon.lock) ---
int _syn_axon_escribir_lock(const char* paquete, const char* version, const char* hash_sha256) {
    if (!hash_sha256 || !*hash_sha256) { fprintf(stderr,"[Axon] WARNING: hash vacio para lock\n"); return -1; }
    FILE* f = fopen("axon.lock", "ab");
    if (!f) { fprintf(stderr,"[Axon] WARNING: no se pudo abrir axon.lock\n"); return -1; }
    fseek(f, 0, SEEK_END);
    if (ftell(f) == 0) { fprintf(f, "[lock]\n"); }
    fprintf(f, "\"%s\" = { version = \"%s\", hash = \"sha256:%s\" }\n", paquete, version, hash_sha256);
    fclose(f);
    fprintf(stderr, "[Axon] Lock actualizado: %s v%s\n", paquete, version);
    return 0;
}

// ============================================================
// M9.0 — Debug/Trace System (time-travel debug, traza persistente)
// extraido a runtime/core/debug.c (D-9(d) corte 5, patron cluster.c R40).
// ============================================================

// ============================================================
// M8.1-M8.4 — std.cluster (transporte UDP/Ed25519, work-stealing,
// raft, checkpoint/live-migration) extraido a runtime/core/cluster.c
// (D-9(d) corte 4, patron modelo.c R39; texto byte-identico).
// El bloque M9.1-M9.3 (debug time-travel) permanece aqui (corte 5).
// ============================================================

// ============================================================
// M9.1-M9.3 — Deterministic Recording / Reversible Breakpoints /
// Memory Snapshots extraido a runtime/core/debug.c (corte 5).
// ============================================================

// ============================================================
// M8.5-M8.6 — std.cluster (auto-discovery & membership, UDP multicast)
// extraido a runtime/core/cluster.c (D-9(d) corte 4, patron modelo.c R39).
// ============================================================

// ============================================================
// M9.4 — Distributed Multi-Node Debugging extraido a
// runtime/core/debug.c (D-9(d) corte 5).
// ============================================================

// ============================================================
// FZ — Fuzzing Distribuido Multi-Nodo (M10.4) extraido a
// runtime/core/fuzz.c (D-9(d) corte 6, patron cluster.c R40).
// ============================================================

// ============================================================
// PATH TRAVERSAL PROTECTION — std.sistema helpers
// ============================================================

int str_eq(CadenaSegura a, CadenaSegura b) {
    if (a.longitud != b.longitud) return 0;
    return memcmp(a.datos, b.datos, (size_t)a.longitud) == 0;
}

CadenaSegura _syn_normalizar_ruta(CadenaSegura ruta) {
    char buf[4096];
    int len = ruta.longitud < 4095 ? ruta.longitud : 4095;
    memcpy(buf, ruta.datos, (size_t)len);
    buf[len] = '\0';
    // Resolve . and ..
    char normalized[4096];
    int nlen = 0;
    int i = 0;
    while (i < len) {
        if (buf[i] == '/' || buf[i] == '\\') {
            // Skip double separators
            while (i < len && (buf[i] == '/' || buf[i] == '\\')) i++;
            continue;
        }
        // Check for ..
        if (buf[i] == '.' && i + 1 < len && buf[i+1] == '.') {
            if (i + 2 >= len || buf[i+2] == '/' || buf[i+2] == '\\') {
                // Go back one component
                while (nlen > 0 && normalized[nlen-1] != '/' && normalized[nlen-1] != '\\') nlen--;
                if (nlen > 0) nlen--; // remove separator
                i += 2;
                if (i < len && (buf[i] == '/' || buf[i] == '\\')) i++;
                continue;
            }
        }
        // Copy component
        while (i < len && buf[i] != '/' && buf[i] != '\\') {
            if (nlen < 4095) normalized[nlen++] = buf[i];
            i++;
        }
        if (i < len && nlen < 4095) normalized[nlen++] = '/';
    }
    if (nlen > 0 && normalized[nlen-1] == '/') nlen--;
    if (nlen == 0) { normalized[nlen++] = '.'; }
    normalized[nlen] = '\0';
    char* result = (char*)pool_alloc((size_t)(nlen + 1));
    if (!result) return ruta;
    memcpy(result, normalized, (size_t)(nlen + 1));
    return (CadenaSegura){ .longitud = nlen, .datos = result };
}

CadenaSegura _syn_obtener_cwd(void) {
    char buf[4096];
#ifdef _WIN32
    DWORD len = GetCurrentDirectoryA(4096, buf);
#else
    char* _cwd = getcwd(buf, 4096);
    int len = _cwd ? (int)strlen(buf) : 0;
#endif
    if (len == 0 || len >= 4096) {
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = (int)len, .datos = result };
}

int _syn_ruta_en_directorio(CadenaSegura ruta, CadenaSegura dir) {
    if (ruta.longitud < dir.longitud) return 0;
    return memcmp(ruta.datos, dir.datos, (size_t)dir.longitud) == 0;
}


