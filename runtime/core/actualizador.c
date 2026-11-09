// cumple Manual 9 §3.1: soporte nativo de `synapse update`
// cumple Manual 9 §3.2: verificación Ed25519, backup e instalación silenciosa
// runtime/core/actualizador.c - helpers de plataforma para el actualizador.
#include "runtime/core/actualizador.h"
#include "runtime/core/cripto.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <sys/stat.h>
#include <sys/types.h>

#ifdef _WIN32
  #include <windows.h>
  #include <direct.h>
  #include <process.h>
  #define MKDIR(p) _mkdir(p)
  #define RUTA_SEP '\\'
#else
  #include <unistd.h>
  #include <limits.h>
  #define MKDIR(p) mkdir((p), 0755)
  #define RUTA_SEP '/'
#endif

// Clave pública canónica de release_keys/public.pem (raw Ed25519, 32 bytes).
static const char* _SYNAPSE_UPDATE_PUBHEX =
    "5019700c9c650939c4cf522e188f28fa4a38873b5a521a54dc9dbda8cab18d2f";

static CadenaSegura _texto_desde_c(const char* s) {
    CadenaSegura r;
    if (s == NULL) {
        r.longitud = 0;
        r.datos = "";
        return r;
    }
    size_t n = strlen(s);
    char* p = (char*)pool_alloc(n + 1);
    if (p == NULL) {
        r.longitud = 0;
        r.datos = "";
        return r;
    }
    memcpy(p, s, n + 1);
    r.longitud = (int)n;
    r.datos = p;
    return r;
}

CadenaSegura _syn_actualizador_asset(void) {
#if defined(_WIN32)
    return _texto_desde_c("synapse-win_x64.exe");
#elif defined(__APPLE__)
    return _texto_desde_c("synapse-darwin_arm64");
#elif defined(__aarch64__)
    return _texto_desde_c("synapse-linux_arm64");
#else
    return _texto_desde_c("synapse-linux_x64");
#endif
}

// cumple Manual 9 §3.2: la clave canónica se puede rotar/espejar con
// SYNAPSE_PUBLIC_KEY (hex de 64), misma convención que install.sh.
CadenaSegura _syn_actualizador_pubkey(void) {
    const char* env = getenv("SYNAPSE_PUBLIC_KEY");
    if (env != NULL) {
        size_t n = strlen(env);
        int ok = (n == 64);
        for (size_t i = 0; ok && i < n; i++) {
            if (!isxdigit((unsigned char)env[i])) ok = 0;
        }
        if (ok) return _texto_desde_c(env);
    }
    return _texto_desde_c(_SYNAPSE_UPDATE_PUBHEX);
}

CadenaSegura _syn_actualizador_exe(void) {
#ifdef _WIN32
    char buf[MAX_PATH];
    DWORD n = GetModuleFileNameA(NULL, buf, (DWORD)sizeof(buf));
    if (n == 0 || n >= sizeof(buf)) return _texto_desde_c("");
    buf[n] = '\0';
    return _texto_desde_c(buf);
#else
    char buf[PATH_MAX];
    ssize_t n = readlink("/proc/self/exe", buf, sizeof(buf) - 1);
    if (n < 0) {
        n = readlink("/proc/curproc/file", buf, sizeof(buf) - 1);
    }
    if (n < 0) return _texto_desde_c("");
    buf[n] = '\0';
    return _texto_desde_c(buf);
#endif
}

// cumple Manual 9 §3.2: descarga robusta en Windows aunque la ruta de curl o
// del destino contenga espacios (cmd /S /C conserva las comillas internas).
int64_t _syn_actualizador_ejecutar(CadenaSegura cmd) {
    if (cmd.datos == NULL || cmd.longitud <= 0) return -1;
    char* cstr = (char*)malloc((size_t)(cmd.longitud + 1));
    if (cstr == NULL) return -1;
    memcpy(cstr, cmd.datos, (size_t)cmd.longitud);
    cstr[cmd.longitud] = '\0';
#ifdef _WIN32
    size_t n = strlen(cstr);
    char* envuelto = (char*)malloc(n + 16);
    if (envuelto == NULL) { free(cstr); return -1; }
    snprintf(envuelto, n + 16, "cmd /S /C \"%s\"", cstr);
    free(cstr);
    int r = system(envuelto);
    free(envuelto);
    return (int64_t)r;
#else
    int r = system(cstr);
    free(cstr);
    return (int64_t)r;
#endif
}

