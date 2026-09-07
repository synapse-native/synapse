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
#ifdef _WIN32
  #include <windows.h>   // GetTickCount64 para el plazo de lectura
#else
  #include <time.h>      // clock_gettime(CLOCK_MONOTONIC)
  #include <errno.h>     // EAGAIN/EWOULDBLOCK
#endif

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

// ============================================================
// Lectura robusta de la respuesta HTTP (Manual 7 §8, calidad industrial)
// ============================================================

// Reloj monotónico en milisegundos (para plazo absoluto de lectura).
static long long _ollama_ahora_ms(void) {
#ifdef _WIN32
    return (long long)GetTickCount64();
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000LL + ts.tv_nsec / 1000000LL;
#endif
}

// Timeout de bloqueo por recv (2 s): permite detectar servidor colgado sin
// esperar el cierre TCP. Windows usa DWORD ms; POSIX struct timeval.
static void _ollama_conf_timeout(int fd) {
#ifdef _WIN32
    DWORD ms = 2000;
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, (const char*)&ms, sizeof(ms));
#else
    struct timeval tv;
    tv.tv_sec = 2;
    tv.tv_usec = 0;
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
#endif
}

// ¿El último recv falló por timeout (servidor vivo pero sin datos)?
static int _ollama_es_timeout(void) {
#ifdef _WIN32
    int e = WSAGetLastError();
    return (e == WSAETIMEDOUT);
#else
    return (errno == EAGAIN || errno == EWOULDBLOCK);
#endif
}

// Busca "\r\n\r\n" (fin de cabeceras HTTP) en buf[0..len).
// Devuelve el índice del primer byte del cuerpo, o -1 si aún no llegó.
static int _ollama_fin_cabeceras(const char* buf, int len) {
    for (int i = 0; i + 3 < len; i++) {
        if (buf[i] == '\r' && buf[i + 1] == '\n' &&
            buf[i + 2] == '\r' && buf[i + 3] == '\n')
            return i + 4;
    }
    return -1;
}

// Lee el entero de una cabecera HTTP (p.ej. "Content-Length: 123" o
// "content-length: 123"). Devuelve -1 si la cabecera no está presente.
static long long _ollama_cabecera_int(const char* buf, int len, const char* nombre) {
    int nl = (int)strlen(nombre);
    for (int i = 0; i + nl < len; i++) {
        int igual = 1;
        for (int j = 0; j < nl; j++) {
            char a = buf[i + j];
            char b = nombre[j];
            if (a >= 'A' && a <= 'Z') a = (char)(a - 'A' + 'a');
            if (b >= 'A' && b <= 'Z') b = (char)(b - 'A' + 'a');
            if (a != b) { igual = 0; break; }
        }
        if (!igual) continue;
        int k = i + nl;
        while (k < len && buf[k] == ' ') k++;
        if (k >= len || buf[k] != ':') continue;
        k++;
        while (k < len && (buf[k] == ' ' || buf[k] == '\t')) k++;
        long long v = 0;
        int digitos = 0;
        while (k < len && buf[k] >= '0' && buf[k] <= '9') {
            v = v * 10 + (buf[k] - '0');
            k++;
            digitos++;
        }
        if (digitos > 0) return v;
        return -1;
    }
    return -1;
}

