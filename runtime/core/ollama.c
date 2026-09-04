// runtime/core/ollama.c — Cliente HTTP mínimo para Ollama (chat local)
// OpenSyn Modo Oraculo (Manual 7 §8): POST /api/chat (stream:false) a
// http://host:puerto (default 127.0.0.1:11434). Sin telemetría: todo local.
// Retorna CadenaSegura pool_alloc (cumple Manual 2 §9.1: RAII libera con
// pool_free); vacía en error de red o si Ollama no responde contenido.
// Consumido por opensyn/principal.syn vía externo _syn_ollama_consultar.

#include "synapse_rt_types.h"
#include "runtime/core/network.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ============================================================
// Utilidades internas (malloc; liberadas dentro de esta unidad)
// ============================================================

// Escapa una cadena para insertarla como valor JSON (prompt/modelo).
static char* _ollama_esc_json(const char* s, int len, int* out_len) {
    int cap = len * 2 + 32;
    char* out = (char*)malloc((size_t)cap);
    if (!out) return NULL;
    int o = 0;
    for (int i = 0; i < len; i++) {
        unsigned char c = (unsigned char)s[i];
        if (o + 8 >= cap) {
            cap *= 2;
            char* nn = (char*)realloc(out, (size_t)cap);
            if (!nn) { free(out); return NULL; }
            out = nn;
        }
        switch (c) {
            case '"':  out[o++] = '\\'; out[o++] = '"'; break;
            case '\\': out[o++] = '\\'; out[o++] = '\\'; break;
            case '\n': out[o++] = '\\'; out[o++] = 'n'; break;
            case '\r': out[o++] = '\\'; out[o++] = 'r'; break;
            case '\t': out[o++] = '\\'; out[o++] = 't'; break;
            default:
                if (c < 0x20) {
                    o += sprintf(out + o, "\\u%04x", (unsigned)c);
                } else {
                    out[o++] = (char)c;
                }
        }
    }
    out[o] = '\0';
    if (out_len) *out_len = o;
    return out;
}

// Desescapa el contenido de un string JSON (\\n, \\", \\uXXXX, etc.).
static char* _ollama_desescapar(const char* s, int len, int* out_len) {
    char* out = (char*)malloc((size_t)(len + 1));
    if (!out) return NULL;
    int o = 0;
    for (int i = 0; i < len; i++) {
        if (s[i] == '\\' && i + 1 < len) {
            i++;
            switch (s[i]) {
                case 'n':  out[o++] = '\n'; break;
                case 'r':  out[o++] = '\r'; break;
                case 't':  out[o++] = '\t'; break;
                case '"':  out[o++] = '"'; break;
                case '\\': out[o++] = '\\'; break;
                case '/':  out[o++] = '/'; break;
                case 'u': {
                    if (i + 4 < len) {
                        unsigned cp = 0;
                        int ok = 1;
                        for (int k = 1; k <= 4; k++) {
                            char h = s[i + k];
                            cp <<= 4;
                            if (h >= '0' && h <= '9') cp |= (unsigned)(h - '0');
                            else if (h >= 'a' && h <= 'f') cp |= (unsigned)(h - 'a' + 10);
                            else if (h >= 'A' && h <= 'F') cp |= (unsigned)(h - 'A' + 10);
                            else { ok = 0; break; }
                        }
                        if (ok) {
                            i += 4;
                            if (cp < 0x80) {
                                out[o++] = (char)cp;
                            } else if (cp < 0x800) {
                                out[o++] = (char)(0xC0 | (cp >> 6));
                                out[o++] = (char)(0x80 | (cp & 0x3F));
                            } else {
                                out[o++] = (char)(0xE0 | (cp >> 12));
                                out[o++] = (char)(0x80 | ((cp >> 6) & 0x3F));
                                out[o++] = (char)(0x80 | (cp & 0x3F));
                            }
                            break;
                        }
                    }
                    out[o++] = '\\';
                    out[o++] = 'u';
                    break;
                }
                default:
                    out[o++] = '\\';
                    out[o++] = s[i];
                    break;
            }
        } else {
            out[o++] = s[i];
        }
    }
    out[o] = '\0';
    if (out_len) *out_len = o;
    return out;
}

// Lee toda la respuesta HTTP (hasta cierre de conexión) en un buffer malloc.
static char* _ollama_leer_respuesta(int fd, int* out_len) {
    int cap = 65536;
    int len = 0;
    char* buf = (char*)malloc((size_t)cap);
    if (!buf) return NULL;
    for (;;) {
        if (len + 16384 >= cap) {
            cap *= 2;
            char* nn = (char*)realloc(buf, (size_t)cap);
            if (!nn) { free(buf); return NULL; }
            buf = nn;
        }
        int n = _syn_recibir(fd, buf + len, cap - len - 1);
        if (n <= 0) break;
        len += n;
        if (len > 32 * 1024 * 1024) break;  // tope de seguridad
    }
    buf[len] = '\0';
    if (out_len) *out_len = len;
    return buf;
}