static int _hex_valor(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static int _decodificar_hex(const char* hex, unsigned char* out, int esperado) {
    int n = 0;
    while (*hex != '\0') {
        if (isspace((unsigned char)*hex)) { hex++; continue; }
        int hi = _hex_valor(hex[0]);
        int lo = (hex[0] != '\0') ? _hex_valor(hex[1]) : -1;
        if (hi < 0 || lo < 0 || n >= esperado) return -1;
        out[n++] = (unsigned char)((hi << 4) | lo);
        hex += 2;
    }
    return (n == esperado) ? 0 : -1;
}

static char* _leer_texto(const char* ruta) {
    FILE* f = fopen(ruta, "rb");
    if (f == NULL) return NULL;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
    long n = ftell(f);
    if (n < 0 || n > (16L * 1024L * 1024L)) { fclose(f); return NULL; }
    rewind(f);
    char* p = (char*)malloc((size_t)n + 1);
    if (p == NULL) { fclose(f); return NULL; }
    size_t leido = fread(p, 1, (size_t)n, f);
    fclose(f);
    p[leido] = '\0';
    return p;
}

int64_t _syn_actualizador_verificar_firma(CadenaSegura artefacto,
                                          CadenaSegura firma_hex,
                                          CadenaSegura clave_hex) {
    if (artefacto.longitud <= 0 || artefacto.datos == NULL) return -1;

    (void)firma_hex;

    // El .sig es el archivo hermano <artefacto>.sig (128 hex ASCII).
    size_t ruta_n = strlen(artefacto.datos) + 5;
    char* ruta_sig = (char*)malloc(ruta_n);
    if (ruta_sig == NULL) return -1;
    snprintf(ruta_sig, ruta_n, "%s.sig", artefacto.datos);
    char* sig_txt = _leer_texto(ruta_sig);
    free(ruta_sig);
    if (sig_txt == NULL) return -1;

    unsigned char firma[64];
    unsigned char pub[32];
    if (_decodificar_hex(sig_txt, firma, 64) != 0) { free(sig_txt); return -1; }
    free(sig_txt);

    const char* clave = (clave_hex.longitud > 0 && clave_hex.datos != NULL)
                            ? clave_hex.datos
                            : _SYNAPSE_UPDATE_PUBHEX;
    if (_decodificar_hex(clave, pub, 32) != 0) return -1;

    FILE* f = fopen(artefacto.datos, "rb");
    if (f == NULL) return -1;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return -1; }
    long n = ftell(f);
    if (n < 0 || n > (1024L * 1024L * 1024L)) { fclose(f); return -1; }
    rewind(f);
    unsigned char* datos = (unsigned char*)malloc((size_t)n);
    if (datos == NULL) { fclose(f); return -1; }
    size_t leido = fread(datos, 1, (size_t)n, f);
    fclose(f);
    if (leido != (size_t)n) { free(datos); return -1; }

    CadenaSegura msg;
    msg.longitud = (int)n;
    msg.datos = (const char*)datos;
    CadenaSegura fs;
    fs.longitud = 64;
    fs.datos = (const char*)firma;
    CadenaSegura pk;
    pk.longitud = 32;
    pk.datos = (const char*)pub;
    int rc = _syn_ed25519_verificar(msg, fs, pk);
    free(datos);
    return rc;
}

static int _crear_dir_recursivo(const char* ruta) {
    if (ruta == NULL || ruta[0] == '\0') return -1;
    char tmp[4096];
    size_t n = strlen(ruta);
    if (n >= sizeof(tmp)) return -1;
    memcpy(tmp, ruta, n + 1);
    for (size_t i = 1; i < n; i++) {
        if (tmp[i] == '/' || tmp[i] == '\\') {
            char saved = tmp[i];
            tmp[i] = '\0';
            MKDIR(tmp);
            tmp[i] = saved;
        }
    }
    if (MKDIR(tmp) != 0) {
        struct stat st;
        if (stat(tmp, &st) != 0 || !(st.st_mode & S_IFDIR)) return -1;
    }
    return 0;
}