// Lee toda la respuesta HTTP en un buffer malloc con PLAZO ABSOLUTO: nunca
// bloquea más de _OLLAMA_PLAZO_MS incluso si Ollama se cuelga a mitad de
// respuesta. Corta en cuanto recibió el cuerpo completo (Content-Length) o el
// servidor cerró la conexión (Connection: close, como pedimos en la request).
// *out_len: >0 longitud leída; -1 error de conexión; -2 plazo agotado
// (servidor sin respuesta); -3 conexión cerrada antes del cuerpo completo.
#define _OLLAMA_PLAZO_MS 300000LL   // 5 min: carga del modelo en frío + generación
static char* _ollama_leer_respuesta(int fd, int* out_len) {
    if (out_len) *out_len = -1;
    _ollama_conf_timeout(fd);
    long long inicio = _ollama_ahora_ms();
    int cap = 65536;
    int len = 0;
    char* buf = (char*)malloc((size_t)cap);
    if (!buf) return NULL;
    int fin_cab = -1;          // índice del cuerpo tras \r\n\r\n
    long long contenido = -1;  // Content-Length (si la envía Ollama)
    int estado = 1;            // 1 ok / -1 error / -2 plazo / -3 incompleta
    for (;;) {
        if (len + 16384 >= cap) {
            cap *= 2;
            char* nn = (char*)realloc(buf, (size_t)cap);
            if (!nn) { free(buf); return NULL; }
            buf = nn;
        }
        int n = _syn_recibir(fd, buf + len, cap - len - 1);
        if (n > 0) {
            len += n;
            if (len > 32 * 1024 * 1024) break;  // tope de seguridad
            if (fin_cab < 0) {
                fin_cab = _ollama_fin_cabeceras(buf, len);
                if (fin_cab >= 0)
                    contenido = _ollama_cabecera_int(buf, fin_cab, "content-length");
            }
            // Cuerpo completo ya recibido (cuando el servidor da Content-Length)
            if (fin_cab >= 0 && contenido >= 0 && len >= fin_cab + (int)contenido) {
                estado = 1;
                break;
            }
        } else if (n == 0) {
            // Cierre limpio del servidor (Connection: close): respuesta completa
            // si ya llegaron cabeceras; incompleta si cortó en medio del cuerpo.
            if (fin_cab >= 0 && contenido >= 0 && len < fin_cab + (int)contenido)
                estado = -3;
            else if (fin_cab < 0 && len == 0)
                estado = -1;
            break;
        } else {
            if (_ollama_es_timeout()) {
                if (_ollama_ahora_ms() - inicio >= _OLLAMA_PLAZO_MS) {
                    estado = -2;  // servidor colgado: no envió nada en el plazo
                    break;
                }
                continue;  // sigue esperando (carga del modelo puede tardar)
            }
            estado = -1;  // error de socket real
            break;
        }
    }
    buf[len] = '\0';
    if (out_len) *out_len = (estado > 0) ? len : estado;
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
        } else {
            // Sin respuesta: distinguir plazo agotado de error para que el chat
            // muestre un mensaje claro y NO se quede colgado en silencio.
            const char* msg = NULL;
            if (rlen == -2)
                msg = "Ollama no respondio a tiempo (puede estar cargando el modelo o colgado). Verifica: ollama serve";
            else if (rlen == -3)
                msg = "Ollama corto la conexion a mitad de respuesta. Reintenta la consulta.";
            else
                msg = "No se pudo leer la respuesta de Ollama. Verifica que este activo: ollama serve";
            int largo = (int)strlen(msg);
            char* pool = (char*)pool_alloc((size_t)largo + 1);
            if (pool) {
                memcpy(pool, msg, (size_t)largo);
                pool[largo] = '\0';
                resultado = (CadenaSegura){ .longitud = largo, .datos = pool };
            }
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

// ============================================================
// Chat STREAMING (Manual 7 §8) — POST /api/chat con "stream":true
// ============================================================
// Sesión incremental: .syn llama _syn_ollama_stream_iniciar, luego repite
// _syn_ollama_stream_leer (cada llamada devuelve el siguiente fragmento de
// contenido, o "" al terminar) y cierra con _syn_ollama_stream_cerrar.
// El cuerpo llega con Transfer-Encoding: chunked (Ollama) → se decodifican
// los marcos y se parsea NDJSON línea a línea, con timeout de inactividad y
// plazo absoluto (herencia de R140: jamás colgar en silencio).

#define OLL_STREAM_IDLE_MS 120000LL    // 2 min sin datos = servidor colgado
#define OLL_STREAM_TOTAL_MS 600000LL   // 10 min absolutos por sesión

typedef struct _OllSesion {
    int fd;
    // buffer crudo de red
    char* rb;
    int rbcap, rblen, rbpos;
    int cab_ok;          // cabeceras ya saltadas
    int chunked;         // Transfer-Encoding: chunked detectado
    // estado del decodificador de chunks
    int fase;            // 0 = línea de tamaño, 1 = payload, 3 = CRLF tras payload
    long restante;       // bytes de payload pendientes en el chunk actual
    // payload decodificado (acumulador NDJSON)
    char* acc;
    int acccap, acclen, accbase;
    long long inicio, ultima;
    int hecho;
    int error;
    char* msg_error;     // malloc, mensaje de error si lo hubo
} _OllSesion;

// Lee bytes crudos a rb. 1 = hay datos, 0 = cierre de conexión, -1 = error.
static int _oll_raw_leer(_OllSesion* s) {
    for (;;) {
        if (s->rblen + 16384 >= s->rbcap) {
            int nuevo = s->rbcap * 2;
            char* nn = (char*)realloc(s->rb, (size_t)nuevo);
            if (!nn) return -1;
            s->rb = nn;
            s->rbcap = nuevo;
        }
        int n = _syn_recibir(s->fd, s->rb + s->rblen, s->rbcap - s->rblen - 1);
        if (n > 0) {
            s->rblen += n;
            s->ultima = _ollama_ahora_ms();
            return 1;
        }
        if (n == 0) return 0;
        if (_ollama_es_timeout()) {
            long long ahora = _ollama_ahora_ms();
            if (ahora - s->ultima > OLL_STREAM_IDLE_MS) return -2;   // inactivo
            if (ahora - s->inicio > OLL_STREAM_TOTAL_MS) return -2;   // plazo
            continue;
        }
        return -1;
    }
}

// Salta cabeceras HTTP la primera vez y detecta chunked. 0 ok, -1 error.
static int _oll_cabeceras(_OllSesion* s) {
    if (s->cab_ok) return 0;
    for (;;) {
        // buscar \r\n\r\n en rb
        int fin = -1;
        for (int i = 0; i + 3 < s->rblen; i++) {
            if (s->rb[i] == '\r' && s->rb[i + 1] == '\n' &&
                s->rb[i + 2] == '\r' && s->rb[i + 3] == '\n') { fin = i + 4; break; }
        }
        if (fin >= 0) {
            s->chunked = (_ollama_cabecera_int(s->rb, fin, "content-length") < 0);
            // chunked si no hay content-length en una respuesta viva
            s->rbpos = fin;
            s->cab_ok = 1;
            return 0;
        }
        int r = _oll_raw_leer(s);
        if (r <= 0) return -1;
    }
}

// Compacta el acumulador acc (descarta lo ya consumido).
static void _oll_acc_compact(_OllSesion* s) {
    if (s->accbase > 0) {
        int rest = s->acclen - s->accbase;
        if (rest > 0) memmove(s->acc, s->acc + s->accbase, (size_t)rest);
        s->acclen = rest;
        s->accbase = 0;
        if (s->acc) s->acc[s->acclen] = '\0';
    }
}

// Decodifica chunked desde rb hacia acc (todo lo que pueda con los bytes
// disponibles). Si el servidor no usa chunked, vuelca rb directo a acc.
static void _oll_dechunk(_OllSesion* s) {
    if (!s->chunked) {
        int disp = s->rblen - s->rbpos;
        if (disp > 0) {
            if (s->acclen + disp + 1 > s->acccap) {
                int nuevo = (s->acclen + disp + 1) * 2;
                char* nn = (char*)realloc(s->acc, (size_t)nuevo);
                if (!nn) return;
                s->acc = nn;
                s->acccap = nuevo;
            }
            memcpy(s->acc + s->acclen, s->rb + s->rbpos, (size_t)disp);
            s->acclen += disp;
            s->acc[s->acclen] = '\0';
            s->rbpos = s->rblen;
        }
        return;
    }
    for (;;) {
        if (s->fase == 0) {
            // buscar la línea de tamaño del chunk
            int nl = -1;
            for (int i = s->rbpos; i + 1 < s->rblen; i++) {
                if (s->rb[i] == '\n') { nl = i; break; }
            }
            if (nl < 0) return;   // falta la línea completa
            long tam = 0;
            int i = s->rbpos;
            while (i < nl) {
                char c = s->rb[i];
                if (c == ';') break;
                if (c >= '0' && c <= '9') tam = tam * 16 + (c - '0');
                else if (c >= 'a' && c <= 'f') tam = tam * 16 + (c - 'a' + 10);
                else if (c >= 'A' && c <= 'F') tam = tam * 16 + (c - 'A' + 10);
                else break;
                i++;
            }
            s->rbpos = nl + 1;
            if (tam == 0) {
                s->fase = 4;   // terminador de chunks: esperar CRLF final
                continue;
            }
            s->restante = tam;
            s->fase = 1;
        } else if (s->fase == 1) {
            int disp = s->rblen - s->rbpos;
            if (disp <= 0) return;
            int tomar = (int)(disp < s->restante ? disp : s->restante);
            if (s->acclen + tomar + 1 > s->acccap) {
                int nuevo = (s->acclen + tomar + 1) * 2;
                char* nn = (char*)realloc(s->acc, (size_t)nuevo);
                if (!nn) return;
                s->acc = nn;
                s->acccap = nuevo;
            }
            memcpy(s->acc + s->acclen, s->rb + s->rbpos, (size_t)tomar);
            s->acclen += tomar;
            s->acc[s->acclen] = '\0';
            s->rbpos += tomar;
            s->restante -= tomar;
            if (s->restante == 0) s->fase = 3;   // esperar CRLF del chunk
        } else if (s->fase == 3) {
            if (s->rblen - s->rbpos < 2) return;
            s->rbpos += 2;
            s->fase = 0;
        } else {   // fase 4: tras el chunk 0 esperamos CRLF y trailers
            if (s->rblen - s->rbpos < 2) return;
            // consumir \r\n (y trailers hasta la línea vacía)
            s->rbpos += 2;
            for (;;) {
                int nl = -1;
                for (int i = s->rbpos; i + 1 < s->rblen; i++) {
                    if (s->rb[i] == '\n') { nl = i; break; }
                }
                if (nl < 0) break;
                int largo = nl - s->rbpos;
                s->rbpos = nl + 1;
                if (largo <= 2) { s->fase = 5; break; }   // línea vacía = fin de trailers
            }
            if (s->fase != 5) return;
            // todo el cuerpo llegó
        }
    }
}

// Extrae el contenido JSON de una línea NDJSON. Devuelve 1 con fragmento en
// *out (malloc, desescapado); 2 si la línea marcó done; 3 si marcó error;
// 0 si la línea no trae nada relevante (thinking, usage, etc.).
static int _oll_linea_json(const char* linea, int largo, char** out, int* out_len,
                           char** msg_err) {
    *out = NULL;
    *out_len = 0;
    // ¿error?
    if (strstr(linea, "\"error\"")) {
        const char* p = strstr(linea, "\"error\"");
        const char* q = strstr(p, ":");
        if (q) {
            q++;
            while (*q == ' ' || *q == '\t') q++;
            if (*q == '"') {
                const char* ini = q + 1;
                const char* fin = ini;
                while (*fin && *fin != '"') {
                    if (*fin == '\\') fin++;
                    if (*fin) fin++;
                }
                int el = (int)(fin - ini);
                int dl = 0;
                char* d = _ollama_desescapar(ini, el, &dl);
                if (d) {
                    *msg_err = d;
                    return 3;
                }
            }
        }
        return 3;
    }
    // ¿done?
    if (strstr(linea, "\"done\":true")) return 2;
    // ¿content?
    const char* p = strstr(linea, "\"content\":\"");
    if (!p) return 0;
    const char* ini = p + 11;
    const char* fin = ini;
    while (*fin && *fin != '"') {
        if (*fin == '\\') fin++;
        if (*fin) fin++;
    }
    int largo2 = (int)(fin - ini);
    if (largo2 <= 0) return 0;
    int dl = 0;
    char* d = _ollama_desescapar(ini, largo2, &dl);
    if (!d) return 0;
    *out = d;
    *out_len = dl;
    return 1;
}

void* _syn_ollama_stream_iniciar(CadenaSegura modelo, CadenaSegura prompt,
                                 CadenaSegura host, int64_t puerto,
                                 int64_t max_tokens) {
    if (modelo.datos == NULL || modelo.longitud <= 0 || prompt.datos == NULL) return NULL;
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
    if (!ms || !ps) { if (ms) free(ms); if (ps) free(ps); return NULL; }
    memcpy(ms, modelo.datos, (size_t)modelo.longitud);
    ms[modelo.longitud] = '\0';
    memcpy(ps, prompt.datos, (size_t)prompt.longitud);
    ps[prompt.longitud] = '\0';
    int mjlen = 0, pjlen = 0;
    char* mjs = _ollama_esc_json(ms, (int)modelo.longitud, &mjlen);
    char* pjs = _ollama_esc_json(ps, (int)prompt.longitud, &pjlen);
    free(ms);
    free(ps);
    if (!mjs || !pjs) { if (mjs) free(mjs); if (pjs) free(pjs); return NULL; }
    int cap_body = mjlen + pjlen + 160;
    char* body = (char*)malloc((size_t)cap_body);
    if (!body) { free(mjs); free(pjs); return NULL; }
    int bl = snprintf(body, (size_t)cap_body,
        "{\"model\":\"%s\",\"messages\":[{\"role\":\"user\",\"content\":\"%s\"}],"
        "\"stream\":true,\"options\":{\"num_predict\":%d}}",
        mjs, pjs, mt);
    free(mjs);
    free(pjs);
    if (bl <= 0 || bl >= cap_body) { free(body); return NULL; }

    char cab[256];
    int hl = snprintf(cab, sizeof(cab),
        "POST /api/chat HTTP/1.1\r\n"
        "Host: %s:%d\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n\r\n",
        hip, pt, bl);

    _syn_iniciar_red();
    int fd = _syn_socket();
    if (fd < 0) { free(body); return NULL; }
    if (_syn_conectar(fd, hip, pt) != 0) {
        _syn_cerrar_socket(fd);
        free(body);
        return NULL;
    }
    _syn_enviar(fd, cab, hl);
    _syn_enviar(fd, body, bl);
    free(body);
    _ollama_conf_timeout(fd);

    _OllSesion* s = (_OllSesion*)malloc(sizeof(_OllSesion));
    if (!s) { _syn_cerrar_socket(fd); return NULL; }
    memset(s, 0, sizeof(*s));
    s->fd = fd;
    s->rbcap = 65536;
    s->rb = (char*)malloc((size_t)s->rbcap);
    s->acccap = 65536;
    s->acc = (char*)malloc((size_t)s->acccap);
    if (!s->rb || !s->acc) {
        if (s->rb) free(s->rb);
        if (s->acc) free(s->acc);
        free(s);
        _syn_cerrar_socket(fd);
        return NULL;
    }
    s->inicio = s->ultima = _ollama_ahora_ms();
    return s;
}

static void _oll_set_error(_OllSesion* s, const char* msg) {
    s->error = 1;
    s->hecho = 1;
    if (!s->msg_error) {
        int largo = (int)strlen(msg);
        char* m = (char*)malloc((size_t)largo + 1);
        if (m) { memcpy(m, msg, (size_t)largo + 1); s->msg_error = m; }
    }
}

// Devuelve el siguiente fragmento de contenido (pool_alloc), o "" cuando la
// sesión terminó (done) o falló (consultar _syn_ollama_stream_estado/error).
CadenaSegura _syn_ollama_stream_leer(void* h) {
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    if (!h) return vacio;
    _OllSesion* s = (_OllSesion*)h;
    // primera llamada: saltar cabeceras y detectar chunked
    if (!s->cab_ok) {
        if (_oll_cabeceras(s) != 0) {
            _oll_set_error(s, "Ollama no respondio (sin cabeceras HTTP). Verifica: ollama serve");
            return vacio;
        }
    }
    for (;;) {
        if (s->hecho) {
            _oll_acc_compact(s);
            return vacio;
        }
        // procesar líneas completas ya disponibles en acc
        _oll_acc_compact(s);
        for (;;) {
            int nl = -1;
            for (int i = s->accbase; i < s->acclen; i++) {
                if (s->acc[i] == '\n') { nl = i; break; }
            }
            if (nl < 0) break;
            int ini = s->accbase;
            int largo = nl - ini;
            if (largo > 0 && s->acc[nl - 1] == '\r') largo--;
            s->accbase = nl + 1;
            if (largo <= 0) continue;
            char* chunk = NULL;
            int clen = 0;
            char* merr = NULL;
            int r = _oll_linea_json(s->acc + ini, largo, &chunk, &clen, &merr);
            if (r == 1 && chunk && clen > 0) {
                char* pool = (char*)pool_alloc((size_t)clen + 1);
                if (!pool) { free(chunk); return vacio; }
                memcpy(pool, chunk, (size_t)clen);
                pool[clen] = '\0';
                free(chunk);
                return (CadenaSegura){ .longitud = clen, .datos = pool };
            }
            if (r == 2) {
                if (chunk) free(chunk);
                s->hecho = 1;
                return vacio;
            }
            if (r == 3) {
                s->error = 1;
                s->hecho = 1;
                if (merr) {
                    if (s->msg_error) free(s->msg_error);
                    s->msg_error = merr;
                }
                return vacio;
            }
            if (chunk) free(chunk);
            // línea sin contenido: seguir con la siguiente
        }
        // decodificar más payload desde la red
        _oll_dechunk(s);
        // si aún no hay línea completa ni datos nuevos: leer red
        int hay_linea = 0;
        for (int i = s->accbase; i < s->acclen; i++) {
            if (s->acc[i] == '\n') { hay_linea = 1; break; }
        }
        if (hay_linea) continue;
        if (s->fase == 5) { s->hecho = 1; return vacio; }
        if (s->rbpos >= s->rblen) {
            int r = _oll_raw_leer(s);
            if (r == 0) {
                // conexión cerrada por el servidor
                if (s->fase == 5 || s->fase == 4) { s->hecho = 1; return vacio; }
                if (s->acclen - s->accbase > 0)
                    _oll_set_error(s, "Ollama cerro la conexion antes de terminar la respuesta.");
                else
                    _oll_set_error(s, "Ollama no envio respuesta.");
                return vacio;
            }
            if (r == -2) {
                _oll_set_error(s, "Ollama dejo de responder (timeout de streaming). Verifica: ollama serve");
                return vacio;
            }
            if (r < 0) {
                _oll_set_error(s, "Error de red con Ollama durante el streaming.");
                return vacio;
            }
        }
    }
}

int64_t _syn_ollama_stream_estado(void* h) {
    if (!h) return 1;
    _OllSesion* s = (_OllSesion*)h;
    if (s->error) return 1;
    if (s->hecho) return 0;
    return 0;
}

CadenaSegura _syn_ollama_stream_error(void* h) {
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    if (!h) return vacio;
    _OllSesion* s = (_OllSesion*)h;
    if (!s->msg_error || !*s->msg_error) return vacio;
    int largo = (int)strlen(s->msg_error);
    char* pool = (char*)pool_alloc((size_t)largo + 1);
    if (!pool) return vacio;
    memcpy(pool, s->msg_error, (size_t)largo + 1);
    return (CadenaSegura){ .longitud = largo, .datos = pool };
}

void _syn_ollama_stream_cerrar(void* h) {
    if (!h) return;
    _OllSesion* s = (_OllSesion*)h;
    _syn_cerrar_socket(s->fd);
    if (s->rb) free(s->rb);
    if (s->acc) free(s->acc);
    if (s->msg_error) free(s->msg_error);
    free(s);
}