// Extrae el primer valor del campo JSON "clave" (string) del body HTTP (tras
// \r\n\r\n). Tolerante a "clave":"v" y "clave": "v" (con espacios).
// Devuelve CadenaSegura pool_alloc desescapada; vacio si el campo no existe.
static CadenaSegura _ollama_campo(const char* buf, const char* clave) {
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    char pat[96];
    snprintf(pat, sizeof(pat), "\"%s\"", clave);
    const char* cuerpo = strstr(buf, "\r\n\r\n");
    const char* base = cuerpo ? cuerpo + 4 : buf;
    const char* p = strstr(base, pat);
    if (!p) return vacio;
    const char* q = p + strlen(pat);
    while (*q && *q != ':') q++;       // hasta el separador ':'
    if (!*q) return vacio;
    q++;
    while (*q == ' ' || *q == '\t') q++;
    if (*q != '"') return vacio;      // el valor no es string
    const char* inicio = q + 1;
    const char* fin = inicio;
    while (*fin && *fin != '"') {
        if (*fin == '\\') fin++;       // saltar el escape
        if (*fin) fin++;
    }
    int largo = (int)(fin - inicio);
    if (largo <= 0) return vacio;
    int deslen = 0;
    char* des = _ollama_desescapar(inicio, largo, &deslen);
    if (!des) return vacio;
    char* pool = (char*)pool_alloc((size_t)(deslen + 1));
    if (!pool) { free(des); return vacio; }
    memcpy(pool, des, (size_t)deslen);
    pool[deslen] = '\0';
    free(des);
    return (CadenaSegura){ .longitud = deslen, .datos = pool };
}

// ============================================================
// API pública (externo de .syn: opensyn/principal.syn)
// ============================================================

// cumple Manual 7 8: consulta al oraculo local Ollama con el prompt del usuario.
// Si la respuesta trae "content" (mensaje del asistente) la devuelve; si trae
// "error" (p.ej. modelo no descargado) devuelve ese texto para mostrarlo.
CadenaSegura _syn_ollama_consultar(CadenaSegura modelo, CadenaSegura prompt,
                                   CadenaSegura host, int64_t puerto,
                                   int64_t max_tokens) {
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    if (modelo.datos == NULL || modelo.longitud <= 0 || prompt.datos == NULL) {
        return vacio;
    }

    char hostbuf[128];
    const char* hip = "127.0.0.1";
    if (host.datos && host.longitud > 0 && host.longitud < 127) {
        memcpy(hostbuf, host.datos, (size_t)host.longitud);
        hostbuf[host.longitud] = '\0';
        if (strcmp(hostbuf, "localhost") == 0) strcpy(hostbuf, "127.0.0.1");
        hip = hostbuf;
    }
    int pt = (int)((puerto <= 0 || puerto > 65535) ? 11434 : puerto);
    int mt = (int)((max_tokens <= 0) ? 1024 : max_tokens);

    char* ms = (char*)malloc((size_t)modelo.longitud + 1);
    char* ps = (char*)malloc((size_t)prompt.longitud + 1);
    if (!ms || !ps) { if (ms) free(ms); if (ps) free(ps); return vacio; }
    memcpy(ms, modelo.datos, (size_t)modelo.longitud);
    ms[modelo.longitud] = '\0';
    memcpy(ps, prompt.datos, (size_t)prompt.longitud);
    ps[prompt.longitud] = '\0';

    int mjlen = 0, pjlen = 0;
    char* mjs = _ollama_esc_json(ms, (int)modelo.longitud, &mjlen);
    char* pjs = _ollama_esc_json(ps, (int)prompt.longitud, &pjlen);
    free(ms);
    free(ps);
    if (!mjs || !pjs) { if (mjs) free(mjs); if (pjs) free(pjs); return vacio; }

    // Marco fijo del JSON (~97 B) + valores escapados + digitos del entero
    int cap_body = mjlen + pjlen + 160;
    char* body = (char*)malloc((size_t)cap_body);
    if (!body) { free(mjs); free(pjs); return vacio; }
    int bl = snprintf(body, (size_t)cap_body,
        "{\"model\":\"%s\",\"messages\":[{\"role\":\"user\",\"content\":\"%s\"}],"
        "\"stream\":false,\"options\":{\"num_predict\":%d}}",
        mjs, pjs, mt);
    free(mjs);
    free(pjs);
    if (bl <= 0 || bl >= cap_body) { free(body); return vacio; }

    char cab[256];
    int hl = snprintf(cab, sizeof(cab),
        "POST /api/chat HTTP/1.1\r\n"
        "Host: %s:%d\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n\r\n",
        hip, pt, bl);

    CadenaSegura resultado = vacio;
    _syn_iniciar_red();
    int fd = _syn_socket();
    if (fd < 0) { free(body); return vacio; }
    if (_syn_conectar(fd, hip, pt) == 0) {
        _syn_enviar(fd, cab, hl);
        _syn_enviar(fd, body, bl);
        int rlen = 0;
        char* resp = _ollama_leer_respuesta(fd, &rlen);
        if (resp) {
            // Mensaje del asistente, o texto de error de Ollama si lo hubo.
            // _ollama_campo devuelve literal "" (no allocado) cuando no existe.
            resultado = _ollama_campo(resp, "content");
            if (resultado.longitud == 0) {
                resultado = _ollama_campo(resp, "error");
            }
            free(resp);
        }
    }
    _syn_cerrar_socket(fd);
    free(body);
    return resultado;
}

