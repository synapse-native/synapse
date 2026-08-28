// runtime/core/axon.c — Axon: HTTP download + TAR extraction + SHA-256 Lock
// D-9(d) corte 11: extraído de synapse_rt.c (modularización, patrón toml.c R64)
// Texto byte-idéntico al original (CRLF preservado). Única edición (regla 11):
// se eliminó la variable `total` (set-but-not-used) en _syn_http_get_archivo.
//
// Manual 6 §6.1 (path traversal protection en extracción TAR); regla 13
// + canon D-9(d). Consumido por nucleo/principal.syn (asm blocks) y tests/*.c.

#include "synapse_rt_types.h"
#include "runtime/core/network.h"  // _syn_socket/_syn_conectar/_syn_enviar/_syn_recibir/_syn_cerrar_socket (network.c)
#include "runtime/core/cripto.h"   // _syn_ed25519_verificar (cripto.c)
#include "runtime/core/toml.h"     // NodoToml/_toml_nodo_liberar (toml.c)
#include "axon/tweetnacl.h"        // SHA256_CTX/sha256_init/update/final
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

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
    int header_done = 0;
    FILE* out = fopen(salida_ruta, "wb");
    if (!out) { _syn_cerrar_socket(fd); return -1; }

    while (1) {
        int n = _syn_recibir(fd, buf, sizeof(buf) - 1);
        if (n <= 0) break;
        buf[n] = 0;

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

        // --- cumple Manual 6 §6.1: typeflags peligrosos rechazados ---
        // L (GNU long name) / K (GNU long link): el siguiente bloque contiene
        // el nombre real -> bypass del chequeo de path traversal actual.
        // 1 (hard link) / 2 (symlink): pueden apuntar fuera de salida_dir.
        // 75% de la superficie de ataque de path traversal en TAR usa estos typeflags.
        if (typeflag == 'L' || typeflag == 'K' || typeflag == '1' || typeflag == '2') {
            fprintf(stderr, "[Axon] ERR_AXON_COMPROMISED: typeflag '%c' rechazado en TAR (path traversal)\n", typeflag);
            fclose(f);
            return -1;
        }

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