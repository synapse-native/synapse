// runtime/core/sistema.c — std.sistema: helpers de ruta/string
// D-9(d) corte 11: extraído de synapse_rt.c (modularización, patrón toml.c R64)
// Texto byte-idéntico al original (CRLF preservado).
//
// Path traversal protection (regla 13 + canon D-9(d)); consumido por
// std/sistema.syn y nucleo/lexer_keywords.syn (str_eq).

#include "synapse_rt_types.h"
#include "runtime/core/sistema.h"

#ifdef _WIN32
  #include <windows.h>
  #include <io.h>
#else
  #include <dirent.h>
  #include <unistd.h>
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ============================================================
// PATH TRAVERSAL PROTECTION — std.sistema helpers
// ============================================================

int64_t str_eq(CadenaSegura a, CadenaSegura b) {
    if (a.longitud != b.longitud) return 0;
    return memcmp(a.datos, b.datos, (size_t)a.longitud) == 0;
}

// cumple Manual 2 §9.1: concat usa pool_alloc (no malloc), RAII libera con pool_free
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

// ============================================================
// HERRAMIENTAS DEL AGENTE OPENSYN (Manual 7 §8 / §2.3)
// cumple Manual 5 §1: estado mutable compartido prohibido — estas
// funciones son puras/thread-safe (sin estado global mutable).
// Lee el repositorio local sin telemetria: listar directorios y
// capturar salida de comandos de solo lectura (git). pool_alloc.
// ============================================================

// cumple Manual 9 §5.7: listar_directorio devuelve entradas "nombre/\n" (carpetas
// con "/") o "nombre\n" (archivos), separadas por '\n'. Vacía si la ruta no
// existe o no es legible. Máx. 200 entradas / 16 KB (prompt del agente acotado).
CadenaSegura _syn_listar_directorio(CadenaSegura ruta) {
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    if (ruta.longitud <= 0 || ruta.longitud >= 4096) return vacio;
    char dirbuf[4096];
    memcpy(dirbuf, ruta.datos, (size_t)ruta.longitud);
    dirbuf[ruta.longitud] = '\0';

    char* acc = (char*)malloc(16384);
    if (!acc) return vacio;
    int used = 0;
    int n = 0;
#ifdef _WIN32
    char patron[4100];
    snprintf(patron, sizeof(patron), "%s\\*", dirbuf);
    struct _finddata_t fd;
    intptr_t h = _findfirst(patron, &fd);
    if (h == -1) { free(acc); return vacio; }
    do {
        if (strcmp(fd.name, ".") == 0 || strcmp(fd.name, "..") == 0) continue;
        if (n >= 200) break;
        int es_dir = (fd.attrib & _A_SUBDIR) != 0;
        int largo = (int)strlen(fd.name);
        if (used + largo + 2 >= 16384) break;
        memcpy(acc + used, fd.name, (size_t)largo);
        used += largo;
        if (es_dir) acc[used++] = '/';
        acc[used++] = '\n';
        n++;
    } while (_findnext(h, &fd) == 0);
    _findclose(h);
#else
    DIR* d = opendir(dirbuf);
    if (!d) { free(acc); return vacio; }
    struct dirent* e;
    while ((e = readdir(d)) != NULL) {
        if (strcmp(e->d_name, ".") == 0 || strcmp(e->d_name, "..") == 0) continue;
        if (n >= 200) break;
        int largo = (int)strlen(e->d_name);
        if (used + largo + 2 >= 16384) break;
        memcpy(acc + used, e->d_name, (size_t)largo);
        used += largo;
        if (e->d_type == DT_DIR) acc[used++] = '/';
        acc[used++] = '\n';
        n++;
    }
    closedir(d);
#endif
    if (used == 0) { free(acc); return vacio; }
    char* pool = (char*)pool_alloc((size_t)used + 1);
    if (!pool) { free(acc); return vacio; }
    memcpy(pool, acc, (size_t)used);
    pool[used] = '\0';
    free(acc);
    return (CadenaSegura){ .longitud = used, .datos = pool };
}

// cumple Manual 9 §5.7: capturar_comando ejecuta un comando de SOLO LECTURA
// (p.ej. git status/log) y devuelve su salida (máx 32 KB). El agente nunca
// recibe ejecución arbitraria: el cliente fija el comando exacto.
CadenaSegura _syn_capturar_comando(CadenaSegura cmd) {
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    if (cmd.longitud <= 0 || cmd.longitud >= 4096) return vacio;
    char cmdbuf[4096];
    memcpy(cmdbuf, cmd.datos, (size_t)cmd.longitud);
    cmdbuf[cmd.longitud] = '\0';
    // cumple Manual 9 §5.7: capturar tambien stderr (git imprime "not a git repo"
    // por stderr y no debe ensuciar el prompt del chat).
    char cmdfull[4200];
    snprintf(cmdfull, sizeof(cmdfull), "%s 2>&1", cmdbuf);
    FILE* p = popen(cmdfull, "r");
    if (!p) return vacio;
    char* acc = (char*)malloc(32768);
    if (!acc) { pclose(p); return vacio; }
    int used = 0;
    while (used < 32760) {
        int leidos = (int)fread(acc + used, 1, (size_t)(32768 - used - 1), p);
        if (leidos <= 0) break;
        used += leidos;
    }
    pclose(p);
    if (used == 0) { free(acc); return vacio; }
    acc[used] = '\0';
    char* pool = (char*)pool_alloc((size_t)used + 1);
    if (!pool) { free(acc); return vacio; }
    memcpy(pool, acc, (size_t)used + 1);
    free(acc);
    return (CadenaSegura){ .longitud = used, .datos = pool };
}
