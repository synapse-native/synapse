// runtime/core/sistema.c — std.sistema: helpers de ruta/string
// D-9(d) corte 11: extraído de synapse_rt.c (modularización, patrón toml.c R64)
// Texto byte-idéntico al original (CRLF preservado).
//
// Manual 6 §6.1 (path traversal protection); consumido por std/sistema.syn
// y nucleo/lexer_keywords.syn (str_eq). Regla 13 + canon D-9(d).

#include "synapse_rt_types.h"
#include "runtime/core/sistema.h"

#ifdef _WIN32
  #include <windows.h>
#endif

// ============================================================
// PATH TRAVERSAL PROTECTION — std.sistema helpers
// ============================================================

int str_eq(CadenaSegura a, CadenaSegura b) {
    if (a.longitud != b.longitud) return 0;
    return memcmp(a.datos, b.datos, (size_t)a.longitud) == 0;
}

// cumple Manual 2 9.1: concat usa pool_alloc (no malloc), RAII libera con pool_free
CadenaSegura concat(CadenaSegura a, CadenaSegura b) {
    int _tl = a.longitud + b.longitud;
    char* _buf = (char*)pool_alloc((size_t)(_tl + 1));
    if (!_buf) { fprintf(stderr, "Error: pool_alloc fallo en concat()\n"); exit(1); }
    memcpy(_buf, a.datos, (size_t)a.longitud);
    memcpy(_buf + a.longitud, b.datos, (size_t)b.longitud);
    _buf[_tl] = '\0';
    return (CadenaSegura){ .longitud = _tl, .datos = _buf };
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