// ============================================================
// GET /api/tags — modelos instalados (lista separada por '\n')
// ============================================================

// cumple Manual 7 8: lista los modelos instalados en Ollama vía GET /api/tags.
// Devuelve CadenaSegura pool_alloc con los nombres separados por '\n' (sin
// escapar: nombres de modelo no contienen comillas ni backslashes). Vacía si
// no hay conexión con el servidor o no hay modelos. Consumida por
// opensyn/principal.syn vía externo _syn_ollama_modelos (/model, /modelos).
static char* _ollama_extraer_nombres(const char* base, int* out_len) {
    // Primer paso: contar longitud total acumulada (nombres + separadores)
    long total = 0;
    int n = 0;
    const char* p = base;
    while ((p = strstr(p, "\"name\"")) != NULL) {
        const char* q = p + 6;
        while (*q && *q != ':') q++;
        if (!*q) break;
        q++;
        while (*q == ' ' || *q == '\t') q++;
        if (*q != '"') { p = q + 1; continue; }
        const char* ini = q + 1;
        const char* fin = ini;
        while (*fin && *fin != '"') {
            if (*fin == '\\') fin++;
            if (*fin) fin++;
        }
        long largo = fin - ini;
        if (largo > 0) {
            total += largo + 1;  // +1 separador '\n'
            n++;
        }
        p = fin + 1;
    }
    if (n == 0) return NULL;
    char* acc = (char*)malloc((size_t)total + 1);
    if (!acc) return NULL;
    // Segundo paso: copiar nombres separados por '\n'
    long used = 0;
    p = base;
    while ((p = strstr(p, "\"name\"")) != NULL) {
        const char* q = p + 6;
        while (*q && *q != ':') q++;
        if (!*q) break;
        q++;
        while (*q == ' ' || *q == '\t') q++;
        if (*q != '"') { p = q + 1; continue; }
        const char* ini = q + 1;
        const char* fin = ini;
        while (*fin && *fin != '"') {
            if (*fin == '\\') fin++;
            if (*fin) fin++;
        }
        long largo = fin - ini;
        if (largo > 0) {
            memcpy(acc + used, ini, (size_t)largo);
            used += largo;
            acc[used++] = '\n';
        }
        p = fin + 1;
    }
    acc[used] = '\0';
    if (out_len) *out_len = (int)used;
    return acc;
}

CadenaSegura _syn_ollama_modelos(CadenaSegura host, int64_t puerto) {
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    char hostbuf[128];
    const char* hip = "127.0.0.1";
    if (host.datos && host.longitud > 0 && host.longitud < 127) {
        memcpy(hostbuf, host.datos, (size_t)host.longitud);
        hostbuf[host.longitud] = '\0';
        if (strcmp(hostbuf, "localhost") == 0) strcpy(hostbuf, "127.0.0.1");
        hip = hostbuf;
    }
    int pt = (int)((puerto <= 0 || puerto > 65535) ? 11434 : puerto);

    char cab[256];
    int hl = snprintf(cab, sizeof(cab),
        "GET /api/tags HTTP/1.1\r\n"
        "Host: %s:%d\r\n"
        "Connection: close\r\n\r\n",
        hip, pt);

    _syn_iniciar_red();
    int fd = _syn_socket();
    if (fd < 0) return vacio;
    CadenaSegura resultado = vacio;
    if (_syn_conectar(fd, hip, pt) == 0) {
        _syn_enviar(fd, cab, hl);
        int rlen = 0;
        char* resp = _ollama_leer_respuesta(fd, &rlen);
        if (resp) {
            const char* cuerpo = strstr(resp, "\r\n\r\n");
            const char* base = cuerpo ? cuerpo + 4 : resp;
            int nlen = 0;
            char* nombres = _ollama_extraer_nombres(base, &nlen);
            if (nombres && nlen > 0) {
                char* pool = (char*)pool_alloc((size_t)nlen + 1);
                if (pool) {
                    memcpy(pool, nombres, (size_t)nlen);
                    pool[nlen] = '\0';
                    resultado = (CadenaSegura){ .longitud = nlen, .datos = pool };
                }
            }
            if (nombres) free(nombres);
            free(resp);
        }
    }
    _syn_cerrar_socket(fd);
    return resultado;
}