static int _copiar_archivo(const char* origen, const char* destino) {
    FILE* in = fopen(origen, "rb");
    if (in == NULL) return -1;
    FILE* out = fopen(destino, "wb");
    if (out == NULL) { fclose(in); return -1; }
    char buf[65536];
    size_t n;
    int ok = 0;
    while ((n = fread(buf, 1, sizeof(buf), in)) > 0) {
        if (fwrite(buf, 1, n, out) != n) { ok = -1; break; }
    }
    if (ferror(in)) ok = -1;
    fclose(in);
    if (fclose(out) != 0) ok = -1;
    return ok;
}

CadenaSegura _syn_actualizador_backup(CadenaSegura destino_dir) {
    if (destino_dir.longitud <= 0 || destino_dir.datos == NULL) {
        return _texto_desde_c("");
    }
    CadenaSegura exe = _syn_actualizador_exe();
    if (exe.longitud <= 0) return _texto_desde_c("");
    if (_crear_dir_recursivo(destino_dir.datos) != 0) return _texto_desde_c("");

    const char* base = strrchr(exe.datos, RUTA_SEP);
#ifdef _WIN32
    const char* base2 = strrchr(exe.datos, '/');
    if (base2 != NULL && (base == NULL || base2 > base)) base = base2;
#endif
    base = (base == NULL) ? exe.datos : base + 1;

    size_t ruta_n = strlen(destino_dir.datos) + strlen(base) + 6;
    char* ruta = (char*)malloc(ruta_n);
    if (ruta == NULL) return _texto_desde_c("");
    snprintf(ruta, ruta_n, "%s%c%s.bak", destino_dir.datos, RUTA_SEP, base);

    int rc = _copiar_archivo(exe.datos, ruta);
    if (rc != 0) { free(ruta); return _texto_desde_c(""); }
    CadenaSegura r = _texto_desde_c(ruta);
    free(ruta);
    return r;
}

#ifdef _WIN32
static void _escapar_ps(const char* s, char* out, size_t out_n) {
    size_t j = 0;
    for (size_t i = 0; s[i] != '\0' && j + 2 < out_n; i++) {
        if (s[i] == '\'') out[j++] = '\'';
        out[j++] = s[i];
    }
    out[j] = '\0';
}

static int _instalar_windows(const char* nuevo, const char* destino,
                             int es_instalador) {
    if (es_instalador) {
        size_t n = strlen(nuevo) + 96;
        char* cmd = (char*)malloc(n);
        if (cmd == NULL) return -1;
        snprintf(cmd, n,
                 "\"%s\" /SILENT /SUPPRESSMSGBOXES /NORESTART", nuevo);
        CadenaSegura cmd_s = _texto_desde_c(cmd);
        free(cmd);
        int64_t rc = _syn_actualizador_ejecutar(cmd_s);
        return (rc == 0) ? 0 : -1;
    }

    char tmp[MAX_PATH];
    DWORD tn = GetTempPathA((DWORD)sizeof(tmp), tmp);
    if (tn == 0 || tn >= sizeof(tmp)) return -1;
    char ps1[MAX_PATH];
    snprintf(ps1, sizeof(ps1), "%ssynapse_update_%d.ps1", tmp,
             (int)GetCurrentProcessId());

    char src[2048];
    char dst[2048];
    _escapar_ps(nuevo, src, sizeof(src));
    _escapar_ps(destino, dst, sizeof(dst));

    FILE* f = fopen(ps1, "wb");
    if (f == NULL) return -1;
    fprintf(f,
            "Start-Sleep -Milliseconds 500\r\n"
            "$src = '%s'\r\n"
            "$dst = '%s'\r\n"
            "for ($i = 0; $i -lt 90; $i++) {\r\n"
            "  try {\r\n"
            "    Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop\r\n"
            "    Start-Process -FilePath $dst -ArgumentList '--version' -WindowStyle Hidden\r\n"
            "    Remove-Item -LiteralPath $src -Force -ErrorAction SilentlyContinue\r\n"
            "    exit 0\r\n"
            "  } catch { Start-Sleep -Seconds 1 }\r\n"
            "}\r\n"
            "exit 1\r\n",
            src, dst);
    fclose(f);

    size_t n = strlen(ps1) + 160;
    char* cmd = (char*)malloc(n);
    if (cmd == NULL) { remove(ps1); return -1; }
    snprintf(cmd, n,
             "start \"\" /B powershell -NoProfile -WindowStyle Hidden "
             "-ExecutionPolicy Bypass -File \"%s\"",
             ps1);
    int rc = system(cmd);
    free(cmd);
    return (rc == 0) ? 0 : -1;
}
#endif

