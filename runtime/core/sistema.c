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
#include <ctype.h>

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
    // cumple Manual 5 §1: función pura, sin estado compartido; separador de
    // PLATAFORMA en la salida (Windows '\', POSIX '/') para que el resultado
    // sea comparable byte a byte con el cwd crudo del SO (H-EOF-3a: antes
    // emitía '/' y el comparador por prefijo nunca matcheaba en Windows).
    char sep = '/';
#ifdef _WIN32
    sep = '\\';
#endif
    char buf[4096];
    int len = ruta.longitud < 4095 ? ruta.longitud : 4095;
    memcpy(buf, ruta.datos, (size_t)len);
    buf[len] = '\0';
    // Resolucion de componentes con PILA (rew ME config_ruta_absoluta): el
    // bucle original retrocedia el componente equivocado cuando el caracter
    // previo era el separador recien emitido — "X/../Y" normalizaba a "XY"
    // (componente fusionado) y ".." podia sobrevivir literal; con la pila,
    // "." se descarta, ".." desapila, y ".." sobre raiz relativa se CONSERVA
    // ("../x") para que el comparador por prefijo lo rechace (sandbox sano).
    int comp_start[2048];
    int comp_len[2048];
    int ncomp = 0;
    int es_absoluta = (len > 0 && (buf[0] == '/' || buf[0] == '\\'));
    int i = 0;
    while (i < len) {
        while (i < len && (buf[i] == '/' || buf[i] == '\\')) i++;
        if (i >= len) break;
        int s = i;
        while (i < len && buf[i] != '/' && buf[i] != '\\') i++;
        int l = i - s;
        if (l == 1 && buf[s] == '.') continue; // "."
        if (l == 2 && buf[s] == '.' && buf[s+1] == '.') {
            if (ncomp > 0) {
                int ts = comp_start[ncomp-1];
                int tl = comp_len[ncomp-1];
                int top_puntos = (tl == 2 && buf[ts] == '.' && buf[ts+1] == '.');
                if (!top_puntos) { ncomp--; continue; }
                // top es "..": apilar ("../.." no colapsa sobre raiz relativa)
            } else if (es_absoluta) {
                continue; // ".." sobre raiz absoluta: fuera del sandbox
            }
            // ncomp==0 relativa: conservar ".." (el prefijo cwd no matcheara)
        }
        if (ncomp < 2048) { comp_start[ncomp] = s; comp_len[ncomp] = l; ncomp++; }
    }
    char normalized[4096];
    int nlen = 0;
    if (es_absoluta && nlen < 4095) normalized[nlen++] = sep;
    for (int k = 0; k < ncomp; k++) {
        if (k > 0 && nlen < 4095) normalized[nlen++] = sep;
        for (int j = 0; j < comp_len[k] && nlen < 4095; j++) {
            normalized[nlen++] = buf[comp_start[k] + j];
        }
    }
    if (nlen == 0) { normalized[nlen++] = '.'; }
    normalized[nlen] = '\0';
    // cumple Manual 2 §9.1: resultado en pool_alloc (RAII estatico del pool,
    // move semantics al retornar por valor)
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
    // cumple Manual 5 §1: función pura; comparación por prefijo con BORDE de
    // componente (H-EOF-3b: memcmp ciego aceptaba 'proyecto_synapse_evil' como
    // hijo de 'proyecto_synapse') e insensible a mayúsculas SOLO en Windows
    // (NTFS no distingue; POSIX sí). Punto de montaje distinto → fuera.
    if (dir.longitud <= 0) return 0;
    if (ruta.longitud < dir.longitud) return 0;
    // Punto de montaje (letra de unidad / raíz): primera componente distinta → 0.
    {
        char a = ruta.datos[0];
        char b = dir.datos[0];
#ifdef _WIN32
        a = (char)tolower((int)(unsigned char)a);
        b = (char)tolower((int)(unsigned char)b);
#endif
        if (a != b) return 0;
    }
    for (int i = 0; i < dir.longitud; i++) {
        char a = ruta.datos[i];
        char b = dir.datos[i];
#ifdef _WIN32
        a = (char)tolower((int)(unsigned char)a);
        b = (char)tolower((int)(unsigned char)b);
#endif
        if (a != b) return 0;
    }
    if (ruta.longitud == dir.longitud) return 1; // ruta == dir
    if (dir.datos[dir.longitud - 1] == '/' || dir.datos[dir.longitud - 1] == '\\') return 1;
    char nx = ruta.datos[dir.longitud];
    return nx == '/' || nx == '\\';
}