int64_t _syn_actualizador_instalar(CadenaSegura nuevo, CadenaSegura destino) {
    if (nuevo.longitud <= 0 || nuevo.datos == NULL) return -1;

    CadenaSegura exe = _syn_actualizador_exe();
    const char* dst = (destino.longitud > 0 && destino.datos != NULL)
                          ? destino.datos
                          : exe.datos;
    if (dst == NULL || dst[0] == '\0') return -1;

    char nombre[1024];
    const char* base = strrchr(nuevo.datos, RUTA_SEP);
#ifdef _WIN32
    const char* base2 = strrchr(nuevo.datos, '/');
    if (base2 != NULL && (base == NULL || base2 > base)) base = base2;
#endif
    base = (base == NULL) ? nuevo.datos : base + 1;
    size_t nb = strlen(base);
    if (nb >= sizeof(nombre)) return -1;
    for (size_t i = 0; i <= nb; i++) {
        nombre[i] = (char)tolower((unsigned char)base[i]);
    }
    int es_instalador = (strstr(nombre, "setup") != NULL ||
                         strstr(nombre, "installer") != NULL);

#ifdef _WIN32
    return _instalar_windows(nuevo.datos, dst, es_instalador);
#else
    if (es_instalador) {
        size_t n = strlen(nuevo.datos) + 8;
        char* cmd = (char*)malloc(n);
        if (cmd == NULL) return -1;
        snprintf(cmd, n, "sh \"%s\"", nuevo.datos);
        int rc = system(cmd);
        free(cmd);
        return (rc == 0) ? 0 : -1;
    }
    if (rename(nuevo.datos, dst) == 0) {
        chmod(dst, 0755);
        return 0;
    }
    if (_copiar_archivo(nuevo.datos, dst) == 0) {
        chmod(dst, 0755);
        return 0;
    }
    return -1;
#endif
}

static int64_t _actualizador_parte_version(const char* s, int len, int indice) {
    if (s == NULL || len <= 0 || indice < 0) return 0;
    int pos = 0;
    if (s[pos] == 'v' || s[pos] == 'V') pos++;
    int actual = 0;
    int64_t parte = 0;
    int visto = 0;
    for (; pos < len; pos++) {
        char c = s[pos];
        if (c == '.') {
            if (actual == indice) return parte;
            actual++;
            parte = 0;
            visto = 0;
        } else if (c >= '0' && c <= '9') {
            if (actual == indice) {
                parte = parte * 10 + (int64_t)(c - '0');
                visto = 1;
            }
        } else {
            if (visto) return actual == indice ? parte : 0;
            break;
        }
    }
    return actual == indice ? parte : 0;
}

int64_t _syn_actualizador_version_mayor(CadenaSegura v) {
    return _actualizador_parte_version(v.datos, v.longitud, 0);
}

int64_t _syn_actualizador_comparar_versiones(CadenaSegura a, CadenaSegura b) {
    for (int i = 0; i < 3; i++) {
        int64_t pa = _actualizador_parte_version(a.datos, a.longitud, i);
        int64_t pb = _actualizador_parte_version(b.datos, b.longitud, i);
        if (pa > pb) return 1;
        if (pa < pb) return -1;
    }
    return 0;
}