// cumple Manual 7 §7.3 (ME r198b3_fmt_lint, H-R198b2-2): modo del sandbox
// de lecturas. ESTRICTO (1) es el DEFAULT: todo binario de usuario conserva
// la contención del cwd de H-CFG-2 (r194) sin llamar al setter. El dispatcher
// CLI del compilador (cli_lint/cli_fmt/cli_check/cli_test en
// nucleo/principal.syn — Manual 8 §4.1) se auto-desactiva la contención con
// _syn_sandbox_set(0): es una herramienta de desarrollo que lee las rutas
// NOMBRADAS por el usuario en argv (M8 §4.1), y el código usuario NUNCA corre
// en su proceso (cli_test ejecuta el exe compilado como SUBPROCESO) — el
// escape no amplia la superficie de H-CFG-2.
static int _syn_sandbox_modo = 1;

void _syn_sandbox_set(int64_t modo) { _syn_sandbox_modo = modo != 0 ? 1 : 0; }

// cumple Manual 7 §7.3 (H-CFG-2, ME r194_deuda_gobernanza): validador del
// sandbox para las builtins de LECTURA (leer_archivo/existe_archivo llamadas
// SIN `importar std.sistema` — el emisor enraiza la llamada aquí antes de
// tocar el runtime de io.c/modelo.c). Composición de los primitivos vigentes
// (H-EOF-3a/b, una sola taxonomía: _syn_normalizar_ruta + _syn_ruta_en_directorio):
// resuelve la relativa contra el cwd normalizado (igual que std.sistema
// _validar_ruta_segura — Manual 7 §2.1), normaliza, y EXIGE contención del cwd
// (borde de componente) MIENTRAS el modo sea estricto (_syn_sandbox_modo==1,
// ME r198b3_fmt_lint: el dispatcher CLI del compilador se la desactiva —
// ver el setter arriba). Evasión del cwd → CadenaSegura vacía (""), que los
// consumidores tratan como lectura/exitencia fallida; los guards de
// _syn_leer_archivo (io.c: longitud<=0) y _syn_existe_archivo (modelo.c: fopen
// falla con "") la convierten en ''/falso SIN abrir NADA.
// Contratos (Manual 2 §12, en C la spec es el comentario+primitivos):
//   requiere: ruta.usuario válida (len>0) — el emisor solo llama con texto
//   garantiza: devuelve ruta NORMALIZADA dentro del cwd, ó {0, ""}
CadenaSegura _syn_ruta_validar(CadenaSegura ruta) {
    if (ruta.datos == NULL || ruta.longitud <= 0) return (CadenaSegura){0, ""};
    CadenaSegura cwd_raw = _syn_obtener_cwd();
    if (cwd_raw.datos == NULL || cwd_raw.longitud <= 0) return (CadenaSegura){0, ""};
    CadenaSegura cwd = _syn_normalizar_ruta(cwd_raw);
    if (cwd.datos == NULL || cwd.longitud <= 0) return (CadenaSegura){0, ""};
    // absoluta? (C:\, \\UNC, /posix) — misma regla que std/sistema.syn
    // (subcadena 1,2 == "\" ó 0,1 == "/" ó 0,2 == "\\\\").
    char c0 = ruta.datos[0];
    int es_absoluta = c0 == '/' || c0 == '\\' ||
                      (ruta.longitud >= 2 && c0 != '\0' && ruta.datos[1] == ':');
    CadenaSegura absoluta = ruta;
    if (!es_absoluta) {
        char sep = '/';
#ifdef _WIN32
        sep = '\\';
#endif
        int tl = cwd.longitud + 1 + ruta.longitud;
        char* buf = (char*)pool_alloc((size_t)(tl + 1));
        if (!buf) return (CadenaSegura){0, ""};
        memcpy(buf, cwd.datos, (size_t)cwd.longitud);
        buf[cwd.longitud] = sep;
        memcpy(buf + cwd.longitud + 1, ruta.datos, (size_t)ruta.longitud);
        buf[tl] = '\0';
        absoluta = (CadenaSegura){ .longitud = tl, .datos = buf };
    }
    CadenaSegura norm = _syn_normalizar_ruta(absoluta);
    if (norm.datos == NULL || norm.longitud <= 0) return (CadenaSegura){0, ""};
    // El modo CLI (_syn_sandbox_modo==0) normaliza pero EXIGE contención NO:
    // es el dispatcher del compilador leyendo las rutas argv del usuario
    // (ME r198b3_fmt_lint, Manual 8 §4.1).
    if (_syn_sandbox_modo && !_syn_ruta_en_directorio(norm, cwd))
        return (CadenaSegura){0, ""};
    return norm;
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
